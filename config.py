# -*- coding: utf-8 -*-
"""
config.py
CBS Somalia Macro Forecasting System - global configuration.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

FORECAST_START_YEAR = 2025
FORECAST_END_YEAR = 2030
BASE_YEAR = 2024

DATA_FILES = {
    "Real": "Real_Data.csv",
    "Fiscal": "Fiscal_Data.csv",
    "External": "External_Data.csv",
    "Monetary": "Monetary_Data.csv",
}

SCENARIOS = ["baseline", "optimistic", "pessimistic", "custom"]
SD_WATCH_THRESHOLD = 0.10

APP_TITLE = "CBS Somalia Macroeconomic Forecasting System"
CURRENCY_SCALE = 1_000_000
CURRENCY_LABEL = "USD million"
