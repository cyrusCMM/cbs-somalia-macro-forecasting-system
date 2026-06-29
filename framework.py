# -*- coding: utf-8 -*-
"""Integrated macro framework page."""

import streamlit as st
from main import run_model
from macro_output import build_macro_framework, build_key_indicators


def render_framework_page(results=None):
    if results is None:
        results = run_model("baseline")

    st.header("Integrated Macroeconomic Framework")
    st.caption("Values are in USD million except ratio indicators.")

    tab1, tab2 = st.tabs(["Key Indicators", "Full Macro Framework"])

    key = build_key_indicators(results)
    macro = build_macro_framework(results)

    with tab1:
        st.dataframe(key, use_container_width=True)
        st.download_button("Download key indicators CSV", key.to_csv(index=False).encode("utf-8"), "key_indicators.csv", "text/csv")

    with tab2:
        st.dataframe(macro, use_container_width=True)
        st.download_button("Download full macro framework CSV", macro.to_csv(index=False).encode("utf-8"), "macro_framework.csv", "text/csv")
