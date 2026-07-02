# -*- coding: utf-8 -*-
"""
main.py
Core runner. Only main.py and app.py should be executed.

v8 update
---------
Runs final model validation after solving. Dashboards and reports can use
Model_Validation and Executive_Indicators to avoid displaying invalid ratios.
"""

from data_loader import load_source_data
from assumptions import ScenarioShock
from solver import solve_macro_model
from config import FORECAST_END_YEAR
from model_validation import validate_model_outputs, build_executive_indicators, has_critical_errors


def run_model(
    scenario: str = "baseline",
    custom_shock: ScenarioShock | None = None,
    uploaded_files: dict | None = None,
    strict_validation: bool = False,
) -> dict:
    data = load_source_data(uploaded_files=uploaded_files)

    latest_actual = data["latest_actual_year"]
    forecast_start = latest_actual + 1

    if forecast_start > FORECAST_END_YEAR:
        raise ValueError(
            f"Latest actual year is {latest_actual}, which is beyond or equal to "
            f"the configured forecast end year {FORECAST_END_YEAR}. "
            "Increase FORECAST_END_YEAR in config.py."
        )

    solved = solve_macro_model(
        data["wide"],
        scenario=scenario,
        custom_shock=custom_shock,
        start_year=forecast_start,
        end_year=FORECAST_END_YEAR,
    )

    results = {
        "Data_Checks": data["checks"],
        "Source_Wide": data["wide"],
        "Latest_Actual_Year": latest_actual,
        "Forecast_Start_Year": forecast_start,
        "Forecast_End_Year": FORECAST_END_YEAR,
        "Source_Mode": data["source_mode"],
        **solved,
    }

    validation = validate_model_outputs(results)
    executive = build_executive_indicators(results)
    results["Model_Validation"] = validation
    results["Executive_Indicators"] = executive
    results["Validation_Passed"] = not has_critical_errors(validation)

    if strict_validation and not results["Validation_Passed"]:
        raise ValueError("Model validation failed. Review Model_Validation before using forecasts.")

    return results


if __name__ == "__main__":
    from outputs import export_outputs, make_dashboard_charts
    results = run_model("baseline")
    path = export_outputs(results)
    make_dashboard_charts(results)
    print(f"Model run complete: {path}")
    print(f"Latest actual year: {results['Latest_Actual_Year']}")
    print(f"Forecast start year: {results['Forecast_Start_Year']}")
    print("DATA CHECKS")
    print(results["Data_Checks"].to_string(index=False))
    print("MODEL VALIDATION")
    print(results["Model_Validation"].to_string(index=False))
