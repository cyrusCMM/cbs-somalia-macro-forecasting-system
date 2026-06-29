# -*- coding: utf-8 -*-
"""Data management page."""

import streamlit as st
from config import DATA_DIR, DATA_FILES
from data_loader import load_source_data
from utils import display_table


def render_data_page():
    st.header("Data Management")
    st.caption("Source data are stored by block. Users update CSVs or the source workbook outside the app, then rerun the model.")

    data = load_source_data()
    st.subheader("Data checks")
    st.dataframe(data["checks"], use_container_width=True)

    st.subheader("Source data preview")
    block = st.selectbox("Select block", list(DATA_FILES.keys()))
    raw = data["raw"]
    preview = raw[raw["Block"].str.strip() == block].copy()
    st.dataframe(preview.head(500), use_container_width=True)

    st.subheader("Wide source data")
    display_table(data["wide"].tail(15))
