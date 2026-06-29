# -*- coding: utf-8 -*-
"""
fiscal_sector.py
Fiscal forecast, ratios and insights.
"""

import pandas as pd


def _last(wide, code, default=0.0):
    if code not in wide.columns:
        return default
    s = wide[code].dropna()
    return float(s.iloc[-1]) if len(s) else default


def forecast_fiscal_sector(wide: pd.DataFrame, assumptions: pd.DataFrame, real: pd.DataFrame, external: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=assumptions.index)
    ngdp = real.loc[assumptions.index, "NGDP"]
    npc = real.loc[assumptions.index, "NPC"]
    m_goods = external.loc[assumptions.index, "M_GOODS"]

    imp_duty = _last(wide, "IMP_DUTY")
    dom_sales = _last(wide, "DOM_SALES")
    pit = _last(wide, "PIT")
    cit = _last(wide, "CIT")
    nontax = _last(wide, "NONTAX")
    debt = _last(wide, "GOV_DEBT", 0.0)

    prev_m_goods = _last(wide, "M_GOODS")
    prev_npc = _last(wide, "NPC")
    prev_ngdp = _last(wide, "NGDP")

    for year, a in assumptions.iterrows():
        g_m = (m_goods.loc[year] / prev_m_goods - 1.0) if prev_m_goods else 0.0
        g_npc = (npc.loc[year] / prev_npc - 1.0) if prev_npc else 0.0
        g_ngdp = (ngdp.loc[year] / prev_ngdp - 1.0) if prev_ngdp else 0.0

        imp_duty = imp_duty * (1.0 + g_m * a["Customs_buoyancy"] + a["Revenue_effort"])
        dom_sales = dom_sales * (1.0 + g_npc * a["VAT_buoyancy"] + a["Revenue_effort"])
        pit = pit * (1.0 + g_ngdp * a["IncomeTax_buoyancy"] + a["Revenue_effort"])
        cit = cit * (1.0 + g_ngdp * a["CIT_buoyancy"] + a["Revenue_effort"])
        nontax = nontax * (1.0 + g_ngdp * a["Nontax_buoyancy"])

        grants = ngdp.loc[year] * a["Grants_GDP_ratio"]
        tax_revenue = imp_duty + dom_sales + pit + cit
        domestic_revenue = tax_revenue + nontax
        total_revenue = domestic_revenue + grants

        wages = ngdp.loc[year] * a["Wages_GDP_ratio"] * (1 + a["Expenditure_pressure"])
        goods_services = ngdp.loc[year] * a["GoodsServices_GDP_ratio"] * (1 + a["Expenditure_pressure"])
        transfers = ngdp.loc[year] * a["Transfers_GDP_ratio"] * (1 + a["Expenditure_pressure"])
        capex = ngdp.loc[year] * a["Capex_GDP_ratio"] * (1 + a["Expenditure_pressure"])
        other_exp = ngdp.loc[year] * a["OtherExp_GDP_ratio"] * (1 + a["Expenditure_pressure"])
        interest = debt * a["Interest_effective_rate"]

        total_expenditure = wages + goods_services + transfers + capex + other_exp + interest
        fiscal_balance = total_revenue - total_expenditure
        debt = max(0.0, debt - fiscal_balance)

        out.loc[year, "IMP_DUTY"] = imp_duty
        out.loc[year, "DOM_SALES"] = dom_sales
        out.loc[year, "PIT"] = pit
        out.loc[year, "CIT"] = cit
        out.loc[year, "NONTAX"] = nontax
        out.loc[year, "GRANTS"] = grants
        out.loc[year, "TAX_REVENUE"] = tax_revenue
        out.loc[year, "DOMESTIC_REVENUE"] = domestic_revenue
        out.loc[year, "TOTAL_REVENUE"] = total_revenue
        out.loc[year, "WAGES"] = wages
        out.loc[year, "GDS_SERV_EXP"] = goods_services
        out.loc[year, "TRANSFERS"] = transfers
        out.loc[year, "CAPEX"] = capex
        out.loc[year, "OTHER_EXP"] = other_exp
        out.loc[year, "INT_PAY"] = interest
        out.loc[year, "TOTAL_EXPENDITURE"] = total_expenditure
        out.loc[year, "FISCAL_BALANCE"] = fiscal_balance
        out.loc[year, "FISCAL_BALANCE_GDP"] = fiscal_balance / ngdp.loc[year]
        out.loc[year, "DEBT"] = debt
        out.loc[year, "DEBT_GDP"] = debt / ngdp.loc[year]

        prev_m_goods = m_goods.loc[year]
        prev_npc = npc.loc[year]
        prev_ngdp = ngdp.loc[year]

    return out


def fiscal_sector_insights(fiscal: pd.DataFrame) -> list[str]:
    latest = int(fiscal.index.max())
    rev = fiscal.loc[latest, "TOTAL_REVENUE"]
    exp = fiscal.loc[latest, "TOTAL_EXPENDITURE"]
    bal = fiscal.loc[latest, "FISCAL_BALANCE_GDP"]
    debt = fiscal.loc[latest, "DEBT_GDP"]
    return [
        f"Total revenue and grants reach USD {rev/1e6:,.1f} million by {latest}.",
        f"Total expenditure reaches USD {exp/1e6:,.1f} million by {latest}.",
        f"The fiscal balance is projected at {bal*100:,.1f}% of GDP.",
        f"Debt is projected at {debt*100:,.1f}% of GDP, based on the current closure rule."
    ]
