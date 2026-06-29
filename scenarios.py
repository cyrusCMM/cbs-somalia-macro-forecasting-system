# -*- coding: utf-8 -*-
"""Scenario analysis page."""

import streamlit as st
import pandas as pd

from assumptions import ScenarioShock
from main import run_model
from utils import line_chart
from config import CURRENCY_SCALE
from macro_output import build_key_indicators


def render_scenarios_page():
    st.header("Scenario Analysis")
    st.caption("Adjust shocks, run a custom scenario, and compare the full linked macro system against baseline.")

    c1, c2, c3 = st.columns(3)
    with c1:
        rgdp = st.slider("Real GDP growth shock", -0.05, 0.05, 0.00, 0.005)
        ngdp = st.slider("Nominal GDP growth shock", -0.05, 0.05, 0.00, 0.005)
        inflation = st.slider("Inflation shock", -0.05, 0.05, 0.00, 0.005)
    with c2:
        cons = st.slider("Consumption growth shock", -0.05, 0.05, 0.00, 0.005)
        inv = st.slider("Investment growth shock", -0.10, 0.10, 0.00, 0.005)
        exp = st.slider("Export growth shock", -0.10, 0.10, 0.00, 0.005)
    with c3:
        imp = st.slider("Import growth shock", -0.10, 0.10, 0.00, 0.005)
        rev = st.slider("Revenue effort shock", -0.05, 0.05, 0.00, 0.005)
        spend = st.slider("Expenditure pressure shock", -0.05, 0.05, 0.00, 0.005)

    if st.button("Run custom scenario"):
        shock = ScenarioShock(rgdp, ngdp, inflation, cons, inv, exp, imp, 0.0, rev, spend)
        baseline = run_model("baseline")
        custom = run_model("custom", custom_shock=shock)

        st.subheader("Scenario transmission")
        st.info("The shock is propagated through the real, external, fiscal and monetary blocks through the recursive solver.")

        real_comp = baseline["Real_Sector"][["NGDP", "Final_consumption", "NINV", "NXGS", "NMGS"]].add_prefix("Baseline_").join(
            custom["Real_Sector"][["NGDP", "Final_consumption", "NINV", "NXGS", "NMGS"]].add_prefix("Custom_")
        )

        tab1, tab2, tab3, tab4 = st.tabs(["GDP & Demand", "Fiscal", "External", "Key Indicators"])

        with tab1:
            comp = pd.DataFrame({
                "Baseline_NGDP": baseline["Real_Sector"]["NGDP"],
                "Custom_NGDP": custom["Real_Sector"]["NGDP"],
                "Baseline_imports": baseline["Real_Sector"]["NMGS"],
                "Custom_imports": custom["Real_Sector"]["NMGS"],
            })
            line_chart(comp, ["Baseline_NGDP", "Custom_NGDP"], "NGDP scenario comparison", "USD million", int(comp.index.min()), int(comp.index.max()), CURRENCY_SCALE)
            line_chart(comp, ["Baseline_imports", "Custom_imports"], "Import scenario comparison", "USD million", int(comp.index.min()), int(comp.index.max()), CURRENCY_SCALE)

        with tab2:
            fiscal_comp = pd.DataFrame({
                "Baseline_balance": baseline["Fiscal_Sector"]["FISCAL_BALANCE_GDP"],
                "Custom_balance": custom["Fiscal_Sector"]["FISCAL_BALANCE_GDP"],
                "Baseline_revenue": baseline["Fiscal_Sector"]["TOTAL_REVENUE"],
                "Custom_revenue": custom["Fiscal_Sector"]["TOTAL_REVENUE"],
            })
            line_chart(fiscal_comp, ["Baseline_balance", "Custom_balance"], "Fiscal balance scenario comparison", "Ratio", int(fiscal_comp.index.min()), int(fiscal_comp.index.max()), 1)
            line_chart(fiscal_comp, ["Baseline_revenue", "Custom_revenue"], "Revenue scenario comparison", "USD million", int(fiscal_comp.index.min()), int(fiscal_comp.index.max()), CURRENCY_SCALE)

        with tab3:
            external_comp = pd.DataFrame({
                "Baseline_CAB": baseline["External_Sector"]["CAB"],
                "Custom_CAB": custom["External_Sector"]["CAB"],
                "Baseline_exports": baseline["External_Sector"]["Exports_GS"],
                "Custom_exports": custom["External_Sector"]["Exports_GS"],
            })
            line_chart(external_comp, ["Baseline_CAB", "Custom_CAB"], "Current account scenario comparison", "USD million", int(external_comp.index.min()), int(external_comp.index.max()), CURRENCY_SCALE)
            line_chart(external_comp, ["Baseline_exports", "Custom_exports"], "Exports scenario comparison", "USD million", int(external_comp.index.min()), int(external_comp.index.max()), CURRENCY_SCALE)

        with tab4:
            st.dataframe(build_key_indicators(custom), use_container_width=True)
