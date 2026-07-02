# -*- coding: utf-8 -*-
"""Data management page.

v9 update
---------
This page is the operational data-update workflow.

It supports:
- upload one Excel workbook;
- upload four block CSV files;
- validate before use;
- compare uploaded data against the default app data;
- show revision log by variable/year;
- set uploaded data as the active session source;
- clear uploaded data and return to default source.

Important
---------
Uploaded data are stored in Streamlit session state only. This is intentional:
GitHub should contain code and sample/demo data, not confidential live data.
"""

from __future__ import annotations

import io
import pandas as pd
import streamlit as st

from config import DATA_FILES
from data_loader import load_source_data
from utils import display_table


def get_active_uploaded_files():
    """Return uploaded files stored in session state, if any."""
    return st.session_state.get("uploaded_files", None)


def _buffer_uploaded_file(uploaded_file):
    """
    Convert Streamlit UploadedFile into an in-memory BytesIO object.

    Streamlit UploadedFile objects can be consumed after reading. Storing a
    BytesIO copy in session_state prevents later pages from receiving an empty
    file handle.
    """
    if uploaded_file is None:
        return None
    data = uploaded_file.getvalue()
    bio = io.BytesIO(data)
    bio.name = uploaded_file.name
    bio.seek(0)
    return bio


def _rewind_uploaded_files(uploaded_files):
    """Reset stored BytesIO objects before each model/data-loader call."""
    if not uploaded_files:
        return uploaded_files
    for obj in uploaded_files.values():
        try:
            obj.seek(0)
        except Exception:
            pass
    return uploaded_files


def _set_uploaded_workbook(workbook):
    st.session_state["uploaded_files"] = {
        "workbook": _buffer_uploaded_file(workbook)
    }


def _set_uploaded_csvs(real, fiscal, external, monetary):
    st.session_state["uploaded_files"] = {
        "Real": _buffer_uploaded_file(real),
        "Fiscal": _buffer_uploaded_file(fiscal),
        "External": _buffer_uploaded_file(external),
        "Monetary": _buffer_uploaded_file(monetary),
    }


def _reset_uploads():
    st.session_state["uploaded_files"] = None
    st.session_state["last_uploaded_validation"] = None
    st.session_state["last_revision_log"] = None


def _build_revision_log(default_wide: pd.DataFrame, uploaded_wide: pd.DataFrame) -> pd.DataFrame:
    """
    Compare default/source data against uploaded data.

    Returns long table:
    Code, Year, Old_Value, New_Value, Change, Percent_Change, Status
    """
    all_years = sorted(set(default_wide.index).union(uploaded_wide.index))
    all_codes = sorted(set(default_wide.columns).union(uploaded_wide.columns))

    old = default_wide.reindex(index=all_years, columns=all_codes)
    new = uploaded_wide.reindex(index=all_years, columns=all_codes)

    diff_mask = ~(old.fillna("__NA__").astype(str).eq(new.fillna("__NA__").astype(str)))

    rows = []
    for year in all_years:
        changed_codes = diff_mask.columns[diff_mask.loc[year]].tolist()
        for code in changed_codes:
            old_val = old.loc[year, code]
            new_val = new.loc[year, code]

            if pd.isna(old_val) and pd.isna(new_val):
                continue

            if pd.isna(old_val):
                status = "NEW_VALUE"
                change = pd.NA
                pct = pd.NA
            elif pd.isna(new_val):
                status = "REMOVED_VALUE"
                change = pd.NA
                pct = pd.NA
            else:
                status = "REVISED_VALUE"
                change = new_val - old_val
                pct = change / old_val if old_val != 0 else pd.NA

            rows.append({
                "Code": code,
                "Year": int(year),
                "Old_Value": old_val,
                "New_Value": new_val,
                "Change": change,
                "Percent_Change": pct,
                "Status": status,
            })

    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=["Code", "Year", "Old_Value", "New_Value", "Change", "Percent_Change", "Status"])
    return out.sort_values(["Year", "Code"]).reset_index(drop=True)


def _validate_uploaded(uploaded_files):
    default_data = load_source_data()
    uploaded_files = _rewind_uploaded_files(uploaded_files)
    uploaded_data = load_source_data(uploaded_files=uploaded_files)
    revision_log = _build_revision_log(default_data["wide"], uploaded_data["wide"])
    return uploaded_data, revision_log


def _download_dataframe_button(label, df, filename):
    st.download_button(
        label,
        df.to_csv(index=False).encode("utf-8"),
        filename,
        "text/csv",
    )


def render_data_page():
    st.header("Data Management")
    st.caption("Upload revised historical data or a new actual year. The model will validate, compare, and forecast from the latest actual year + 1.")

    st.subheader("1. Current active source")
    if st.session_state.get("uploaded_files"):
        st.success("Active source: uploaded session data")
    else:
        st.info("Active source: default app data in the data/ folder")

    c_clear, c_refresh = st.columns([1, 3])
    with c_clear:
        if st.button("Clear uploaded data"):
            _reset_uploads()
            st.success("Uploaded data cleared. The model will use default app data.")

    st.subheader("2. Upload updated data")
    upload_mode = st.radio("Upload format", ["One Excel workbook", "Four CSV files"], horizontal=True)

    if upload_mode == "One Excel workbook":
        workbook = st.file_uploader(
            "Upload CBS source workbook",
            type=["xlsx", "xls"],
            help="Required sheets: Real_Data, Fiscal_Data, External_Data, Monetary_Data.",
        )

        if workbook is not None:
            if st.button("Validate workbook and set as active data"):
                candidate = {"workbook": _buffer_uploaded_file(workbook)}
                try:
                    uploaded_data, revision_log = _validate_uploaded(candidate)
                    _set_uploaded_workbook(workbook)
                    st.session_state["last_uploaded_validation"] = uploaded_data["checks"]
                    st.session_state["last_revision_log"] = revision_log
                    st.success(
                        f"Workbook accepted. Latest actual year detected: {uploaded_data['latest_actual_year']}. "
                        f"Forecast will start in {uploaded_data['latest_actual_year'] + 1}."
                    )
                except Exception as e:
                    st.error(f"Workbook validation failed: {e}")

    else:
        c1, c2 = st.columns(2)
        with c1:
            real = st.file_uploader("Upload Real_Data.csv", type=["csv"])
            fiscal = st.file_uploader("Upload Fiscal_Data.csv", type=["csv"])
        with c2:
            external = st.file_uploader("Upload External_Data.csv", type=["csv"])
            monetary = st.file_uploader("Upload Monetary_Data.csv", type=["csv"])

        if all([real, fiscal, external, monetary]):
            if st.button("Validate CSV files and set as active data"):
                candidate = {
                    "Real": _buffer_uploaded_file(real),
                    "Fiscal": _buffer_uploaded_file(fiscal),
                    "External": _buffer_uploaded_file(external),
                    "Monetary": _buffer_uploaded_file(monetary),
                }
                try:
                    uploaded_data, revision_log = _validate_uploaded(candidate)
                    _set_uploaded_csvs(real, fiscal, external, monetary)
                    st.session_state["last_uploaded_validation"] = uploaded_data["checks"]
                    st.session_state["last_revision_log"] = revision_log
                    st.success(
                        f"CSV files accepted. Latest actual year detected: {uploaded_data['latest_actual_year']}. "
                        f"Forecast will start in {uploaded_data['latest_actual_year'] + 1}."
                    )
                except Exception as e:
                    st.error(f"CSV validation failed: {e}")

    st.subheader("3. Active data checks")
    uploaded_files = get_active_uploaded_files()
    try:
        uploaded_files = _rewind_uploaded_files(uploaded_files)
        data = load_source_data(uploaded_files=uploaded_files)
    except Exception as e:
        st.error(f"Active data failed to load: {e}")
        st.stop()

    st.dataframe(data["checks"], use_container_width=True)

    failed = data["checks"][data["checks"]["status"].isin(["CHECK", "WATCH"])]
    if not failed.empty:
        st.warning("Some validation checks need attention. Review details before using the run for official forecasts.")
    else:
        st.success("All source-data validation checks passed.")

    st.subheader("4. Revision log")
    if uploaded_files:
        try:
            default_data = load_source_data()
            revision_log = _build_revision_log(default_data["wide"], data["wide"])
            st.caption(f"{len(revision_log):,} changed cells compared with the default app data.")
            st.dataframe(revision_log.head(1000), use_container_width=True)
            _download_dataframe_button("Download revision log", revision_log, "data_revision_log.csv")
        except Exception as e:
            st.warning(f"Could not build revision log: {e}")
    else:
        st.caption("Upload new data to generate a revision log against the default app data.")

    st.subheader("5. Source data preview")
    block = st.selectbox("Select block", list(DATA_FILES.keys()))
    raw = data["raw"]
    preview = raw[raw["Block"].str.strip() == block].copy()
    st.dataframe(preview.head(500), use_container_width=True)

    st.subheader("6. Wide source data")
    display_table(data["wide"].tail(20))

    st.info(
        "Recommended workflow: upload updated source data → validate → review revision log → run model → review model validation → export results."
    )
