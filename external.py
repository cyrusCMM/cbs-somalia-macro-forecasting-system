# -*- coding: utf-8 -*-
"""External sector dashboard page."""

import streamlit as st
from config import CURRENCY_SCALE
from main import run_model
from external_sector import external_sector_insights
from utils import kpi_cards, line_chart, policy_insight_box, fmt_money, fmt_pct


def render_external_page(results=None):
    if results is None:
        results = run_model("baseline")
    external = results["External_Sector"]
    real = results["Real_Sector"]

    st.header("External Sector Block")
    min_year, max_year = int(external.index.min()), int(external.index.max())
    start, end = st.slider("External year range", min_year, max_year, (max(min_year, 1990), max_year))

    latest = end
    ngdp = real.loc[latest, "NGDP"] if latest in real.index else None
    kpi_cards([
        ("Exports G&S", fmt_money(external.loc[latest, "Exports_GS"]), ""),
        ("Imports G&S", fmt_money(external.loc[latest, "Imports_GS"]), ""),
        ("Trade balance/GDP", fmt_pct(external.loc[latest, "Trade_balance"] / ngdp) if ngdp else "n/a", ""),
        ("Current account/GDP", fmt_pct(external.loc[latest, "CAB"] / ngdp) if ngdp and "CAB" in external else "n/a", ""),
    ])

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Trade", "Balances", "Policy Insights"])
    with tab1:
        line_chart(external, ["Exports_GS", "Imports_GS"], "Exports and imports", "USD million", start, end, CURRENCY_SCALE)
    with tab2:
        line_chart(external, ["X_GOODS", "M_GOODS", "X_SERV", "M_SERV"], "Goods and services trade", "USD million", start, end, CURRENCY_SCALE)
    with tab3:
        line_chart(external, ["Trade_balance", "CAB"], "External balances", "USD million", start, end, CURRENCY_SCALE)
    with tab4:
        policy_insight_box("External sector interpretation", external_sector_insights(external.loc[start:end], real))
