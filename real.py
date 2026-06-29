# -*- coding: utf-8 -*-
"""Real sector dashboard page."""

import streamlit as st
from config import CURRENCY_SCALE, FORECAST_START_YEAR
from main import run_model
from real_sector import real_sector_insights
from utils import kpi_cards, line_chart, policy_insight_box, fmt_money, fmt_pct


def render_real_page(results=None):
    if results is None:
        results = run_model("baseline")
    real = results["Real_Sector"]

    st.header("Real Sector Block")
    min_year, max_year = int(real.index.min()), int(real.index.max())
    start, end = st.slider("Year range", min_year, max_year, (2012 if min_year <= 2012 else min_year, max_year))

    latest = end
    kpi_cards([
        ("Nominal GDP", fmt_money(real.loc[latest, "NGDP"]), fmt_pct(real.loc[latest, "GDP_growth"]) if "GDP_growth" in real else ""),
        ("Real GDP", fmt_money(real.loc[latest, "RGDP"]), fmt_pct(real.loc[latest, "Real_GDP_growth"]) if "Real_GDP_growth" in real else ""),
        ("Consumption/GDP", fmt_pct(real.loc[latest, "Final_consumption"] / real.loc[latest, "NGDP"]), ""),
        ("Investment/GDP", fmt_pct(real.loc[latest, "NINV"] / real.loc[latest, "NGDP"]), ""),
    ])

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Diagnostics", "Forecast", "Policy Insights"])

    with tab1:
        line_chart(
            real,
            ["NGDP", "Final_consumption", "NINV"],
            "Domestic demand and GDP",
            "USD million",
            start,
            end,
            CURRENCY_SCALE,
        )
        line_chart(
            real,
            ["NXGS", "NMGS"],
            "Exports and imports of goods & services",
            "USD million",
            start,
            end,
            CURRENCY_SCALE,
        )

    with tab2:
        shares = real[["Final_consumption", "NINV", "NXGS", "NMGS"]].div(real["NGDP"], axis=0) * 100
        line_chart(
            shares,
            ["Final_consumption", "NINV", "NXGS", "NMGS"],
            "Demand components (% of GDP)",
            "% of GDP",
            start,
            end,
            1,
            value_format="percent",
        )

    with tab3:
        line_chart(real, ["NGDP", "RGDP"], "GDP forecast path", "USD million", start, end, CURRENCY_SCALE)
        st.dataframe(real.loc[start:end], use_container_width=True)

    with tab4:
        policy_insight_box("Real sector interpretation", real_sector_insights(real.loc[start:end]))
