# -*- coding: utf-8 -*-
"""
app.py
CBS Somalia Macroeconomic Forecasting System.
Run:
    streamlit run app.py
"""

import streamlit as st

from config import APP_TITLE, CURRENCY_SCALE
from main import run_model
from utils import kpi_cards, fmt_money, fmt_pct, line_chart
from data import render_data_page, get_active_uploaded_files
from real import render_real_page
from fiscal import render_fiscal_page
from external import render_external_page
from monetary import render_monetary_page
from framework import render_framework_page
from scenarios import render_scenarios_page
from reports import render_reports_page
from model_validation import has_critical_errors, safe_indicator_value

st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)

with st.sidebar:
    st.subheader("Navigation")
    page = st.radio(
        "Go to",
        [
            "Home Dashboard",
            "Data Management",
            "Real Sector",
            "Fiscal Sector",
            "External Sector",
            "Monetary Sector",
            "Macro Framework",
            "Scenario Analysis",
            "Reports",
        ],
    )
    scenario = st.selectbox("Scenario", ["baseline", "optimistic", "pessimistic"])
    run_button = st.button("Run selected scenario")

    active_source = "Uploaded session data" if st.session_state.get("uploaded_files") else "Default app data"
    st.caption(f"Active source: {active_source}")

uploaded_files = get_active_uploaded_files()
active_source_key = "uploaded" if uploaded_files else "default"

if (
    "results" not in st.session_state
    or run_button
    or st.session_state.get("results_source_key") != active_source_key
    or st.session_state.get("results_scenario") != scenario
):
    st.session_state["results"] = run_model(scenario, uploaded_files=uploaded_files)
    st.session_state["results_source_key"] = active_source_key
    st.session_state["results_scenario"] = scenario

results = st.session_state["results"]

validation = results.get("Model_Validation")
validation_failed = has_critical_errors(validation)

if validation_failed:
    st.error("Model validation has critical errors. Review the validation diagnostics before using dashboard results.")
    with st.expander("Show validation diagnostics", expanded=True):
        st.dataframe(validation, use_container_width=True)
else:
    st.success("Model validation passed. No critical consistency errors detected.")

if page == "Home Dashboard":
    real = results["Real_Sector"]
    external = results["External_Sector"]
    latest = int(real.index.max())
    indicators = results.get("Executive_Indicators")

    st.header("Executive Dashboard")
    st.caption(
        f"Latest actual year: {results.get('Latest_Actual_Year')}; "
        f"forecast starts: {results.get('Forecast_Start_Year')}; "
        f"source: {results.get('Source_Mode')}"
    )

    # Do not display invalid ratios. If a ratio fails, display CHECK instead.
    nominal_gdp = safe_indicator_value(indicators, validation, "Nominal GDP")
    real_growth = safe_indicator_value(indicators, validation, "Real GDP growth")
    fiscal_balance = safe_indicator_value(indicators, validation, "Fiscal balance/GDP")
    cab_gdp = safe_indicator_value(indicators, validation, "Current account/GDP")
    debt_gdp = safe_indicator_value(indicators, validation, "Debt/GDP")
    m2_gdp = safe_indicator_value(indicators, validation, "M2/GDP")

    kpi_cards([
        ("Nominal GDP", fmt_money(nominal_gdp) if nominal_gdp is not None else "CHECK", ""),
        ("Real GDP growth", fmt_pct(real_growth) if real_growth is not None else "CHECK", ""),
        ("Fiscal balance/GDP", fmt_pct(fiscal_balance) if fiscal_balance is not None else "CHECK", ""),
        ("Current account/GDP", fmt_pct(cab_gdp) if cab_gdp is not None else "CHECK", ""),
        ("Debt/GDP", fmt_pct(debt_gdp) if debt_gdp is not None else "CHECK", ""),
        ("M2/GDP", fmt_pct(m2_gdp) if m2_gdp is not None else "CHECK", ""),
    ], columns=3)

    c1, c2 = st.columns(2)
    with c1:
        line_chart(real, ["NGDP", "Final_consumption", "NINV"], "GDP and domestic demand", "USD million", 2018, latest, CURRENCY_SCALE)
    with c2:
        line_chart(external, ["Exports_GS", "Imports_GS", "CAB"], "External sector", "USD million", 2018, latest, CURRENCY_SCALE)

    st.subheader("Executive indicators")
    st.dataframe(indicators, use_container_width=True)

elif page == "Data Management":
    render_data_page()
elif page == "Real Sector":
    render_real_page(results)
elif page == "Fiscal Sector":
    render_fiscal_page(results)
elif page == "External Sector":
    render_external_page(results)
elif page == "Monetary Sector":
    render_monetary_page(results)
elif page == "Macro Framework":
    render_framework_page(results)
elif page == "Scenario Analysis":
    render_scenarios_page(uploaded_files=uploaded_files)
elif page == "Reports":
    render_reports_page(results)
