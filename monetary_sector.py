# -*- coding: utf-8 -*-
"""
monetary_sector.py
Monetary forecast and insights.
"""

import pandas as pd
import numpy as np


def _recent_ratio(wide, num, den, fallback=0.1):
    if num not in wide.columns or den not in wide.columns:
        return fallback
    df = pd.concat([wide[num], wide[den]], axis=1).dropna()
    if df.empty:
        return fallback
    r = (df.iloc[:, 0] / df.iloc[:, 1]).replace([np.inf, -np.inf], np.nan).dropna()
    return float(r.tail(3).mean()) if len(r) else fallback


def forecast_monetary_sector(wide: pd.DataFrame, real: pd.DataFrame, assumptions: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=assumptions.index)
    ngdp = real.loc[assumptions.index, "NGDP"]

    m2_ratio = _recent_ratio(wide, "M2", "NGDP", fallback=0.12)
    dep_ratio = _recent_ratio(wide, "TOT_DEP", "NGDP", fallback=0.12)
    psc_dep_ratio = _recent_ratio(wide, "PSC", "TOT_DEP", fallback=0.30)
    nfa_ratio = _recent_ratio(wide, "NFA", "NGDP", fallback=0.05)
    nda_ratio = _recent_ratio(wide, "NDA", "NGDP", fallback=0.05)

    out["M2"] = ngdp * m2_ratio
    out["TOT_DEP"] = ngdp * dep_ratio
    out["PSC"] = out["TOT_DEP"] * psc_dep_ratio
    out["NFA"] = ngdp * nfa_ratio
    out["NDA"] = ngdp * nda_ratio
    out["M2_GDP"] = out["M2"] / ngdp
    out["PSC_GDP"] = out["PSC"] / ngdp
    return out


def monetary_sector_insights(monetary: pd.DataFrame) -> list[str]:
    latest = int(monetary.index.max())
    m2_gdp = monetary.loc[latest, "M2_GDP"]
    psc_gdp = monetary.loc[latest, "PSC_GDP"]
    return [
        f"Broad money is projected at {m2_gdp*100:,.1f}% of GDP by {latest}.",
        f"Private sector credit is projected at {psc_gdp*100:,.1f}% of GDP by {latest}.",
        "Deposits remain the central balance-sheet channel for monetary deepening.",
        "The monetary block should be interpreted cautiously because the historical sample is short."
    ]
