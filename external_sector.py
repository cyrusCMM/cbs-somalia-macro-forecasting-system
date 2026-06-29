# -*- coding: utf-8 -*-
"""
external_sector.py
External sector forecast, balances and insights.
"""

import pandas as pd


def _extend_abs_signed(wide: pd.DataFrame, code: str, growth_col: str, assumptions: pd.DataFrame) -> pd.Series:
    hist = wide[code].dropna().astype(float)
    sign = -1 if hist.iloc[-1] < 0 else 1
    s = hist.abs().copy()
    for year, row in assumptions.iterrows():
        s.loc[int(year)] = s.iloc[-1] * (1.0 + float(row[growth_col]))
    return (s * sign).sort_index()


def _extend_positive(wide: pd.DataFrame, code: str, growth_col: str, assumptions: pd.DataFrame) -> pd.Series:
    s = wide[code].dropna().astype(float).copy()
    for year, row in assumptions.iterrows():
        s.loc[int(year)] = s.iloc[-1] * (1.0 + float(row[growth_col]))
    return s.sort_index()


def forecast_external_sector(wide: pd.DataFrame, assumptions: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=sorted(set(wide.index).union(assumptions.index)))
    if "X_GOODS" in wide: out["X_GOODS"] = _extend_positive(wide, "X_GOODS", "X_GOODS_growth", assumptions)
    if "M_GOODS" in wide: out["M_GOODS"] = _extend_positive(wide, "M_GOODS", "M_GOODS_growth", assumptions)
    if "X_SERV" in wide: out["X_SERV"] = _extend_positive(wide, "X_SERV", "X_SERV_growth", assumptions)
    if "M_SERV" in wide: out["M_SERV"] = _extend_abs_signed(wide, "M_SERV", "M_SERV_growth", assumptions)

    if "PRI_INC_CR" in wide: out["PRI_INC_CR"] = _extend_positive(wide, "PRI_INC_CR", "Primary_income_credit_growth", assumptions)
    if "PRI_INC_DB" in wide: out["PRI_INC_DB"] = _extend_abs_signed(wide, "PRI_INC_DB", "Primary_income_debit_growth", assumptions)
    if "SEC_INC_CR" in wide: out["SEC_INC_CR"] = _extend_positive(wide, "SEC_INC_CR", "Secondary_income_credit_growth", assumptions)
    if "SEC_INC_DB" in wide: out["SEC_INC_DB"] = _extend_abs_signed(wide, "SEC_INC_DB", "Secondary_income_debit_growth", assumptions)

    if "NER_AVG" in wide: out["NER_AVG"] = _extend_positive(wide, "NER_AVG", "NER_AVG_growth", assumptions)
    if "PM" in wide: out["PM"] = _extend_positive(wide, "PM", "PM_growth", assumptions)
    if "PX" in wide: out["PX"] = _extend_positive(wide, "PX", "PX_growth", assumptions)

    if all(c in out for c in ["X_GOODS", "X_SERV"]):
        out["Exports_GS"] = out["X_GOODS"] + out["X_SERV"]
    if all(c in out for c in ["M_GOODS", "M_SERV"]):
        out["Imports_GS"] = out["M_GOODS"].abs() + out["M_SERV"].abs()
    if all(c in out for c in ["Exports_GS", "Imports_GS"]):
        out["Trade_balance"] = out["Exports_GS"] - out["Imports_GS"]

    if all(c in out for c in ["PRI_INC_CR", "PRI_INC_DB"]):
        out["Primary_income_balance"] = out["PRI_INC_CR"] + out["PRI_INC_DB"]
    if all(c in out for c in ["SEC_INC_CR", "SEC_INC_DB"]):
        out["Secondary_income_balance"] = out["SEC_INC_CR"] + out["SEC_INC_DB"]
    if all(c in out for c in ["Trade_balance", "Primary_income_balance", "Secondary_income_balance"]):
        out["CAB"] = out["Trade_balance"] + out["Primary_income_balance"] + out["Secondary_income_balance"]
    return out


def external_sector_insights(external: pd.DataFrame, real: pd.DataFrame) -> list[str]:
    latest = int(external.index.max())
    ngdp = real.loc[latest, "NGDP"] if latest in real.index else None
    tb = external.loc[latest, "Trade_balance"]
    cab = external.loc[latest, "CAB"] if "CAB" in external else None
    imp = external.loc[latest, "Imports_GS"]
    exp = external.loc[latest, "Exports_GS"]
    return [
        f"Exports of goods and services reach USD {exp/1e9:,.1f} billion by {latest}.",
        f"Imports remain larger than exports, at USD {imp/1e9:,.1f} billion by {latest}.",
        f"The trade balance is {tb/ngdp*100:,.1f}% of GDP by {latest}." if ngdp else "The trade balance remains the main external pressure point.",
        f"The current account is {cab/ngdp*100:,.1f}% of GDP by {latest}." if ngdp and cab is not None else "Transfers and income flows remain important for the current account."
    ]
