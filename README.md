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


## v6 updates

- Added upload-based data workflow.
- Users can upload either:
  - one Excel workbook with sheets Real_Data, Fiscal_Data, External_Data, Monetary_Data; or
  - four CSV files: Real_Data.csv, Fiscal_Data.csv, External_Data.csv, Monetary_Data.csv.
- Uploaded data are stored in Streamlit session state and used across pages in that session.
- GitHub should contain code and sample/demo data only, not confidential live data.
- Forecast start year is automatically detected as latest actual year + 1.


## v7 updates

- Added stronger source-data validation.
- Data checks now include:
  - duplicate code-year rows,
  - required variable availability,
  - extra/non-required variable listing,
  - block-level year coverage,
  - latest actual year,
  - GDP expenditure identity and statistical discrepancy check,
  - SNBS GDP revision variable availability.
- Forecast start remains automatic: latest actual year + 1.
- No behavioural model interface changes are required for SNBS historical data revisions when file structure and codes remain unchanged.


## v8 updates

- Added `model_validation.py` as a final validation gate after the model solves.
- Executive dashboard now uses final solved indicators from `Executive_Indicators`.
- Dashboard ratios with critical validation errors display `CHECK` instead of a misleading number.
- External-sector debit flows are normalized so income debits enter the current account with the correct negative sign.
- Model output now includes:
  - `Model_Validation`
  - `Executive_Indicators`
  - `Validation_Passed`
- Reports export the validation diagnostics.
- Scenario outputs must validate before scenario charts are displayed.


## v9 updates

- Added full operational data upload workflow.
- Data Management page now supports:
  - one Excel workbook upload, or
  - four CSV block uploads.
- Uploaded files are buffered safely in Streamlit session state so all pages use the same active source.
- The app detects latest actual year automatically and forecasts from latest actual + 1.
- Added revision log comparing uploaded data against default app data.
- Reports page can download active source data and data checks.
- The app refreshes model results when the active data source changes.


## v10 hotfix

- Fixed repeated uploaded-file reads in Streamlit.
- Added file rewind before every `pd.read_csv()` / `pd.read_excel()` call.
- Prevents `pandas.errors.EmptyDataError` after uploading data, changing pages, or running scenarios.
