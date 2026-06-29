# -*- coding: utf-8 -*-
"""Reports and exports page."""

import streamlit as st
from main import run_model
from outputs import export_outputs, make_dashboard_charts
from macro_output import build_macro_framework, build_key_indicators


def render_reports_page(results=None):
    st.header("Reports and Downloads")
    if results is None:
        results = run_model("baseline")

    if st.button("Generate Excel output and dashboard PNGs"):
        path = export_outputs(results)
        make_dashboard_charts(results)
        st.success(f"Files generated in outputs folder: {path}")

    macro = build_macro_framework(results)
    key = build_key_indicators(results)

    st.download_button(
        "Download full macro framework CSV",
        macro.to_csv(index=False).encode("utf-8"),
        "macro_framework.csv",
        "text/csv",
    )
    st.download_button(
        "Download key indicators CSV",
        key.to_csv(index=False).encode("utf-8"),
        "key_indicators.csv",
        "text/csv",
    )
    st.download_button(
        "Download GDP reconciliation CSV",
        results["GDP_Reconciliation"].to_csv().encode("utf-8"),
        "GDP_Reconciliation.csv",
        "text/csv",
    )
