# -*- coding: utf-8 -*-
"""Fiscal sector dashboard page."""

import streamlit as st
from config import CURRENCY_SCALE
from main import run_model
from fiscal_sector import fiscal_sector_insights
from utils import kpi_cards, line_chart, stacked_bar_chart, percent_share_chart, policy_insight_box, fmt_money, fmt_pct


def render_fiscal_page(results=None):
    if results is None:
        results = run_model("baseline")
    fiscal = results["Fiscal_Sector"]

    st.header("Fiscal Sector Block")
    min_year, max_year = int(fiscal.index.min()), int(fiscal.index.max())
    start, end = st.slider("Fiscal year range", min_year, max_year, (min_year, max_year))

    latest = end
    kpi_cards([
        ("Total revenue", fmt_money(fiscal.loc[latest, "TOTAL_REVENUE"]), ""),
        ("Total expenditure", fmt_money(fiscal.loc[latest, "TOTAL_EXPENDITURE"]), ""),
        ("Fiscal balance/GDP", fmt_pct(fiscal.loc[latest, "FISCAL_BALANCE_GDP"]), ""),
        ("Debt/GDP", fmt_pct(fiscal.loc[latest, "DEBT_GDP"]), ""),
    ])

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Revenue", "Expenditure & Debt", "Policy Insights"])

    with tab1:
        line_chart(
            fiscal,
            ["TOTAL_REVENUE", "TOTAL_EXPENDITURE", "FISCAL_BALANCE"],
            "Fiscal outlook",
            "USD million",
            start,
            end,
            CURRENCY_SCALE,
        )

    with tab2:
        stacked_bar_chart(
            fiscal,
            ["IMP_DUTY", "DOM_SALES", "PIT", "CIT", "NONTAX", "GRANTS"],
            "Revenue and grants composition",
            "USD million",
            start,
            end,
            CURRENCY_SCALE,
            label_totals=True,
            label_segments=True,
        )
        percent_share_chart(
            fiscal,
            ["IMP_DUTY", "DOM_SALES", "PIT", "CIT", "NONTAX", "GRANTS"],
            "Revenue and grants composition (% of total resources)",
            start,
            end,
        )

    with tab3:
        stacked_bar_chart(
            fiscal,
            ["WAGES", "GDS_SERV_EXP", "TRANSFERS", "CAPEX", "OTHER_EXP", "INT_PAY"],
            "Expenditure composition",
            "USD million",
            start,
            end,
            CURRENCY_SCALE,
            label_totals=True,
            label_segments=True,
        )
        line_chart(fiscal, ["DEBT_GDP"], "Debt-to-GDP", "Ratio", start, end, 1)

    with tab4:
        policy_insight_box("Fiscal interpretation", fiscal_sector_insights(fiscal.loc[start:end]))
