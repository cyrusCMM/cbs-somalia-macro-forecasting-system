# -*- coding: utf-8 -*-
"""
reconciliation.py
GDP reconciliation and clean macro output.
"""

import pandas as pd
from config import SD_WATCH_THRESHOLD


def build_gdp_reconciliation(real: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=real.index)
    out["GDP"] = real["NGDP"]
    out["Final_consumption"] = real["Final_consumption"]
    out["Investment"] = real["NINV"]
    out["Exports_GS"] = real["NXGS"]
    out["Imports_GS"] = real["NMGS"]
    out["Expenditure_GDP_before_SD"] = out["Final_consumption"] + out["Investment"] + out["Exports_GS"] - out["Imports_GS"]
    out["Statistical_discrepancy"] = out["GDP"] - out["Expenditure_GDP_before_SD"]
    out["Statistical_discrepancy_pct_GDP"] = out["Statistical_discrepancy"] / out["GDP"]
    out["Reconciled_GDP"] = out["Expenditure_GDP_before_SD"] + out["Statistical_discrepancy"]
    out["Check"] = out["Reconciled_GDP"] - out["GDP"]
    out["SD_Flag"] = out["Statistical_discrepancy_pct_GDP"].abs().apply(lambda x: "OK" if x <= SD_WATCH_THRESHOLD else "WATCH")
    return out


def build_nominal_gdp_output(real: pd.DataFrame, external: pd.DataFrame) -> pd.DataFrame:
    years = real.index
    rows = [
        "GDP", "Final consumption", "Private", "Public",
        "Gross fixed capital formation", "Private investment", "Public investment", "Change in stocks",
        "Foreign balance", "Exports of goods and services", "Imports of goods and services", "Statistical discrepancy",
        "Gross National Income", "Gross National Disposable Income", "Absorption", "National saving",
        "Investment", "Saving - Investment balance", "CAB", "Primary income balance", "Secondary income balance"
    ]
    out = pd.DataFrame(index=rows, columns=years, dtype=float)
    out.loc["GDP"] = real["NGDP"]
    out.loc["Final consumption"] = real["Final_consumption"]
    out.loc["Private"] = real["NPC"]
    out.loc["Public"] = real["NGC"]
    out.loc["Gross fixed capital formation"] = real["NINV"]
    out.loc["Private investment"] = real["NINV"]
    out.loc["Public investment"] = 0.0
    out.loc["Change in stocks"] = 0.0
    out.loc["Exports of goods and services"] = real["NXGS"]
    out.loc["Imports of goods and services"] = real["NMGS"]
    out.loc["Foreign balance"] = real["NXGS"] - real["NMGS"]
    out.loc["Statistical discrepancy"] = real["NGDP"] - (real["Final_consumption"] + real["NINV"] + real["NXGS"] - real["NMGS"])

    primary = external["Primary_income_balance"] if "Primary_income_balance" in external else 0.0
    secondary = external["Secondary_income_balance"] if "Secondary_income_balance" in external else 0.0
    cab = external["CAB"] if "CAB" in external else out.loc["Foreign balance"] + primary + secondary

    out.loc["Primary income balance"] = primary
    out.loc["Secondary income balance"] = secondary
    out.loc["Gross National Income"] = out.loc["GDP"] + out.loc["Primary income balance"]
    out.loc["Gross National Disposable Income"] = out.loc["Gross National Income"] + out.loc["Secondary income balance"]
    out.loc["Absorption"] = out.loc["Final consumption"] + out.loc["Gross fixed capital formation"]
    out.loc["National saving"] = out.loc["Gross National Disposable Income"] - out.loc["Final consumption"]
    out.loc["Investment"] = out.loc["Gross fixed capital formation"]
    out.loc["Saving - Investment balance"] = out.loc["National saving"] - out.loc["Investment"]
    out.loc["CAB"] = cab
    return out
