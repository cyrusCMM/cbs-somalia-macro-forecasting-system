# -*- coding: utf-8 -*-
"""
real_sector.py
Real sector forecast and presentation helpers.

v8 validation-gate update
-------------------------
For forecast years, nominal GDP is reconciled to the expenditure identity.
This preserves the demand-side model logic and prevents the statistical
discrepancy from becoming a residual that explodes over the forecast period.

Historical years keep official NGDP and the observed statistical discrepancy.
Forecast years use the latest observed SD/GDP ratio as the reconciliation
target, usually close to zero after the SNBS update.
"""

import pandas as pd
import numpy as np


def _extend_series(wide: pd.DataFrame, code: str, growth_col: str, assumptions: pd.DataFrame) -> pd.Series:
    s = wide[code].dropna().astype(float).copy()
    for year, row in assumptions.iterrows():
        s.loc[int(year)] = s.iloc[-1] * (1.0 + float(row[growth_col]))
    return s.sort_index()


def _latest_sd_ratio(wide: pd.DataFrame) -> float:
    required = ["NGDP", "NPC", "NGC", "NINV", "NXGS", "NMGS"]
    if not all(c in wide.columns for c in required):
        return 0.0
    df = wide[required].dropna()
    if df.empty:
        return 0.0
    exp_gdp = df["NPC"] + df["NGC"] + df["NINV"] + df["NXGS"] - df["NMGS"]
    sd_ratio = ((df["NGDP"] - exp_gdp) / df["NGDP"]).replace([np.inf, -np.inf], np.nan).dropna()
    if sd_ratio.empty:
        return 0.0
    # Use latest actual, but keep it inside a narrow technical band.
    return float(np.clip(sd_ratio.iloc[-1], -0.02, 0.02))


def forecast_real_sector(wide: pd.DataFrame, assumptions: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=sorted(set(wide.index).union(assumptions.index)))

    for code, growth in [
        ("NGDP", "NGDP_growth"), ("RGDP", "RGDP_growth"), ("NPC", "NPC_growth"),
        ("NGC", "NGC_growth"), ("NINV", "NINV_growth"), ("NXGS", "NXGS_growth"),
        ("NMGS", "NMGS_growth"), ("CPI_AVG", "Inflation"),
    ]:
        if code in wide.columns:
            out[code] = _extend_series(wide, code, growth, assumptions)

    if "NPC" in out and "NGC" in out:
        out["Final_consumption"] = out["NPC"] + out["NGC"]

    if all(c in out for c in ["Final_consumption", "NINV", "NXGS", "NMGS"]):
        out["Absorption"] = out["Final_consumption"] + out["NINV"]
        out["Expenditure_GDP_before_SD"] = out["Final_consumption"] + out["NINV"] + out["NXGS"] - out["NMGS"]

    # Reconcile nominal GDP in forecast years to the expenditure identity.
    if all(c in out for c in ["NGDP", "Expenditure_GDP_before_SD"]):
        target_sd_ratio = _latest_sd_ratio(wide)
        for year in assumptions.index:
            year = int(year)
            exp_value = out.loc[year, "Expenditure_GDP_before_SD"]
            if pd.notna(exp_value):
                out.loc[year, "NGDP"] = exp_value / (1.0 - target_sd_ratio)

        out["Statistical_discrepancy"] = out["NGDP"] - out["Expenditure_GDP_before_SD"]
        out["Statistical_discrepancy_pct_GDP"] = out["Statistical_discrepancy"] / out["NGDP"]

    out["GDP_growth"] = out["NGDP"].pct_change()
    out["Real_GDP_growth"] = out["RGDP"].pct_change()
    return out


def real_sector_insights(real: pd.DataFrame) -> list[str]:
    latest = int(real.index.max())
    gdp = real.loc[latest, "NGDP"]
    cons_share = real.loc[latest, "Final_consumption"] / gdp
    inv_share = real.loc[latest, "NINV"] / gdp
    imp_share = real.loc[latest, "NMGS"] / gdp
    return [
        f"Nominal GDP reaches about USD {gdp/1e9:,.1f} billion by {latest}.",
        f"Final consumption remains the largest demand component at about {cons_share*100:,.1f}% of GDP.",
        f"Investment is projected at about {inv_share*100:,.1f}% of GDP, indicating the scale of domestic capital formation.",
        f"Imports remain structurally large at about {imp_share*100:,.1f}% of GDP, keeping external consistency central to the forecast."
    ]
