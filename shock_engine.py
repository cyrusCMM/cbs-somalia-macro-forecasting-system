# -*- coding: utf-8 -*-
"""
shock_engine.py

Scenario shock bundles for the CBS Somalia macro model.

v5 update
---------
The former aggregate "domestic demand shock" has been split into separate
real-economy shocks:

- household_consumption
- private_investment
- government_consumption
- public_investment
- export_demand
- import_demand

This gives users a clearer policy simulation interface and allows shocks
to propagate through linked real, fiscal, external and monetary channels.
"""

from __future__ import annotations

from dataclasses import dataclass
from assumptions import ScenarioShock


@dataclass
class ShockBundle:
    """
    High-level economic shocks entered by the user.

    Values are decimal percentage-point shocks.
    Example: 0.02 = +2 percentage points.
    """
    household_consumption: float = 0.0
    private_investment: float = 0.0
    government_consumption: float = 0.0
    public_investment: float = 0.0
    export_demand: float = 0.0
    import_demand: float = 0.0

    external_price: float = 0.0
    grants: float = 0.0
    revenue_reform: float = 0.0
    financial_deepening: float = 0.0
    expenditure_pressure: float = 0.0


def build_scenario_shock(bundle: ShockBundle) -> ScenarioShock:
    """
    Convert high-level economic shocks into model assumption shocks.

    Transmission logic
    ------------------
    Household consumption shock:
        Directly raises private consumption, imports, domestic tax bases,
        money demand and nominal GDP.

    Private investment shock:
        Raises investment, imports, credit demand and productive capacity.

    Government consumption shock:
        Raises public consumption, nominal activity and expenditure pressure.

    Public investment shock:
        Raises investment and capital expenditure pressure, with moderate
        growth effects.

    Export demand shock:
        Raises exports, GDP and current-account receipts.

    Import demand shock:
        Raises imports directly and affects customs/VAT bases, but worsens
        trade balance.

    External price shock:
        Raises inflation, nominal import values and nominal GDP, but slightly
        weakens real activity.

    Revenue reform shock:
        Raises tax effort across revenue heads.

    Financial deepening shock:
        Supports investment, deposits, broad money and credit channels.
    """

    # Real activity channel
    real_gdp_growth_add = (
        0.15 * bundle.household_consumption
        + 0.25 * bundle.private_investment
        + 0.10 * bundle.government_consumption
        + 0.20 * bundle.public_investment
        + 0.20 * bundle.export_demand
        - 0.05 * bundle.import_demand
        - 0.15 * bundle.external_price
        + 0.20 * bundle.financial_deepening
    )

    # Nominal activity channel
    nominal_gdp_growth_add = (
        0.25 * bundle.household_consumption
        + 0.25 * bundle.private_investment
        + 0.15 * bundle.government_consumption
        + 0.20 * bundle.public_investment
        + 0.15 * bundle.export_demand
        + 0.05 * bundle.import_demand
        + 0.35 * bundle.external_price
        + 0.15 * bundle.financial_deepening
    )

    # Inflation channel
    inflation_add = (
        0.05 * bundle.household_consumption
        + 0.05 * bundle.government_consumption
        + 0.60 * bundle.external_price
    )

    # Demand components
    consumption_growth_add = (
        0.85 * bundle.household_consumption
        + 0.25 * bundle.government_consumption
        - 0.10 * bundle.external_price
    )

    investment_growth_add = (
        0.85 * bundle.private_investment
        + 0.55 * bundle.public_investment
        + 0.40 * bundle.financial_deepening
        - 0.10 * bundle.external_price
    )

    exports_growth_add = (
        0.90 * bundle.export_demand
        - 0.10 * bundle.external_price
    )

    imports_growth_add = (
        0.45 * bundle.household_consumption
        + 0.55 * bundle.private_investment
        + 0.25 * bundle.government_consumption
        + 0.40 * bundle.public_investment
        + 0.90 * bundle.import_demand
        + 0.55 * bundle.external_price
        + 0.20 * bundle.financial_deepening
    )

    # Expenditure pressure combines explicit pressure plus public demand.
    expenditure_pressure_add = (
        bundle.expenditure_pressure
        + 0.35 * bundle.government_consumption
        + 0.25 * bundle.public_investment
    )

    return ScenarioShock(
        real_gdp_growth_add=real_gdp_growth_add,
        nominal_gdp_growth_add=nominal_gdp_growth_add,
        inflation_add=inflation_add,
        consumption_growth_add=consumption_growth_add,
        investment_growth_add=investment_growth_add,
        exports_growth_add=exports_growth_add,
        imports_growth_add=imports_growth_add,
        grants_gdp_ratio_add=bundle.grants,
        revenue_effort_add=bundle.revenue_reform,
        expenditure_pressure_add=expenditure_pressure_add,
    )


def describe_bundle(bundle: ShockBundle) -> list[str]:
    """Return plain-language explanation of selected shocks."""
    lines = []

    if bundle.household_consumption:
        lines.append("Household consumption shock affects private consumption, imports, domestic tax bases and nominal activity.")
    if bundle.private_investment:
        lines.append("Private investment shock affects investment, imports, credit demand and medium-term growth.")
    if bundle.government_consumption:
        lines.append("Government consumption shock affects public demand, recurrent expenditure, GDP and fiscal balance.")
    if bundle.public_investment:
        lines.append("Public investment shock affects capital expenditure, investment, imports, growth and debt dynamics.")
    if bundle.export_demand:
        lines.append("Export demand shock affects exports, GDP, trade balance and the current account.")
    if bundle.import_demand:
        lines.append("Import demand shock affects imports, customs/VAT bases and the trade balance.")
    if bundle.external_price:
        lines.append("External price shock affects inflation, import values, nominal GDP and the current account.")
    if bundle.grants:
        lines.append("Grant shock affects fiscal resources, fiscal balance and debt dynamics.")
    if bundle.revenue_reform:
        lines.append("Revenue reform shock affects customs, sales taxes, income taxes and domestic revenue.")
    if bundle.financial_deepening:
        lines.append("Financial deepening shock affects investment, nominal activity, deposits, M2 and credit.")
    if bundle.expenditure_pressure:
        lines.append("Expenditure pressure shock affects spending, fiscal balance and debt.")

    if not lines:
        lines.append("No additional shock selected; results are equivalent to the neutral custom case.")

    return lines
