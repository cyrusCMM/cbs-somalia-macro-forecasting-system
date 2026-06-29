# -*- coding: utf-8 -*-
"""Monetary sector dashboard page."""

import streamlit as st
from config import CURRENCY_SCALE
from main import run_model
from monetary_sector import monetary_sector_insights
from utils import kpi_cards, line_chart, policy_insight_box, fmt_money, fmt_pct


def render_monetary_page(results=None):
    if results is None:
        results = run_model("baseline")
    monetary = results["Monetary_Sector"]

    st.header("Monetary Sector Block")
    min_year, max_year = int(monetary.index.min()), int(monetary.index.max())
    start, end = st.slider("Monetary year range", min_year, max_year, (min_year, max_year))

    latest = end
    kpi_cards([
        ("Broad money M2", fmt_money(monetary.loc[latest, "M2"]), ""),
        ("Deposits", fmt_money(monetary.loc[latest, "TOT_DEP"]), ""),
        ("Private sector credit", fmt_money(monetary.loc[latest, "PSC"]), ""),
        ("Credit/GDP", fmt_pct(monetary.loc[latest, "PSC_GDP"]), ""),
    ])

    tab1, tab2, tab3 = st.tabs(["Overview", "Financial Deepening", "Policy Insights"])
    with tab1:
        line_chart(monetary, ["M2", "TOT_DEP", "PSC"], "Monetary aggregates", "USD million", start, end, CURRENCY_SCALE)
    with tab2:
        line_chart(monetary, ["M2_GDP", "PSC_GDP"], "Financial deepening ratios", "Ratio", start, end, 1)
    with tab3:
        policy_insight_box("Monetary interpretation", monetary_sector_insights(monetary.loc[start:end]))
