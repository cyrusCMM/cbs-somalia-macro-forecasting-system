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


## v4 updates

- Forecast horizon extended to 2035.
- Added `shock_engine.py` for simultaneous macro shock bundles.
- Scenario Analysis now transmits shocks across real, external, fiscal and monetary blocks.
- Scenario page now compares baseline versus scenario for GDP, demand, fiscal balance, debt, current account, M2 and private credit.


## v5 updates

- Split aggregate demand shock into:
  - Household consumption shock
  - Private investment shock
  - Government consumption shock
  - Public investment shock
  - Export demand shock
  - Import demand shock
- Scenario Analysis page now shows component-level real economy shocks.
- Demand shocks now transmit separately into GDP, imports, fiscal revenue, expenditure, debt, current account, M2 and private credit.
