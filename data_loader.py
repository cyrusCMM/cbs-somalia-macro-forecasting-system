# -*- coding: utf-8 -*-
"""
data_loader.py

Read and validate source data for the CBS Somalia macro model.

v7 update
---------
Adds stronger validation for annual data updates and SNBS revisions:

- latest actual year detection;
- duplicate code-year checks;
- required code checks;
- missing value checks;
- GDP expenditure identity check;
- statistical discrepancy threshold check;
- new/extra code listing;
- block-level year coverage checks.

Supported source formats
------------------------
1. Default CSV files in data/:
   Real_Data.csv, Fiscal_Data.csv, External_Data.csv, Monetary_Data.csv

2. Uploaded files through Streamlit:
   - one Excel workbook with sheets Real_Data, Fiscal_Data, External_Data, Monetary_Data; or
   - four CSV files with the same names.
"""

from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import numpy as np

from config import DATA_DIR, DATA_FILES, SD_WATCH_THRESHOLD

REQUIRED_COLUMNS = ["Block", "Variable", "Code", "Type", "Unit", "Source"]

REQUIRED_CODES = [
    "NGDP", "RGDP", "NPC", "NGC", "NINV", "NXGS", "NMGS", "CPI_AVG", "CPI_EOP",
    "IMP_DUTY", "DOM_SALES", "PIT", "CIT", "NONTAX", "GRANTS",
    "WAGES", "GDS_SERV_EXP", "TRANSFERS", "INT_PAY", "CAPEX", "OTHER_EXP",
    "X_GOODS", "M_GOODS", "X_SERV", "M_SERV",
    "PRI_INC_CR", "PRI_INC_DB", "SEC_INC_CR", "SEC_INC_DB", "CAB", "NER_AVG", "PM", "PX",
    "M2", "TOT_DEP", "PSC", "NFA", "NDA",
]

CORE_GDP_CODES = ["NGDP", "NPC", "NGC", "NINV", "NXGS", "NMGS"]
REAL_GDP_CODES = ["RGDP"]
SNBS_REVISION_CODES = ["NGDP", "RGDP", "NPC", "NGC", "NINV", "NXGS", "NMGS"]

EXCEL_SHEETS = {
    "Real": "Real_Data",
    "Fiscal": "Fiscal_Data",
    "External": "External_Data",
    "Monetary": "Monetary_Data",
}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
    return df


def _year_columns(df: pd.DataFrame) -> List[str]:
    out = []
    for col in df.columns:
        s = str(col).strip()
        if s.isdigit() and 1900 <= int(s) <= 2100:
            out.append(s)
    return out


def _to_long(df: pd.DataFrame, block_name: str, source_name: str = "") -> pd.DataFrame:
    df = _normalise_columns(df)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{source_name or block_name} is missing required columns: {missing}")

    years = _year_columns(df)
    if not years:
        raise ValueError(f"{source_name or block_name} has no year columns.")

    df = df[df["Code"].notna() & (df["Code"].astype(str).str.strip() != "")].copy()

    long = df.melt(
        id_vars=REQUIRED_COLUMNS,
        value_vars=years,
        var_name="Year",
        value_name="Value",
    )
    long["Year"] = long["Year"].astype(int)
    long["Value"] = pd.to_numeric(long["Value"], errors="coerce")
    long["Block"] = long["Block"].fillna(block_name).astype(str).str.strip()
    long["Code"] = long["Code"].astype(str).str.strip()
    return long


def read_block_csv(path: Path, block_name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {block_name} data file: {path}")
    df = pd.read_csv(path)
    return _to_long(df, block_name, path.name)


def read_uploaded_csv(uploaded_file: Any, block_name: str) -> pd.DataFrame:
    df = pd.read_csv(uploaded_file)
    return _to_long(df, block_name, getattr(uploaded_file, "name", block_name))


def read_uploaded_excel(uploaded_file: Any) -> pd.DataFrame:
    frames = []
    xl = pd.ExcelFile(uploaded_file)
    available = set(xl.sheet_names)

    missing_sheets = [sheet for sheet in EXCEL_SHEETS.values() if sheet not in available]
    if missing_sheets:
        raise ValueError(f"Uploaded workbook is missing required sheets: {missing_sheets}")

    for block, sheet in EXCEL_SHEETS.items():
        df = pd.read_excel(xl, sheet_name=sheet)
        frames.append(_to_long(df, block, sheet))

    return pd.concat(frames, ignore_index=True)


def _combine_default_blocks(data_dir: Path) -> pd.DataFrame:
    frames = []
    for block, filename in DATA_FILES.items():
        frames.append(read_block_csv(data_dir / filename, block))
    return pd.concat(frames, ignore_index=True)


def _combine_uploaded_blocks(uploaded_files: Dict[str, Any]) -> pd.DataFrame:
    """
    uploaded_files may contain:
    - {"workbook": uploaded_excel_file}
    - {"Real": file, "Fiscal": file, "External": file, "Monetary": file}
    """
    if uploaded_files is None:
        return _combine_default_blocks(DATA_DIR)

    if "workbook" in uploaded_files and uploaded_files["workbook"] is not None:
        return read_uploaded_excel(uploaded_files["workbook"])

    frames = []
    missing = []
    for block in DATA_FILES.keys():
        if block not in uploaded_files or uploaded_files[block] is None:
            missing.append(block)
        else:
            frames.append(read_uploaded_csv(uploaded_files[block], block))

    if missing:
        raise ValueError(f"Missing uploaded CSV file(s) for block(s): {missing}")

    return pd.concat(frames, ignore_index=True)


def _make_wide(raw: pd.DataFrame) -> pd.DataFrame:
    wide = (
        raw.sort_values(["Code", "Year"])
        .drop_duplicates(["Code", "Year"], keep="last")
        .pivot(index="Year", columns="Code", values="Value")
        .sort_index()
    )
    wide.columns.name = None
    return wide


def latest_actual_year(wide: pd.DataFrame) -> int:
    valid = wide.dropna(how="all")
    if valid.empty:
        raise ValueError("No usable actual data found.")
    return int(valid.index.max())


def load_source_data(data_dir: str | Path = DATA_DIR, uploaded_files: Dict[str, Any] | None = None) -> Dict[str, object]:
    data_dir = Path(data_dir)

    if uploaded_files:
        raw = _combine_uploaded_blocks(uploaded_files)
        source_mode = "uploaded"
    else:
        raw = _combine_default_blocks(data_dir)
        source_mode = "default_csv"

    raw = raw.sort_values(["Block", "Code", "Year"]).reset_index(drop=True)
    wide = _make_wide(raw)
    latest = latest_actual_year(wide)
    derived = compute_derived_indicators(wide)
    checks = validate_data(raw, wide, derived)

    return {
        "raw": raw,
        "wide": wide,
        "checks": checks,
        "derived": derived,
        "latest_actual_year": latest,
        "source_mode": source_mode,
    }


def validate_data(raw: pd.DataFrame, wide: pd.DataFrame, derived: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []

    def add(check, status, details):
        rows.append([check, status, details])

    dup = int(raw.duplicated(["Code", "Year"], keep=False).sum())
    add("Duplicate Code-Year rows", "OK" if dup == 0 else "CHECK", f"{dup} duplicate rows found")

    missing_codes = [c for c in REQUIRED_CODES if c not in wide.columns]
    add("Required codes present", "OK" if not missing_codes else "CHECK",
        "All required codes present" if not missing_codes else str(missing_codes))

    extra_codes = sorted([c for c in wide.columns if c not in REQUIRED_CODES])
    add("Additional non-required codes", "INFO" if extra_codes else "OK",
        "None" if not extra_codes else ", ".join(extra_codes[:40]) + (" ..." if len(extra_codes) > 40 else ""))

    add("Year coverage", "OK", f"{int(wide.index.min())}-{int(wide.index.max())}")

    latest = latest_actual_year(wide)
    add("Latest actual year detected", "OK", str(latest))

    # Block-level coverage
    block_coverage = (
        raw.dropna(subset=["Value"])
        .groupby("Block")["Year"]
        .agg(["min", "max"])
        .reset_index()
    )
    coverage_text = "; ".join([f"{r.Block}: {int(r['min'])}-{int(r['max'])}" for _, r in block_coverage.iterrows()])
    add("Block-level coverage", "OK", coverage_text)

    missing_values = {}
    for c in REQUIRED_CODES:
        if c in wide.columns:
            n = int(wide[c].isna().sum())
            if n:
                missing_values[c] = n
    add("Missing values in required codes", "OK" if not missing_values else "WATCH",
        "None" if not missing_values else str(missing_values))

    # GDP identity/statistical discrepancy
    if all(c in wide.columns for c in CORE_GDP_CODES):
        exp_gdp = wide["NPC"] + wide["NGC"] + wide["NINV"] + wide["NXGS"] - wide["NMGS"]
        sd = wide["NGDP"] - exp_gdp
        sd_pct = (sd / wide["NGDP"]).replace([np.inf, -np.inf], np.nan)
        max_abs_sd = float(sd_pct.abs().dropna().max()) if not sd_pct.dropna().empty else np.nan
        latest_sd = float(sd_pct.loc[latest]) if latest in sd_pct.index and pd.notna(sd_pct.loc[latest]) else np.nan

        status = "OK"
        if pd.notna(max_abs_sd) and max_abs_sd > SD_WATCH_THRESHOLD:
            status = "WATCH"
        add(
            "GDP expenditure identity / statistical discrepancy",
            status,
            f"Latest SD/GDP={latest_sd:,.2%}; max abs SD/GDP={max_abs_sd:,.2%}; threshold={SD_WATCH_THRESHOLD:,.0%}"
        )
    else:
        add("GDP expenditure identity / statistical discrepancy", "CHECK", f"Missing one of {CORE_GDP_CODES}")

    # SNBS revision series availability
    missing_snbs = [c for c in SNBS_REVISION_CODES if c not in wide.columns]
    add("SNBS GDP revision variables available", "OK" if not missing_snbs else "CHECK",
        "All available" if not missing_snbs else str(missing_snbs))

    return pd.DataFrame(rows, columns=["check", "status", "details"])


def compute_derived_indicators(wide: pd.DataFrame) -> pd.DataFrame:
    d = pd.DataFrame(index=wide.index)

    for code, out in [
        ("NGDP", "NGDP_growth"), ("RGDP", "RGDP_growth"), ("NPC", "NPC_growth"),
        ("NINV", "NINV_growth"), ("M_GOODS", "M_GOODS_growth"), ("X_GOODS", "X_GOODS_growth"),
        ("CPI_AVG", "Inflation_CPI_avg")
    ]:
        if code in wide.columns:
            d[out] = wide[code].astype(float).pct_change()

    if all(c in wide.columns for c in ["NPC", "NGC", "NINV", "NXGS", "NMGS", "NGDP"]):
        d["Final_consumption"] = wide["NPC"] + wide["NGC"]
        d["Absorption"] = d["Final_consumption"] + wide["NINV"]
        d["Expenditure_GDP_before_SD"] = d["Final_consumption"] + wide["NINV"] + wide["NXGS"] - wide["NMGS"]
        d["Statistical_discrepancy"] = wide["NGDP"] - d["Expenditure_GDP_before_SD"]
        d["Statistical_discrepancy_pct_GDP"] = d["Statistical_discrepancy"] / wide["NGDP"]

    if all(c in wide.columns for c in ["X_GOODS", "M_GOODS", "X_SERV", "M_SERV"]):
        d["Exports_GS_external"] = wide["X_GOODS"] + wide["X_SERV"]
        d["Imports_GS_external"] = wide["M_GOODS"].abs() + wide["M_SERV"].abs()
        d["Trade_balance_external"] = d["Exports_GS_external"] - d["Imports_GS_external"]

    if all(c in wide.columns for c in ["PRI_INC_CR", "PRI_INC_DB"]):
        d["Primary_income_balance"] = wide["PRI_INC_CR"] + wide["PRI_INC_DB"]
    if all(c in wide.columns for c in ["SEC_INC_CR", "SEC_INC_DB"]):
        d["Secondary_income_balance"] = wide["SEC_INC_CR"] + wide["SEC_INC_DB"]

    return d
