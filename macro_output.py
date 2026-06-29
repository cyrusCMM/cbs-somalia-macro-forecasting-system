# -*- coding: utf-8 -*-
"""
macro_output.py

Builds clean macro-framework outputs for Excel/CSV export.

This avoids gaps caused by exporting block tables separately. The output
combines real, fiscal, external and monetary variables into one consistent
macro framework table.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from config import CURRENCY_SCALE


def _get(df: pd.DataFrame, col: str, years, scale: float = 1.0):
    if col not in df.columns:
        return pd.Series(index=years, dtype=float)
    return df[col].reindex(years) / scale


def build_macro_framework(results: dict, scale_to_millions: bool = True) -> pd.DataFrame:
    real = results["Real_Sector"]
    fiscal = results["Fiscal_Sector"]
    external = results["External_Sector"]
    monetary = results["Monetary_Sector"]
    rec = results["GDP_Reconciliation"]

    years = sorted(set(real.index).union(fiscal.index).union(external.index).union(monetary.index))
    scale = CURRENCY_SCALE if scale_to_millions else 1.0

    rows = []

    def add(section, item, series, unit="USD million"):
        rows.append([section, item, unit] + [series.get(y, np.nan) for y in years])

    # Real sector
    add("Real Sector", "Nominal GDP", _get(real, "NGDP", years, scale))
    add("Real Sector", "Real GDP", _get(real, "RGDP", years, scale))
    add("Real Sector", "Final consumption", _get(real, "Final_consumption", years, scale))
    add("Real Sector", "Private consumption", _get(real, "NPC", years, scale))
    add("Real Sector", "Public consumption", _get(real, "NGC", years, scale))
    add("Real Sector", "Investment", _get(real, "NINV", years, scale))
    add("Real Sector", "Exports of goods and services", _get(real, "NXGS", years, scale))
    add("Real Sector", "Imports of goods and services", _get(real, "NMGS", years, scale))
    add("Real Sector", "Absorption", _get(real, "Absorption", years, scale))
    add("Real Sector", "Statistical discrepancy", _get(rec, "Statistical_discrepancy", years, scale))
    add("Real Sector", "Statistical discrepancy / GDP", _get(rec, "Statistical_discrepancy_pct_GDP", years, 1.0), "Ratio")

    # Fiscal sector
    add("Fiscal Sector", "Customs duties", _get(fiscal, "IMP_DUTY", years, scale))
    add("Fiscal Sector", "Sales tax / VAT", _get(fiscal, "DOM_SALES", years, scale))
    add("Fiscal Sector", "Income tax", _get(fiscal, "PIT", years, scale))
    add("Fiscal Sector", "Corporate income tax", _get(fiscal, "CIT", years, scale))
    add("Fiscal Sector", "Non-tax revenue", _get(fiscal, "NONTAX", years, scale))
    add("Fiscal Sector", "Grants", _get(fiscal, "GRANTS", years, scale))
    add("Fiscal Sector", "Total revenue and grants", _get(fiscal, "TOTAL_REVENUE", years, scale))
    add("Fiscal Sector", "Wages", _get(fiscal, "WAGES", years, scale))
    add("Fiscal Sector", "Goods and services", _get(fiscal, "GDS_SERV_EXP", years, scale))
    add("Fiscal Sector", "Transfers", _get(fiscal, "TRANSFERS", years, scale))
    add("Fiscal Sector", "Capital expenditure", _get(fiscal, "CAPEX", years, scale))
    add("Fiscal Sector", "Other expenditure", _get(fiscal, "OTHER_EXP", years, scale))
    add("Fiscal Sector", "Interest payments", _get(fiscal, "INT_PAY", years, scale))
    add("Fiscal Sector", "Total expenditure", _get(fiscal, "TOTAL_EXPENDITURE", years, scale))
    add("Fiscal Sector", "Fiscal balance", _get(fiscal, "FISCAL_BALANCE", years, scale))
    add("Fiscal Sector", "Fiscal balance / GDP", _get(fiscal, "FISCAL_BALANCE_GDP", years, 1.0), "Ratio")
    add("Fiscal Sector", "Debt", _get(fiscal, "DEBT", years, scale))
    add("Fiscal Sector", "Debt / GDP", _get(fiscal, "DEBT_GDP", years, 1.0), "Ratio")

    # External sector
    add("External Sector", "Goods exports", _get(external, "X_GOODS", years, scale))
    add("External Sector", "Goods imports", _get(external, "M_GOODS", years, scale))
    add("External Sector", "Services exports", _get(external, "X_SERV", years, scale))
    add("External Sector", "Services imports", _get(external, "M_SERV", years, scale))
    add("External Sector", "Exports of goods and services", _get(external, "Exports_GS", years, scale))
    add("External Sector", "Imports of goods and services", _get(external, "Imports_GS", years, scale))
    add("External Sector", "Trade balance", _get(external, "Trade_balance", years, scale))
    add("External Sector", "Primary income balance", _get(external, "Primary_income_balance", years, scale))
    add("External Sector", "Secondary income balance", _get(external, "Secondary_income_balance", years, scale))
    add("External Sector", "Current account balance", _get(external, "CAB", years, scale))
    if "NGDP" in real:
        add("External Sector", "Current account / GDP", (external["CAB"].reindex(years) / real["NGDP"].reindex(years)), "Ratio")
        add("External Sector", "Trade balance / GDP", (external["Trade_balance"].reindex(years) / real["NGDP"].reindex(years)), "Ratio")

    # Monetary sector
    add("Monetary Sector", "Broad money M2", _get(monetary, "M2", years, scale))
    add("Monetary Sector", "Total deposits", _get(monetary, "TOT_DEP", years, scale))
    add("Monetary Sector", "Private sector credit", _get(monetary, "PSC", years, scale))
    add("Monetary Sector", "Net foreign assets", _get(monetary, "NFA", years, scale))
    add("Monetary Sector", "Net domestic assets", _get(monetary, "NDA", years, scale))
    add("Monetary Sector", "M2 / GDP", _get(monetary, "M2_GDP", years, 1.0), "Ratio")
    add("Monetary Sector", "Private sector credit / GDP", _get(monetary, "PSC_GDP", years, 1.0), "Ratio")

    out = pd.DataFrame(rows, columns=["Section", "Indicator", "Unit"] + years)
    return out


def build_key_indicators(results: dict) -> pd.DataFrame:
    """Compact executive indicators table."""
    framework = build_macro_framework(results)
    keep = [
        "Nominal GDP",
        "Real GDP",
        "Final consumption",
        "Investment",
        "Total revenue and grants",
        "Total expenditure",
        "Fiscal balance / GDP",
        "Debt / GDP",
        "Current account / GDP",
        "M2 / GDP",
        "Private sector credit / GDP",
        "Statistical discrepancy / GDP",
    ]
    return framework[framework["Indicator"].isin(keep)].reset_index(drop=True)
