# -*- coding: utf-8 -*-
"""
data_loader.py
Read block CSV source data and prepare model-ready frames.
"""

from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np

from config import DATA_DIR, DATA_FILES

REQUIRED_COLUMNS = ["Block", "Variable", "Code", "Type", "Unit", "Source"]

REQUIRED_CODES = [
    "NGDP", "RGDP", "NPC", "NGC", "NINV", "NXGS", "NMGS", "CPI_AVG", "CPI_EOP",
    "IMP_DUTY", "DOM_SALES", "PIT", "CIT", "NONTAX", "GRANTS",
    "WAGES", "GDS_SERV_EXP", "TRANSFERS", "INT_PAY", "CAPEX", "OTHER_EXP",
    "X_GOODS", "M_GOODS", "X_SERV", "M_SERV",
    "PRI_INC_CR", "PRI_INC_DB", "SEC_INC_CR", "SEC_INC_DB", "CAB", "NER_AVG", "PM", "PX",
    "M2", "TOT_DEP", "PSC", "NFA", "NDA",
]


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for col in ["Block", "Variable", "Code", "Type", "Unit", "Source"]:
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


def read_block_csv(path: Path, block_name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {block_name} data file: {path}")

    df = _normalise_columns(pd.read_csv(path))
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {missing}")

    years = _year_columns(df)
    if not years:
        raise ValueError(f"{path.name} has no year columns.")

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


def load_source_data(data_dir: str | Path = DATA_DIR) -> Dict[str, object]:
    data_dir = Path(data_dir)
    frames = []
    for block, filename in DATA_FILES.items():
        frames.append(read_block_csv(data_dir / filename, block))

    raw = pd.concat(frames, ignore_index=True).sort_values(["Block", "Code", "Year"]).reset_index(drop=True)
    wide = (
        raw.sort_values(["Code", "Year"])
        .drop_duplicates(["Code", "Year"], keep="last")
        .pivot(index="Year", columns="Code", values="Value")
        .sort_index()
    )
    wide.columns.name = None

    return {
        "raw": raw,
        "wide": wide,
        "checks": validate_data(raw, wide),
        "derived": compute_derived_indicators(wide),
    }


def validate_data(raw: pd.DataFrame, wide: pd.DataFrame) -> pd.DataFrame:
    rows = []
    dup = int(raw.duplicated(["Code", "Year"], keep=False).sum())
    rows.append(["Duplicate Code-Year rows", "OK" if dup == 0 else "CHECK", f"{dup} duplicate rows found"])

    missing_codes = [c for c in REQUIRED_CODES if c not in wide.columns]
    rows.append(["Required codes present", "OK" if not missing_codes else "CHECK",
                 "All required codes present" if not missing_codes else str(missing_codes)])

    rows.append(["Year coverage", "OK", f"{int(wide.index.min())}-{int(wide.index.max())}"])

    missing_values = {}
    for c in REQUIRED_CODES:
        if c in wide.columns:
            n = int(wide[c].isna().sum())
            if n:
                missing_values[c] = n
    rows.append(["Missing values in required codes", "OK" if not missing_values else "WATCH",
                 "None" if not missing_values else str(missing_values)])

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
