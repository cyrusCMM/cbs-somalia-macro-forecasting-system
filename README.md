# CBS Somalia Macroeconomic Forecasting System v3

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## What is new in v3

- Recursive macro solver: shocks propagate through real, external, fiscal and monetary blocks.
- Clean macro-framework export: one integrated output table with key indicators.
- Fixed fiscal stacked-bar charts: year labels and bar labels now render correctly.
- Improved dashboard labels: readable names, final-point labels, and clearer axes.
- Scenario page compares linked variables, not only NGDP.

## Source data

The app reads historical actuals from:

- data/Real_Data.csv
- data/Fiscal_Data.csv
- data/External_Data.csv
- data/Monetary_Data.csv

Forecasts are generated in Python.

## Main pages

- Home Dashboard
- Data Management
- Real Sector
- Fiscal Sector
- External Sector
- Monetary Sector
- Macro Framework
- Scenario Analysis
- Reports
