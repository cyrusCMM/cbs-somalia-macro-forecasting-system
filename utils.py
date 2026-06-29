# -*- coding: utf-8 -*-
"""
utils.py
Shared helper functions for the CBS Somalia Macro Forecasting System.
"""

from __future__ import annotations

from typing import Iterable, Optional
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from config import CURRENCY_SCALE, CURRENCY_LABEL, FORECAST_START_YEAR


LABELS = {
    "NGDP": "Nominal GDP",
    "RGDP": "Real GDP",
    "Final_consumption": "Final consumption",
    "NINV": "Investment",
    "NXGS": "Exports of goods & services",
    "NMGS": "Imports of goods & services",
    "GDP_growth": "Nominal GDP growth",
    "Real_GDP_growth": "Real GDP growth",
    "IMP_DUTY": "Customs duties",
    "DOM_SALES": "Sales tax / VAT",
    "PIT": "Income tax",
    "CIT": "Corporate income tax",
    "NONTAX": "Non-tax revenue",
    "GRANTS": "Grants",
    "TOTAL_REVENUE": "Total revenue & grants",
    "TOTAL_EXPENDITURE": "Total expenditure",
    "FISCAL_BALANCE": "Fiscal balance",
    "DEBT_GDP": "Debt / GDP",
    "WAGES": "Wages",
    "GDS_SERV_EXP": "Goods & services",
    "TRANSFERS": "Transfers",
    "CAPEX": "Capital expenditure",
    "OTHER_EXP": "Other expenditure",
    "INT_PAY": "Interest payments",
    "X_GOODS": "Goods exports",
    "M_GOODS": "Goods imports",
    "X_SERV": "Service exports",
    "M_SERV": "Service imports",
    "Exports_GS": "Exports of goods & services",
    "Imports_GS": "Imports of goods & services",
    "Trade_balance": "Trade balance",
    "CAB": "Current account balance",
    "M2": "Broad money (M2)",
    "TOT_DEP": "Total deposits",
    "PSC": "Private sector credit",
    "M2_GDP": "M2 / GDP",
    "PSC_GDP": "Private credit / GDP",
    "Statistical_discrepancy_pct_GDP": "Statistical discrepancy / GDP",
    "Baseline_NGDP": "Baseline NGDP",
    "Custom_NGDP": "Custom NGDP",
    "Baseline_balance": "Baseline fiscal balance",
    "Custom_balance": "Custom fiscal balance",
}


def pretty_label(name: str) -> str:
    return LABELS.get(str(name), str(name).replace("_", " ").title())


def fmt_money(value, scale=CURRENCY_SCALE, suffix=CURRENCY_LABEL):
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value/scale:,.1f} {suffix}"


def fmt_pct(value, decimals=1):
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value*100:.{decimals}f}%"


def kpi_cards(items, columns=4):
    cols = st.columns(columns)
    for i, item in enumerate(items):
        label, value, delta = item
        with cols[i % columns]:
            st.metric(label, value, delta)


def year_filter(df: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    out = df.copy()
    out.index = out.index.astype(int)
    return out.loc[(out.index >= start_year) & (out.index <= end_year)]


def _shade_forecast(ax, years):
    years = [int(y) for y in years]
    if not years or max(years) < FORECAST_START_YEAR:
        return
    ax.axvspan(FORECAST_START_YEAR - 0.5, max(years) + 0.5, alpha=0.08, color="tab:blue")
    ax.axvline(FORECAST_START_YEAR - 0.5, linestyle="--", linewidth=1, alpha=0.75, color="tab:blue")
    ymin, ymax = ax.get_ylim()
    ax.text(FORECAST_START_YEAR, ymax, "Forecast", va="top", ha="left", fontsize=9, alpha=0.8)


def _format_value(v, value_format: str):
    if pd.isna(v):
        return ""
    if value_format == "percent":
        return f"{v:.1f}%"
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    if abs(v) >= 100:
        return f"{v:,.0f}"
    return f"{v:,.1f}"


def _label_last_points(ax, data: pd.DataFrame, value_format: str = "number"):
    for col in data.columns:
        s = data[col].dropna()
        if s.empty:
            continue
        ax.annotate(
            _format_value(s.iloc[-1], value_format),
            xy=(s.index[-1], s.iloc[-1]),
            xytext=(7, 0),
            textcoords="offset points",
            fontsize=8,
            va="center",
        )


def line_chart(
    df: pd.DataFrame,
    columns: list[str],
    title: str,
    y_label: str = "",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    scale: float = 1.0,
    value_format: str = "number",
    label_last: bool = True,
):
    cols = [c for c in columns if c in df.columns]
    data = df[cols].copy()
    if start_year is not None and end_year is not None:
        data = year_filter(data, start_year, end_year)
    data = data / scale
    data = data.rename(columns={c: pretty_label(c) for c in data.columns})

    fig, ax = plt.subplots(figsize=(11, 5.2))
    for col in data.columns:
        ax.plot(data.index.astype(int), data[col], marker="o", linewidth=2.2, label=col)

    ax.set_title(title, fontsize=16, weight="bold", pad=10)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel(y_label, fontsize=11)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", frameon=True)
    _shade_forecast(ax, data.index)

    if label_last:
        _label_last_points(ax, data, value_format)

    fig.tight_layout()
    st.pyplot(fig)


def stacked_bar_chart(
    df: pd.DataFrame,
    columns: list[str],
    title: str,
    y_label: str = "",
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    scale: float = 1.0,
    label_totals: bool = True,
    label_segments: bool = True,
):
    cols = [c for c in columns if c in df.columns]
    data = df[cols].copy()
    if start_year is not None and end_year is not None:
        data = year_filter(data, start_year, end_year)
    data = data / scale
    data = data.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    data = data.rename(columns={c: pretty_label(c) for c in data.columns})

    years = [int(y) for y in data.index]
    x = np.arange(len(years))
    fig, ax = plt.subplots(figsize=(11, 5.2))
    bottom = np.zeros(len(data), dtype=float)

    max_total = max(float(data.sum(axis=1).max()), 1.0)
    for col in data.columns:
        vals = data[col].values.astype(float)
        bars = ax.bar(x, vals, bottom=bottom, label=col, width=0.72)

        if label_segments:
            for bar, val, bot in zip(bars, vals, bottom):
                if abs(val) >= max_total * 0.055:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bot + val / 2,
                        _format_value(val, "number"),
                        ha="center",
                        va="center",
                        fontsize=8,
                        color="white",
                        weight="bold",
                    )
        bottom += vals

    if label_totals:
        totals = data.sum(axis=1).values.astype(float)
        y_offset = max_total * 0.015
        for xi, total in zip(x, totals):
            ax.text(xi, total + y_offset, _format_value(total, "number"), ha="center", va="bottom", fontsize=9, weight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years])
    ax.set_xlim(-0.6, len(years) - 0.4)
    ax.set_title(title, fontsize=16, weight="bold", pad=10)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel(y_label, fontsize=11)
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(loc="best", frameon=True)
    # For categorical x-axis, shade forecast if all years are forecasts.
    fig.tight_layout()
    st.pyplot(fig)


def percent_share_chart(
    df: pd.DataFrame,
    columns: list[str],
    title: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
):
    cols = [c for c in columns if c in df.columns]
    data = df[cols].copy()
    if start_year is not None and end_year is not None:
        data = year_filter(data, start_year, end_year)
    data = data.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    share = data.div(data.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0) * 100
    share = share.rename(columns={c: pretty_label(c) for c in share.columns})

    years = [int(y) for y in share.index]
    x = np.arange(len(years))
    fig, ax = plt.subplots(figsize=(11, 5.2))
    bottom = np.zeros(len(share), dtype=float)

    for col in share.columns:
        vals = share[col].values.astype(float)
        bars = ax.bar(x, vals, bottom=bottom, label=col, width=0.72)
        for bar, val, bot in zip(bars, vals, bottom):
            if val >= 6:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bot + val / 2,
                    f"{val:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white",
                    weight="bold",
                )
        bottom += vals

    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years])
    ax.set_xlim(-0.6, len(years) - 0.4)
    ax.set_ylim(0, 100)
    ax.set_title(title, fontsize=16, weight="bold", pad=10)
    ax.set_xlabel("Year")
    ax.set_ylabel("Percent of total")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(loc="best", frameon=True)
    fig.tight_layout()
    st.pyplot(fig)


def display_table(df: pd.DataFrame, scale: Optional[float] = None, pct_cols: Optional[Iterable[str]] = None):
    out = df.copy()
    if scale:
        num_cols = out.select_dtypes(include=[np.number]).columns
        out[num_cols] = out[num_cols] / scale
    st.dataframe(out, use_container_width=True)


def policy_insight_box(title: str, bullets: list[str]):
    st.markdown(f"### {title}")
    for b in bullets:
        st.markdown(f"- {b}")
