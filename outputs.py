# -*- coding: utf-8 -*-
"""
outputs.py
Export model outputs to Excel and static dashboard PNGs.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from config import OUTPUT_DIR, CURRENCY_SCALE
from macro_output import build_macro_framework, build_key_indicators


def export_outputs(results: dict, output_dir: Path = OUTPUT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "cbs_somalia_macro_model_outputs.xlsx"

    macro = build_macro_framework(results)
    key = build_key_indicators(results)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        key.to_excel(writer, sheet_name="Key_Indicators", index=False)
        macro.to_excel(writer, sheet_name="Macro_Framework", index=False)

        # Block outputs retained as working sheets
        for name in [
            "Assumptions", "Real_Sector", "External_Sector",
            "Fiscal_Sector", "Monetary_Sector", "GDP_Reconciliation",
            "Nominal_GDP_Output", "Data_Checks"
        ]:
            obj = results.get(name)
            if isinstance(obj, pd.DataFrame):
                obj.to_excel(writer, sheet_name=name[:31])

    return path


def make_dashboard_charts(results: dict, output_dir: Path = OUTPUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    real = results["Real_Sector"]
    fiscal = results["Fiscal_Sector"]
    rec = results["GDP_Reconciliation"]
    external = results["External_Sector"]

    fig, ax = plt.subplots(figsize=(10, 5))
    (real[["NGDP", "Final_consumption", "NINV", "NXGS", "NMGS"]] / CURRENCY_SCALE).dropna(how="all").plot(ax=ax)
    ax.set_title("Macro components")
    ax.set_ylabel("USD million")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard_macro_components.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    (rec["Statistical_discrepancy_pct_GDP"] * 100).dropna().plot(ax=ax)
    ax.set_title("Statistical discrepancy (% GDP)")
    ax.set_ylabel("Percent")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard_sd_gdp.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    (fiscal[["TOTAL_REVENUE", "TOTAL_EXPENDITURE", "FISCAL_BALANCE"]] / CURRENCY_SCALE).dropna(how="all").plot(ax=ax)
    ax.set_title("Fiscal framework")
    ax.set_ylabel("USD million")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard_fiscal.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    (external[["Exports_GS", "Imports_GS", "CAB"]] / CURRENCY_SCALE).dropna(how="all").plot(ax=ax)
    ax.set_title("External sector")
    ax.set_ylabel("USD million")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "dashboard_external.png", dpi=150)
    plt.close(fig)
