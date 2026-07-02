# -*- coding: utf-8 -*-
"""
model_validation.py

Final consistency and plausibility validation for the CBS Somalia macro model.

This module is deliberately separate from the data loader. data_loader.py checks
whether source data are structurally valid. model_validation.py checks whether the
solved model output is economically coherent before dashboards and reports are used.

The validation gate has two objectives:
1. prevent impossible ratios from appearing in the executive dashboard;
2. preserve the model logic while flagging inconsistencies that need review.

Severity levels
---------------
OK       : check passed.
INFO     : information only.
WATCH    : plausible but should be reviewed.
ERROR    : material inconsistency; dashboards should be treated as not fit for use.
"""

from __future__ import annotations

import math
import numpy as np
import pandas as pd


# Conservative plausibility bands. These are not policy targets. They are guardrails
# to prevent obvious unit/sign/linking errors from being presented as results.
PLAUSIBILITY_BOUNDS = {
    "Current account/GDP": (-0.80, 0.80),
    "Trade balance/GDP": (-1.00, 0.60),
    "Fiscal balance/GDP": (-0.50, 0.50),
    "Debt/GDP": (0.00, 2.50),
    "Revenue/GDP": (0.00, 1.00),
    "Expenditure/GDP": (0.00, 1.20),
    "M2/GDP": (0.00, 2.00),
    "PSC/GDP": (0.00, 2.00),
    "Imports/GDP": (0.00, 2.50),
    "Exports/GDP": (0.00, 2.00),
    "Consumption/GDP": (0.00, 2.50),
    "Investment/GDP": (0.00, 1.50),
    "Real GDP growth": (-0.30, 0.30),
    "Nominal GDP growth": (-0.30, 0.50),
}


def _finite(x) -> bool:
    try:
        return x is not None and not pd.isna(x) and np.isfinite(float(x))
    except Exception:
        return False


def _ratio(num, den):
    if not _finite(num) or not _finite(den) or float(den) == 0:
        return np.nan
    return float(num) / float(den)


def _row(check, status, value=np.nan, details="", year=None, threshold=""):
    return {
        "check": check,
        "status": status,
        "year": year,
        "value": value,
        "threshold": threshold,
        "details": details,
    }


def _check_range(name, value, year=None, severity_if_fail="ERROR"):
    lo, hi = PLAUSIBILITY_BOUNDS[name]
    if not _finite(value):
        return _row(name, "ERROR", value, "Missing or non-finite value.", year, f"{lo:g} to {hi:g}")
    status = "OK" if lo <= float(value) <= hi else severity_if_fail
    details = "Within plausibility range." if status == "OK" else "Outside plausibility range; check units, signs, or model linkages."
    return _row(name, status, float(value), details, year, f"{lo:g} to {hi:g}")


def build_executive_indicators(results: dict) -> pd.DataFrame:
    """
    Build executive indicators from final solved model outputs only.

    The dashboard should use this table rather than recomputing ratios ad hoc
    from mixed raw/forecast data.
    """
    real = results["Real_Sector"]
    fiscal = results["Fiscal_Sector"]
    external = results["External_Sector"]
    monetary = results["Monetary_Sector"]

    latest = int(real.index.max())
    fiscal_year = int(fiscal.index.max())
    monetary_year = int(monetary.index.max())

    ngdp = real.loc[latest, "NGDP"]
    rows = []

    def add(name, value, unit="", year=latest):
        rows.append({"Indicator": name, "Value": value, "Unit": unit, "Year": year})

    add("Nominal GDP", ngdp, "USD")
    add("Real GDP growth", real.loc[latest, "Real_GDP_growth"], "Ratio")
    add("Nominal GDP growth", real.loc[latest, "GDP_growth"], "Ratio")
    add("Consumption/GDP", _ratio(real.loc[latest, "Final_consumption"], ngdp), "Ratio")
    add("Investment/GDP", _ratio(real.loc[latest, "NINV"], ngdp), "Ratio")
    add("Exports/GDP", _ratio(real.loc[latest, "NXGS"], ngdp), "Ratio")
    add("Imports/GDP", _ratio(real.loc[latest, "NMGS"], ngdp), "Ratio")

    if latest in external.index:
        add("Trade balance/GDP", _ratio(external.loc[latest, "Trade_balance"], ngdp), "Ratio")
        add("Current account/GDP", _ratio(external.loc[latest, "CAB"], ngdp), "Ratio")

    if fiscal_year in real.index:
        f_ngdp = real.loc[fiscal_year, "NGDP"]
        add("Revenue/GDP", _ratio(fiscal.loc[fiscal_year, "TOTAL_REVENUE"], f_ngdp), "Ratio", fiscal_year)
        add("Expenditure/GDP", _ratio(fiscal.loc[fiscal_year, "TOTAL_EXPENDITURE"], f_ngdp), "Ratio", fiscal_year)
        add("Fiscal balance/GDP", _ratio(fiscal.loc[fiscal_year, "FISCAL_BALANCE"], f_ngdp), "Ratio", fiscal_year)
        add("Debt/GDP", _ratio(fiscal.loc[fiscal_year, "DEBT"], f_ngdp), "Ratio", fiscal_year)

    if monetary_year in real.index:
        m_ngdp = real.loc[monetary_year, "NGDP"]
        add("M2/GDP", _ratio(monetary.loc[monetary_year, "M2"], m_ngdp), "Ratio", monetary_year)
        add("PSC/GDP", _ratio(monetary.loc[monetary_year, "PSC"], m_ngdp), "Ratio", monetary_year)

    return pd.DataFrame(rows)


def validate_model_outputs(results: dict) -> pd.DataFrame:
    """
    Validate final solved model outputs.

    Returns a dataframe with status values: OK, INFO, WATCH, ERROR.
    """
    rows = []

    real = results["Real_Sector"]
    fiscal = results["Fiscal_Sector"]
    external = results["External_Sector"]
    monetary = results["Monetary_Sector"]
    rec = results["GDP_Reconciliation"]

    # 1. Required output tables.
    for name in ["Real_Sector", "Fiscal_Sector", "External_Sector", "Monetary_Sector", "GDP_Reconciliation"]:
        obj = results.get(name)
        ok = isinstance(obj, pd.DataFrame) and not obj.empty
        rows.append(_row(f"{name} exists", "OK" if ok else "ERROR", details="Output table generated." if ok else "Missing or empty output table."))

    # 2. Missing values in forecast years.
    forecast_start = results.get("Forecast_Start_Year", None)
    forecast_end = results.get("Forecast_End_Year", None)
    if forecast_start is not None and forecast_end is not None:
        for name, df in [("Real_Sector", real), ("Fiscal_Sector", fiscal), ("External_Sector", external), ("Monetary_Sector", monetary)]:
            idx = [y for y in df.index if int(y) >= int(forecast_start) and int(y) <= int(forecast_end)]
            if idx:
                sub = df.loc[idx]
                missing = int(sub.isna().sum().sum())
                rows.append(_row(f"{name} forecast missing values", "OK" if missing == 0 else "ERROR", missing, f"{missing} missing forecast cells."))

    # 3. GDP reconciliation check.
    if "Check" in rec.columns:
        max_abs_check = float(rec["Check"].abs().dropna().max()) if not rec["Check"].dropna().empty else 0.0
        rows.append(_row("GDP reconciliation arithmetic", "OK" if max_abs_check <= 1e-3 else "ERROR", max_abs_check, "Reconciled GDP minus GDP; tolerance allows floating-point rounding."))

    if "Statistical_discrepancy_pct_GDP" in rec.columns:
        latest = int(rec.index.max())
        latest_sd = rec.loc[latest, "Statistical_discrepancy_pct_GDP"]
        max_sd = rec["Statistical_discrepancy_pct_GDP"].abs().dropna().max()
        status = "OK" if _finite(latest_sd) and abs(float(latest_sd)) <= 0.10 else "WATCH"
        rows.append(_row("Latest statistical discrepancy/GDP", status, latest_sd, "Latest year SD/GDP.", latest, "abs <= 10%"))

        # Historic samples may have old benchmark breaks. Keep max SD as WATCH, not ERROR.
        status_max = "OK" if _finite(max_sd) and float(max_sd) <= 0.40 else "WATCH"
        rows.append(_row("Maximum statistical discrepancy/GDP", status_max, max_sd, "Full-sample max absolute SD/GDP.", None, "abs <= 40%"))

    # 4. Plausibility checks using final solved outputs.
    indicators = build_executive_indicators(results)
    for _, r in indicators.iterrows():
        name = r["Indicator"]
        if name in PLAUSIBILITY_BOUNDS:
            severity = "WATCH" if name == "Debt/GDP" else "ERROR"
            rows.append(_check_range(name, r["Value"], r["Year"], severity_if_fail=severity))

    # 5. External-sector identity and sign checks.
    latest_external = int(external.index.max())
    if all(c in external.columns for c in ["Trade_balance", "Primary_income_balance", "Secondary_income_balance", "CAB"]):
        lhs = external["CAB"]
        rhs = external["Trade_balance"] + external["Primary_income_balance"] + external["Secondary_income_balance"]
        err = (lhs - rhs).abs().dropna()
        max_err = float(err.max()) if not err.empty else 0.0
        rows.append(_row("Current account identity", "OK" if max_err <= 1e-6 else "ERROR", max_err, "CAB - (trade + primary + secondary)."))

    if "Imports_GS" in external.columns:
        imp_latest = external.loc[latest_external, "Imports_GS"]
        rows.append(_row("External imports positive", "OK" if _finite(imp_latest) and imp_latest >= 0 else "ERROR", imp_latest, "Imports_GS should be positive."))

    # 6. Fiscal identity checks.
    latest_fiscal = int(fiscal.index.max())
    if all(c in fiscal.columns for c in ["TOTAL_REVENUE", "TOTAL_EXPENDITURE", "FISCAL_BALANCE"]):
        err = (fiscal["FISCAL_BALANCE"] - (fiscal["TOTAL_REVENUE"] - fiscal["TOTAL_EXPENDITURE"])).abs().dropna()
        max_err = float(err.max()) if not err.empty else 0.0
        rows.append(_row("Fiscal balance identity", "OK" if max_err <= 1e-6 else "ERROR", max_err, "Balance - (revenue - expenditure)."))

    if "DEBT" in fiscal.columns:
        latest_debt = fiscal.loc[latest_fiscal, "DEBT"]
        status = "WATCH" if _finite(latest_debt) and latest_debt == 0 else ("OK" if _finite(latest_debt) and latest_debt > 0 else "ERROR")
        rows.append(_row("Debt stock availability", status, latest_debt, "Zero debt may indicate missing GOV_DEBT source or a closure rule that pays down debt fully."))

    # 7. Monetary identity checks.
    latest_monetary = int(monetary.index.max())
    if all(c in monetary.columns for c in ["M2", "M2_GDP"]):
        m_ngdp = real.loc[latest_monetary, "NGDP"] if latest_monetary in real.index else np.nan
        calc = _ratio(monetary.loc[latest_monetary, "M2"], m_ngdp)
        stored = monetary.loc[latest_monetary, "M2_GDP"]
        diff = abs(calc - stored) if _finite(calc) and _finite(stored) else np.nan
        rows.append(_row("M2/GDP identity", "OK" if _finite(diff) and diff <= 1e-9 else "ERROR", diff, "Stored M2_GDP versus M2/NGDP."))

    out = pd.DataFrame(rows)
    # Ensure stable column order
    return out[["check", "status", "year", "value", "threshold", "details"]]


def has_critical_errors(validation: pd.DataFrame) -> bool:
    if validation is None or validation.empty:
        return True
    return bool((validation["status"] == "ERROR").any())


def validation_summary(validation: pd.DataFrame) -> dict:
    if validation is None or validation.empty:
        return {"ERROR": 1}
    return validation["status"].value_counts().to_dict()


def safe_indicator_value(indicators: pd.DataFrame, validation: pd.DataFrame, indicator: str):
    """
    Return value only if the indicator has no ERROR in validation. Otherwise return None.
    """
    if indicators is None or indicators.empty:
        return None
    r = indicators[indicators["Indicator"] == indicator]
    if r.empty:
        return None

    if validation is not None and not validation.empty:
        failed = validation[(validation["check"] == indicator) & (validation["status"] == "ERROR")]
        if not failed.empty:
            return None

    val = r.iloc[0]["Value"]
    return val if _finite(val) else None
