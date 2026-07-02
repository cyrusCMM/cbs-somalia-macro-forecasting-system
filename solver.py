# -*- coding: utf-8 -*-
"""
solver.py

Recursive macro-consistency solver for the CBS Somalia macro model.
"""

from __future__ import annotations

import pandas as pd

from assumptions import build_assumptions, ScenarioShock
from real_sector import forecast_real_sector
from external_sector import forecast_external_sector
from fiscal_sector import forecast_fiscal_sector
from monetary_sector import forecast_monetary_sector
from reconciliation import build_gdp_reconciliation, build_nominal_gdp_output
from config import FORECAST_START_YEAR, FORECAST_END_YEAR


def _recompute_real_identities(real: pd.DataFrame) -> pd.DataFrame:
    """Recompute core expenditure identities after block links are updated."""
    real = real.copy()
    real["Final_consumption"] = real["NPC"] + real["NGC"]
    real["Absorption"] = real["Final_consumption"] + real["NINV"]
    real["Expenditure_GDP_before_SD"] = real["Final_consumption"] + real["NINV"] + real["NXGS"] - real["NMGS"]
    real["Statistical_discrepancy"] = real["NGDP"] - real["Expenditure_GDP_before_SD"]
    real["Statistical_discrepancy_pct_GDP"] = real["Statistical_discrepancy"] / real["NGDP"]
    real["GDP_growth"] = real["NGDP"].pct_change()
    real["Real_GDP_growth"] = real["RGDP"].pct_change()
    return real


def _link_external_to_real(real: pd.DataFrame, external: pd.DataFrame, forecast_years) -> pd.DataFrame:
    """
    In forecast years, use the external-sector trade forecast as the source
    for exports/imports of goods and services in the expenditure identity.
    """
    real = real.copy()
    for year in forecast_years:
        if year in real.index and year in external.index:
            if "Exports_GS" in external.columns:
                real.loc[year, "NXGS"] = external.loc[year, "Exports_GS"]
            if "Imports_GS" in external.columns:
                real.loc[year, "NMGS"] = external.loc[year, "Imports_GS"]
    return _recompute_real_identities(real)


def solve_macro_model(
    wide: pd.DataFrame,
    scenario: str = "baseline",
    custom_shock: ScenarioShock | None = None,
    max_iter: int = 2,
    start_year: int = FORECAST_START_YEAR,
    end_year: int = FORECAST_END_YEAR,
) -> dict:
    """
    Solve the integrated macro model.

    v6: start_year and end_year are now passed in by main.py, allowing
    automatic forecast start after the latest actual year.
    """
    assumptions = build_assumptions(
        wide,
        scenario=scenario,
        custom_shock=custom_shock,
        start_year=start_year,
        end_year=end_year,
    )
    forecast_years = list(assumptions.index)

    real = forecast_real_sector(wide, assumptions)
    external = forecast_external_sector(wide, assumptions)
    # Keep national-accounts NXGS/NMGS in the real-sector GDP identity.
    # The external block can differ from national accounts because BOP trade and
    # expenditure-side trade are not always the same source series.
    # Do not overwrite real-sector trade with BOP trade here.

    for _ in range(max_iter):
        fiscal = forecast_fiscal_sector(wide, assumptions, real, external)
        monetary = forecast_monetary_sector(wide, real, assumptions)
        real = _recompute_real_identities(real)

    gdp_reconciliation = build_gdp_reconciliation(real)
    nominal_output = build_nominal_gdp_output(real, external)

    return {
        "Assumptions": assumptions,
        "Real_Sector": real,
        "External_Sector": external,
        "Fiscal_Sector": fiscal,
        "Monetary_Sector": monetary,
        "GDP_Reconciliation": gdp_reconciliation,
        "Nominal_GDP_Output": nominal_output,
    }
