# -*- coding: utf-8 -*-
"""
main.py
Core runner. Only main.py and app.py should be executed.
"""

from data_loader import load_source_data
from assumptions import ScenarioShock
from solver import solve_macro_model


def run_model(scenario: str = "baseline", custom_shock: ScenarioShock | None = None) -> dict:
    data = load_source_data()
    solved = solve_macro_model(data["wide"], scenario=scenario, custom_shock=custom_shock)

    return {
        "Data_Checks": data["checks"],
        "Source_Wide": data["wide"],
        **solved,
    }


if __name__ == "__main__":
    from outputs import export_outputs, make_dashboard_charts
    results = run_model("baseline")
    path = export_outputs(results)
    make_dashboard_charts(results)
    print(f"Model run complete: {path}")
    print(results["Data_Checks"].to_string(index=False))
