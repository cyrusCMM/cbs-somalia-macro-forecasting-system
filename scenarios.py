# -*- coding: utf-8 -*-
"""Scenario analysis page with component-level simultaneous macro shocks."""

import streamlit as st
import pandas as pd

from main import run_model
from shock_engine import ShockBundle, build_scenario_shock, describe_bundle
from utils import line_chart
from config import CURRENCY_SCALE
from macro_output import build_key_indicators


def render_scenarios_page():
    st.header("Scenario Analysis")
    st.caption("Apply simultaneous component-level macro shocks and trace the impact across real, external, fiscal and monetary blocks.")

    st.subheader("Real economy demand shocks")
    st.write("The former aggregate demand shock has been split into separate components for clearer policy simulation.")

    c1, c2, c3 = st.columns(3)

    with c1:
        household_consumption = st.slider(
            "Household consumption shock",
            -0.08, 0.08, 0.00, 0.005,
            help="Affects private consumption, imports, sales tax/VAT base and nominal activity."
        )
        private_investment = st.slider(
            "Private investment shock",
            -0.10, 0.10, 0.00, 0.005,
            help="Affects investment, imports, credit demand and productive capacity."
        )
        government_consumption = st.slider(
            "Government consumption shock",
            -0.08, 0.08, 0.00, 0.005,
            help="Affects public consumption, recurrent expenditure, GDP and fiscal balance."
        )

    with c2:
        public_investment = st.slider(
            "Public investment shock",
            -0.10, 0.10, 0.00, 0.005,
            help="Affects capital expenditure, investment, imports, GDP and debt."
        )
        export_demand = st.slider(
            "Export demand shock",
            -0.10, 0.10, 0.00, 0.005,
            help="Affects exports, GDP, trade balance and current account."
        )
        import_demand = st.slider(
            "Import demand shock",
            -0.10, 0.10, 0.00, 0.005,
            help="Affects imports, customs/VAT bases and the trade balance."
        )

    with c3:
        external_price = st.slider(
            "External price shock",
            -0.08, 0.08, 0.00, 0.005,
            help="Affects inflation, import values, nominal GDP and current account."
        )
        financial_deepening = st.slider(
            "Financial deepening shock",
            -0.06, 0.06, 0.00, 0.005,
            help="Affects investment, deposits, broad money and private credit."
        )

    st.subheader("Fiscal and financing shocks")
    f1, f2, f3 = st.columns(3)

    with f1:
        grants = st.slider(
            "Grants shock (% of GDP)",
            -0.04, 0.04, 0.00, 0.0025,
            help="Direct change in grants-to-GDP ratio."
        )
    with f2:
        revenue_reform = st.slider(
            "Revenue reform effort",
            -0.05, 0.05, 0.00, 0.005,
            help="Affects revenue effort across customs, sales taxes, income tax and CIT."
        )
    with f3:
        expenditure_pressure = st.slider(
            "Other expenditure pressure",
            -0.05, 0.05, 0.00, 0.005,
            help="Additional expenditure pressure beyond public consumption and public investment shocks."
        )

    bundle = ShockBundle(
        household_consumption=household_consumption,
        private_investment=private_investment,
        government_consumption=government_consumption,
        public_investment=public_investment,
        export_demand=export_demand,
        import_demand=import_demand,
        external_price=external_price,
        grants=grants,
        revenue_reform=revenue_reform,
        financial_deepening=financial_deepening,
        expenditure_pressure=expenditure_pressure,
    )

    with st.expander("Transmission explanation", expanded=True):
        for line in describe_bundle(bundle):
            st.markdown(f"- {line}")

    if st.button("Run component shock scenario"):
        shock = build_scenario_shock(bundle)

        baseline = run_model("baseline")
        custom = run_model("custom", custom_shock=shock)

        st.success("Scenario solved. Component shocks have been transmitted across the linked macro blocks.")

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Real transmission",
            "Fiscal transmission",
            "External transmission",
            "Monetary transmission",
            "Key indicators",
        ])

        with tab1:
            real_comp = pd.DataFrame({
                "Baseline_NGDP": baseline["Real_Sector"]["NGDP"],
                "Custom_NGDP": custom["Real_Sector"]["NGDP"],
                "Baseline_consumption": baseline["Real_Sector"]["Final_consumption"],
                "Custom_consumption": custom["Real_Sector"]["Final_consumption"],
                "Baseline_investment": baseline["Real_Sector"]["NINV"],
                "Custom_investment": custom["Real_Sector"]["NINV"],
                "Baseline_imports": baseline["Real_Sector"]["NMGS"],
                "Custom_imports": custom["Real_Sector"]["NMGS"],
            })
            line_chart(real_comp, ["Baseline_NGDP", "Custom_NGDP"], "NGDP: baseline vs scenario", "USD million", 2024, 2035, CURRENCY_SCALE)
            line_chart(real_comp, ["Baseline_consumption", "Custom_consumption", "Baseline_investment", "Custom_investment"], "Consumption and investment transmission", "USD million", 2024, 2035, CURRENCY_SCALE)
            line_chart(real_comp, ["Baseline_imports", "Custom_imports"], "Import leakage from demand shocks", "USD million", 2024, 2035, CURRENCY_SCALE)

        with tab2:
            fiscal_comp = pd.DataFrame({
                "Baseline_revenue": baseline["Fiscal_Sector"]["TOTAL_REVENUE"],
                "Custom_revenue": custom["Fiscal_Sector"]["TOTAL_REVENUE"],
                "Baseline_expenditure": baseline["Fiscal_Sector"]["TOTAL_EXPENDITURE"],
                "Custom_expenditure": custom["Fiscal_Sector"]["TOTAL_EXPENDITURE"],
                "Baseline_balance": baseline["Fiscal_Sector"]["FISCAL_BALANCE_GDP"],
                "Custom_balance": custom["Fiscal_Sector"]["FISCAL_BALANCE_GDP"],
                "Baseline_debt": baseline["Fiscal_Sector"]["DEBT_GDP"],
                "Custom_debt": custom["Fiscal_Sector"]["DEBT_GDP"],
            })
            line_chart(fiscal_comp, ["Baseline_revenue", "Custom_revenue", "Baseline_expenditure", "Custom_expenditure"], "Fiscal revenue and expenditure transmission", "USD million", 2025, 2035, CURRENCY_SCALE)
            line_chart(fiscal_comp, ["Baseline_balance", "Custom_balance", "Baseline_debt", "Custom_debt"], "Fiscal balance and debt transmission", "Ratio", 2025, 2035, 1)

        with tab3:
            external_comp = pd.DataFrame({
                "Baseline_exports": baseline["External_Sector"]["Exports_GS"],
                "Custom_exports": custom["External_Sector"]["Exports_GS"],
                "Baseline_imports": baseline["External_Sector"]["Imports_GS"],
                "Custom_imports": custom["External_Sector"]["Imports_GS"],
                "Baseline_CAB": baseline["External_Sector"]["CAB"],
                "Custom_CAB": custom["External_Sector"]["CAB"],
            })
            line_chart(external_comp, ["Baseline_exports", "Custom_exports", "Baseline_imports", "Custom_imports"], "Trade transmission", "USD million", 2024, 2035, CURRENCY_SCALE)
            line_chart(external_comp, ["Baseline_CAB", "Custom_CAB"], "Current account transmission", "USD million", 2024, 2035, CURRENCY_SCALE)

        with tab4:
            monetary_comp = pd.DataFrame({
                "Baseline_M2": baseline["Monetary_Sector"]["M2"],
                "Custom_M2": custom["Monetary_Sector"]["M2"],
                "Baseline_PSC": baseline["Monetary_Sector"]["PSC"],
                "Custom_PSC": custom["Monetary_Sector"]["PSC"],
                "Baseline_M2_GDP": baseline["Monetary_Sector"]["M2_GDP"],
                "Custom_M2_GDP": custom["Monetary_Sector"]["M2_GDP"],
            })
            line_chart(monetary_comp, ["Baseline_M2", "Custom_M2", "Baseline_PSC", "Custom_PSC"], "Monetary transmission", "USD million", 2025, 2035, CURRENCY_SCALE)
            line_chart(monetary_comp, ["Baseline_M2_GDP", "Custom_M2_GDP"], "Financial deepening transmission", "Ratio", 2025, 2035, 1)

        with tab5:
            st.subheader("Scenario key indicators")
            st.dataframe(build_key_indicators(custom), use_container_width=True)
            st.download_button(
                "Download scenario key indicators",
                build_key_indicators(custom).to_csv(index=False).encode("utf-8"),
                "scenario_key_indicators.csv",
                "text/csv",
            )
