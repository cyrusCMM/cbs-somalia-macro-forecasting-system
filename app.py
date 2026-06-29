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
from data import render_data_page
from real import render_real_page
from fiscal import render_fiscal_page
from external import render_external_page
from monetary import render_monetary_page
from framework import render_framework_page
from scenarios import render_scenarios_page
from reports import render_reports_page

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

if "results" not in st.session_state or run_button:
    st.session_state["results"] = run_model(scenario)

results = st.session_state["results"]

if page == "Home Dashboard":
    real = results["Real_Sector"]
    fiscal = results["Fiscal_Sector"]
    external = results["External_Sector"]
    monetary = results["Monetary_Sector"]

    latest = int(real.index.max())
    fiscal_latest = int(fiscal.index.max())
    cab_ratio = external.loc[latest, "CAB"] / real.loc[latest, "NGDP"] if latest in external.index and "CAB" in external else None

    st.header("Executive Dashboard")
    kpi_cards([
        ("Nominal GDP", fmt_money(real.loc[latest, "NGDP"]), ""),
        ("Real GDP growth", fmt_pct(real.loc[latest, "Real_GDP_growth"]), ""),
        ("Fiscal balance/GDP", fmt_pct(fiscal.loc[fiscal_latest, "FISCAL_BALANCE_GDP"]), ""),
        ("Current account/GDP", fmt_pct(cab_ratio), ""),
        ("Debt/GDP", fmt_pct(fiscal.loc[fiscal_latest, "DEBT_GDP"]), ""),
        ("M2/GDP", fmt_pct(monetary.loc[fiscal_latest, "M2_GDP"]) if fiscal_latest in monetary.index else "n/a", ""),
    ], columns=3)

    c1, c2 = st.columns(2)
    with c1:
        line_chart(real, ["NGDP", "Final_consumption", "NINV"], "GDP and domestic demand", "USD million", 2018, latest, CURRENCY_SCALE)
    with c2:
        line_chart(external, ["Exports_GS", "Imports_GS", "CAB"], "External sector", "USD million", 2018, latest, CURRENCY_SCALE)

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
    render_scenarios_page()
elif page == "Reports":
    render_reports_page(results)
