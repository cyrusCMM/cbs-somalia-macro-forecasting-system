# -*- coding: utf-8 -*-
"""
assumptions.py
Scenario assumptions for baseline, optimistic, pessimistic and custom runs.

v8 validation-gate update
-------------------------
The model now uses robust recent-growth assumptions instead of mechanically
projecting extreme revision-year growth rates. This preserves the forecasting
logic but prevents one-off statistical revisions from producing explosive
exports, imports or current account paths.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd

from config import FORECAST_START_YEAR, FORECAST_END_YEAR


@dataclass
class ScenarioShock:
    real_gdp_growth_add: float = 0.0
    nominal_gdp_growth_add: float = 0.0
    inflation_add: float = 0.0
    consumption_growth_add: float = 0.0
    investment_growth_add: float = 0.0
    exports_growth_add: float = 0.0
    imports_growth_add: float = 0.0
    grants_gdp_ratio_add: float = 0.0
    revenue_effort_add: float = 0.0
    expenditure_pressure_add: float = 0.0


def _clip(v: float, lo: float = -0.30, hi: float = 0.50) -> float:
    return float(np.clip(0.0 if pd.isna(v) else v, lo, hi))


def _recent_avg_growth(
    s: pd.Series,
    periods: int = 5,
    fallback: float = 0.05,
    lo: float = -0.15,
    hi: float = 0.20,
    method: str = "median",
) -> float:
    """
    Robust recent growth estimator.

    Uses median by default because annual source revisions can create
    one-off jumps that should not be projected mechanically for 10 years.
    """
    s = s.dropna().astype(float)
    if len(s) < 2:
        return fallback

    g = s.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    if g.empty:
        return fallback

    g = g.tail(periods)
    if method == "mean":
        val = float(g.mean())
    else:
        val = float(g.median())

    if pd.isna(val):
        val = fallback
    return _clip(val, lo, hi)


def _recent_ratio(num: pd.Series, den: pd.Series, periods: int = 3, fallback: float = 0.0) -> float:
    df = pd.concat([num, den], axis=1).dropna()
    if df.empty:
        return fallback
    r = (df.iloc[:, 0] / df.iloc[:, 1]).replace([np.inf, -np.inf], np.nan).dropna()
    return fallback if r.empty else float(r.tail(periods).mean())


def _get(wide: pd.DataFrame, code: str) -> pd.Series:
    return wide[code] if code in wide.columns else pd.Series(dtype=float)


def build_baseline_assumptions(
    wide: pd.DataFrame,
    start_year: int = FORECAST_START_YEAR,
    end_year: int = FORECAST_END_YEAR,
) -> pd.DataFrame:
    years = list(range(start_year, end_year + 1))
    a = pd.DataFrame(index=years)
    a.index.name = "Year"
    get = lambda code: _get(wide, code)

    # Real and nominal activity.
    a["RGDP_growth"] = _recent_avg_growth(get("RGDP"), fallback=0.035, lo=-0.05, hi=0.08)
    a["NGDP_growth"] = _recent_avg_growth(get("NGDP"), fallback=0.065, lo=-0.05, hi=0.12)
    a["Inflation"] = _recent_avg_growth(get("CPI_AVG"), fallback=0.045, lo=-0.05, hi=0.15)

    # National accounts expenditure components.
    a["NPC_growth"] = _recent_avg_growth(get("NPC"), fallback=0.08, lo=-0.05, hi=0.12)
    a["NGC_growth"] = _recent_avg_growth(get("NGC"), fallback=0.06, lo=-0.05, hi=0.15)
    a["NINV_growth"] = _recent_avg_growth(get("NINV"), fallback=0.08, lo=-0.10, hi=0.15)
    a["NXGS_growth"] = _recent_avg_growth(get("NXGS"), fallback=0.08, lo=-0.10, hi=0.15)
    a["NMGS_growth"] = _recent_avg_growth(get("NMGS"), fallback=0.08, lo=-0.10, hi=0.15)

    # External/BOP components. Use robust caps to prevent revision-year spikes.
    a["X_GOODS_growth"] = _recent_avg_growth(get("X_GOODS"), fallback=0.06, lo=-0.10, hi=0.10)
    a["M_GOODS_growth"] = _recent_avg_growth(get("M_GOODS"), fallback=0.06, lo=-0.10, hi=0.10)
    a["X_SERV_growth"] = _recent_avg_growth(get("X_SERV"), fallback=0.06, lo=-0.10, hi=0.10)
    a["M_SERV_growth"] = _recent_avg_growth(get("M_SERV").abs(), fallback=0.06, lo=-0.10, hi=0.10)

    a["NER_AVG_growth"] = _recent_avg_growth(get("NER_AVG"), fallback=0.03, lo=-0.10, hi=0.15)
    a["PM_growth"] = _recent_avg_growth(get("PM"), fallback=0.03, lo=-0.10, hi=0.15)
    a["PX_growth"] = _recent_avg_growth(get("PX"), fallback=0.03, lo=-0.10, hi=0.15)

    a["Primary_income_credit_growth"] = _recent_avg_growth(get("PRI_INC_CR"), fallback=0.05, lo=-0.10, hi=0.10)
    a["Primary_income_debit_growth"] = _recent_avg_growth(get("PRI_INC_DB").abs(), fallback=0.05, lo=-0.10, hi=0.10)
    a["Secondary_income_credit_growth"] = _recent_avg_growth(get("SEC_INC_CR"), fallback=0.05, lo=-0.10, hi=0.12)
    a["Secondary_income_debit_growth"] = _recent_avg_growth(get("SEC_INC_DB").abs(), fallback=0.05, lo=-0.10, hi=0.12)

    ngdp = get("NGDP")
    a["Grants_GDP_ratio"] = _recent_ratio(get("GRANTS"), ngdp, fallback=0.04)
    a["Wages_GDP_ratio"] = _recent_ratio(get("WAGES"), ngdp, fallback=0.027)
    a["GoodsServices_GDP_ratio"] = _recent_ratio(get("GDS_SERV_EXP"), ngdp, fallback=0.014)
    a["Transfers_GDP_ratio"] = _recent_ratio(get("TRANSFERS"), ngdp, fallback=0.011)
    a["Capex_GDP_ratio"] = _recent_ratio(get("CAPEX"), ngdp, fallback=0.002)
    a["OtherExp_GDP_ratio"] = _recent_ratio(get("OTHER_EXP"), ngdp, fallback=0.001)

    # Fiscal buoyancies remain explicit model parameters.
    a["Customs_buoyancy"] = 0.70
    a["VAT_buoyancy"] = 1.00
    a["IncomeTax_buoyancy"] = 1.20
    a["CIT_buoyancy"] = 1.20
    a["Nontax_buoyancy"] = 1.00
    a["Interest_effective_rate"] = 0.013
    a["Revenue_effort"] = 0.0
    a["Expenditure_pressure"] = 0.0
    a["Scenario"] = "baseline"
    return a


def get_scenario_shock(scenario: str) -> ScenarioShock:
    scenario = scenario.lower().strip()
    if scenario == "baseline":
        return ScenarioShock()
    if scenario == "optimistic":
        return ScenarioShock(0.015, 0.020, 0.0, 0.010, 0.020, 0.020, 0.010, 0.005, 0.020, -0.010)
    if scenario == "pessimistic":
        return ScenarioShock(-0.015, -0.020, 0.015, -0.010, -0.020, -0.020, -0.010, -0.005, -0.020, 0.020)
    if scenario == "custom":
        return ScenarioShock()
    raise ValueError(f"Unknown scenario: {scenario}")


def apply_scenario(baseline: pd.DataFrame, scenario: str = "baseline", custom_shock: Optional[ScenarioShock] = None) -> pd.DataFrame:
    shock = custom_shock or get_scenario_shock(scenario)
    out = baseline.copy()

    out["RGDP_growth"] += shock.real_gdp_growth_add
    out["NGDP_growth"] += shock.nominal_gdp_growth_add
    out["Inflation"] += shock.inflation_add
    out["NPC_growth"] += shock.consumption_growth_add
    out["NGC_growth"] += shock.consumption_growth_add
    out["NINV_growth"] += shock.investment_growth_add

    for c in ["NXGS_growth", "X_GOODS_growth", "X_SERV_growth"]:
        out[c] += shock.exports_growth_add
    for c in ["NMGS_growth", "M_GOODS_growth", "M_SERV_growth"]:
        out[c] += shock.imports_growth_add

    out["Grants_GDP_ratio"] += shock.grants_gdp_ratio_add
    out["Revenue_effort"] += shock.revenue_effort_add
    out["Expenditure_pressure"] += shock.expenditure_pressure_add
    out["Scenario"] = scenario.lower().strip()
    return out


def build_assumptions(
    wide: pd.DataFrame,
    scenario: str = "baseline",
    start_year: int = FORECAST_START_YEAR,
    end_year: int = FORECAST_END_YEAR,
    custom_shock: Optional[ScenarioShock] = None,
) -> pd.DataFrame:
    return apply_scenario(build_baseline_assumptions(wide, start_year, end_year), scenario, custom_shock)
