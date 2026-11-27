"""Deterministic Decimal financial engine for IdeaStress.

LLMs NEVER perform arithmetic here. Every figure is computed with Python Decimal
precision, explicit currency tracking, and safe boundary guards.
"""

from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

from ideastress.domain.models import (
    BusinessType,
    FinancialAnalysis,
    FinancialInputs,
    MonthlyProjection,
    ScenarioMetrics,
    SensitivityPoint,
)
from ideastress.exceptions import CurrencyMismatchError, FinancialValidationError

TWO_PLACES = Decimal("0.01")


def q2(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def validate_financial_inputs(inputs: FinancialInputs) -> None:
    """Validate financial inputs before running deterministic math."""
    if not inputs.currency or len(inputs.currency.strip()) != 3:
        raise CurrencyMismatchError("Currency must be a valid 3-letter ISO-4217 code (e.g., USD, MYR, EUR).")
    if inputs.unit_price <= Decimal("0"):
        raise FinancialValidationError("unit_price must be strictly greater than 0.")
    if inputs.variable_cost_per_unit < Decimal("0"):
        raise FinancialValidationError("variable_cost_per_unit cannot be negative.")
    if inputs.fixed_monthly_costs < Decimal("0"):
        raise FinancialValidationError("fixed_monthly_costs cannot be negative.")
    if inputs.starting_cash < Decimal("0"):
        raise FinancialValidationError("starting_cash cannot be negative.")
    if inputs.horizon_months < 1 or inputs.horizon_months > 60:
        raise FinancialValidationError("horizon_months must be between 1 and 60.")
    if inputs.monthly_churn_rate < Decimal("0") or inputs.monthly_churn_rate >= Decimal("1"):
        raise FinancialValidationError("monthly_churn_rate must be in [0, 1).")
    if inputs.refund_rate < Decimal("0") or inputs.refund_rate >= Decimal("1"):
        raise FinancialValidationError("refund_rate must be in [0, 1).")
    if inputs.business_type == BusinessType.MARKETPLACE:
        tr = inputs.take_rate if inputs.take_rate is not None else Decimal("0.15")
        if tr <= Decimal("0") or tr > Decimal("1"):
            raise FinancialValidationError("marketplace take_rate must be in (0, 1].")



PAYMENT_PROCESSOR_FEES = {
    "none": (Decimal("0.00"), Decimal("0.00")),
    "stripe_us": (Decimal("0.029"), Decimal("0.30")),      # Stripe US standard domestic card: 2.9% + $0.30
    "stripe_saas": (Decimal("0.036"), Decimal("0.30")),    # Stripe US card + 0.7% Stripe Billing
    "mor_paddle": (Decimal("0.050"), Decimal("0.50")),     # Merchant of Record (Paddle / Lemon Squeezy): 5% + $0.50
}


def compute_payment_fee_per_unit(inputs: FinancialInputs) -> Decimal:
    """Compute per-transaction payment processing fee based on selected preset."""
    pct, flat = PAYMENT_PROCESSOR_FEES.get(inputs.payment_processor, (Decimal("0.00"), Decimal("0.00")))
    gross_charge = inputs.unit_price
    if inputs.business_type == BusinessType.MARKETPLACE:
        # Marketplace typically processes full GMV or platform fee depending on setup; compute on net take
        take_rate = inputs.take_rate if inputs.take_rate is not None else Decimal("0.15")
        gross_charge = inputs.unit_price * take_rate
    return q2(gross_charge * pct + flat)


def effective_unit_revenue(inputs: FinancialInputs) -> Decimal:
    """Net revenue realized per unit/customer/order after take-rate and refunds."""
    gross_unit = inputs.unit_price
    if inputs.business_type == BusinessType.MARKETPLACE:
        take_rate = inputs.take_rate if inputs.take_rate is not None else Decimal("0.15")
        gross_unit = gross_unit * take_rate
    net_unit = gross_unit * (Decimal("1") - inputs.refund_rate)
    return net_unit


def run_scenario(
    inputs: FinancialInputs,
    scenario_name: str = "base",
    price_mult: Decimal = Decimal("1.0"),
    new_cust_mult: Decimal = Decimal("1.0"),
    var_cost_mult: Decimal = Decimal("1.0"),
    fixed_cost_mult: Decimal = Decimal("1.0"),
    acq_spend_mult: Decimal = Decimal("1.0"),
    churn_mult: Decimal = Decimal("1.0"),
) -> ScenarioMetrics:
    """Run a single deterministic monthly cash-flow and unit-economics simulation."""
    validate_financial_inputs(inputs)

    adj_price = inputs.unit_price * price_mult
    payment_fee = compute_payment_fee_per_unit(inputs)
    adj_var_cost = inputs.variable_cost_per_unit * (Decimal('1') + inputs.us_payroll_tax_burden_pct) * var_cost_mult + payment_fee
    adj_fixed = inputs.fixed_monthly_costs * fixed_cost_mult
    adj_acq_spend = inputs.monthly_acquisition_spend * acq_spend_mult
    adj_churn = min(Decimal("0.95"), max(Decimal("0"), inputs.monthly_churn_rate * churn_mult))

    base_new = inputs.monthly_new_customers
    if inputs.monthly_visitors is not None and (
        inputs.observed_conversion_rate is not None or inputs.conversion_rate is not None
    ):
        cvr = inputs.observed_conversion_rate if inputs.observed_conversion_rate is not None else inputs.conversion_rate
        assert cvr is not None
        base_new = int((Decimal(inputs.monthly_visitors) * cvr).to_integral_value(rounding=ROUND_HALF_UP))

    adj_new_customers = max(0, int((Decimal(base_new) * new_cust_mult).to_integral_value(rounding=ROUND_HALF_UP)))

    # If observed CAC is given and acq_spend wasn't explicitly scaled up, derive spend from observed CAC
    if inputs.observed_cac is not None and inputs.monthly_acquisition_spend == Decimal("0"):
        adj_acq_spend = inputs.observed_cac * Decimal(adj_new_customers) * acq_spend_mult

    # Net unit revenue
    if inputs.business_type == BusinessType.MARKETPLACE:
        take_rate = inputs.take_rate if inputs.take_rate is not None else Decimal("0.15")
        unit_net_rev = adj_price * take_rate * (Decimal("1") - inputs.refund_rate)
    else:
        unit_net_rev = adj_price * (Decimal("1") - inputs.refund_rate)

    unit_contrib = unit_net_rev - adj_var_cost
    gross_margin_pct: Optional[Decimal] = None
    if unit_net_rev > Decimal("0"):
        gross_margin_pct = q2((unit_contrib / unit_net_rev) * Decimal("100"))

    # Break-even units (monthly)
    total_monthly_overhead = adj_fixed + adj_acq_spend
    if unit_contrib <= Decimal("0"):
        break_even_units = None
        break_even_status = "NOT_REACHABLE_UNDER_CURRENT_ASSUMPTIONS"
    elif total_monthly_overhead == Decimal("0"):
        break_even_units = 0
        break_even_status = "REACHABLE"
    else:
        break_even_units = int(math.ceil(float(total_monthly_overhead / unit_contrib)))
        break_even_status = "REACHABLE"

    # CAC
    cac: Optional[Decimal] = None
    if inputs.observed_cac is not None:
        cac = q2(inputs.observed_cac * acq_spend_mult)
    elif adj_new_customers > 0 and adj_acq_spend > Decimal("0"):
        cac = q2(adj_acq_spend / Decimal(adj_new_customers))
    elif adj_acq_spend == Decimal("0"):
        cac = Decimal("0.00")

    # LTV & Payback (only meaningful for recurring SaaS with non-zero churn)
    ltv: Optional[Decimal] = None
    ltv_status = "NOT_APPLICABLE_NON_RECURRING"
    ltv_to_cac: Optional[Decimal] = None
    cac_payback: Optional[Decimal] = None

    if inputs.business_type == BusinessType.SAAS:
        if unit_contrib <= Decimal("0"):
            ltv_status = "NEGATIVE_UNIT_MARGIN"
        elif adj_churn <= Decimal("0"):
            ltv_status = "REQUIRES_NONZERO_CHURN_DATA"
        else:
            ltv = q2(unit_contrib / adj_churn)
            ltv_status = "CALCULATED"
            if cac is not None and cac > Decimal("0"):
                ltv_to_cac = q2(ltv / cac)
                cac_payback = q2(cac / unit_contrib)
            elif cac == Decimal("0.00"):
                ltv_to_cac = None
                cac_payback = Decimal("0.00")
    else:
        if cac is not None and cac > Decimal("0") and unit_contrib > Decimal("0"):
            cac_payback = q2(cac / unit_contrib)

    # Monthly cash-flow simulation
    projections: List[MonthlyProjection] = []
    cash = inputs.starting_cash
    active = inputs.starting_customers
    total_rev = Decimal("0")
    total_net_cf = Decimal("0")
    min_cash = cash
    is_recurring = inputs.business_type == BusinessType.SAAS

    for m in range(1, inputs.horizon_months + 1):
        if is_recurring:
            churned = int((Decimal(active) * adj_churn).to_integral_value(rounding=ROUND_HALF_UP))
            active = max(0, active - churned) + adj_new_customers
            billable_units = active
        else:
            churned = 0
            active = adj_new_customers
            billable_units = adj_new_customers

        rev = unit_net_rev * Decimal(billable_units)
        cogs = adj_var_cost * Decimal(billable_units)
        gp = rev - cogs
        ebt = gp - adj_fixed - adj_acq_spend
        tax_reserve = (ebt * inputs.effective_tax_rate) if (ebt > Decimal('0') and inputs.effective_tax_rate > Decimal('0')) else Decimal('0')
        net_cf = ebt - tax_reserve
        cash = cash + net_cf

        total_rev += rev
        total_net_cf += net_cf
        if cash < min_cash:
            min_cash = cash

        projections.append(
            MonthlyProjection(
                month=m,
                active_customers=active,
                new_customers=adj_new_customers,
                churned_customers=churned,
                revenue=q2(rev),
                cogs=q2(cogs),
                gross_profit=q2(gp),
                acquisition_spend=q2(adj_acq_spend),
                fixed_costs=q2(adj_fixed),
                net_cash_flow=q2(net_cf),
                ending_cash=q2(cash),
            )
        )

    # Runway calculation based on average monthly net burn
    avg_monthly_net_cf = total_net_cf / Decimal(inputs.horizon_months)
    if avg_monthly_net_cf >= Decimal("0"):
        runway_months: Optional[Decimal] = None
        runway_status = "CASH_FLOW_POSITIVE"
    else:
        monthly_burn = -avg_monthly_net_cf
        runway_months = q2(inputs.starting_cash / monthly_burn) if monthly_burn > Decimal("0") else None
        runway_status = "BURNING_CASH"

    last_month_rev = projections[-1].revenue if projections else Decimal("0.00")
    m12_mrr = last_month_rev if is_recurring else Decimal("0.00")
    m12_arr = q2(m12_mrr * Decimal("12")) if is_recurring else Decimal("0.00")

    return ScenarioMetrics(
        scenario_name=scenario_name,
        currency=inputs.currency.upper(),
        horizon_months=inputs.horizon_months,
        unit_contribution_margin=q2(unit_contrib),
        gross_margin_pct=gross_margin_pct,
        break_even_units=break_even_units,
        break_even_status=break_even_status,
        cac=cac,
        ltv=ltv,
        ltv_status=ltv_status,
        ltv_to_cac=ltv_to_cac,
        cac_payback_months=cac_payback,
        month_12_mrr=q2(m12_mrr),
        month_12_arr_run_rate=m12_arr,
        total_revenue=q2(total_rev),
        total_net_cash_flow=q2(total_net_cf),
        min_cash_balance=q2(min_cash),
        ending_cash_balance=q2(cash),
        runway_months=runway_months,
        runway_status=runway_status,
        projections=projections,
        assumptions_applied={
            "price_multiplier": str(price_mult),
            "new_customers_multiplier": str(new_cust_mult),
            "variable_cost_multiplier": str(var_cost_mult),
            "fixed_cost_multiplier": str(fixed_cost_mult),
            "acquisition_spend_multiplier": str(acq_spend_mult),
            "churn_multiplier": str(churn_mult),
        },
    )


def run_sensitivity_analysis(inputs: FinancialInputs, base: ScenarioMetrics) -> List[SensitivityPoint]:
    """Single-variable sensitivity stress tests around the base scenario."""
    tests = [
        ("Unit Price", "-20%", dict(price_mult=Decimal("0.80"))),
        ("Unit Price", "-10%", dict(price_mult=Decimal("0.90"))),
        ("Unit Price", "+20%", dict(price_mult=Decimal("1.20"))),
        ("New Customer Volume", "-30%", dict(new_cust_mult=Decimal("0.70"))),
        ("Acquisition Spend / CAC", "+50%", dict(acq_spend_mult=Decimal("1.50"))),
        ("Acquisition Spend / CAC", "+100%", dict(acq_spend_mult=Decimal("2.00"))),
        ("Variable Cost", "+25%", dict(var_cost_mult=Decimal("1.25"))),
        ("Fixed Costs", "+25%", dict(fixed_cost_mult=Decimal("1.25"))),
    ]
    if inputs.business_type == BusinessType.SAAS:
        tests.append(("Monthly Churn", "+50%", dict(churn_mult=Decimal("1.50"))))

    points: List[SensitivityPoint] = []
    for var_name, label, kwargs in tests:
        res = run_scenario(inputs, scenario_name=f"sens_{var_name}_{label}", **kwargs)
        points.append(
            SensitivityPoint(
                variable=var_name,
                change_label=label,
                ending_cash=res.ending_cash_balance,
                delta_ending_cash=q2(res.ending_cash_balance - base.ending_cash_balance),
                break_even_units=res.break_even_units,
                survives_horizon=res.min_cash_balance >= Decimal("0"),
            )
        )
    return points


def run_full_financial_analysis(inputs: FinancialInputs) -> FinancialAnalysis:
    """Run Conservative, Base, Optimistic scenarios + sensitivity + Reverse Frontier Solver."""
    from ideastress.finance.solver import solve_reverse_frontier

    validate_financial_inputs(inputs)

    conservative = run_scenario(
        inputs,
        scenario_name="conservative",
        price_mult=Decimal("0.90"),
        new_cust_mult=Decimal("0.65"),
        var_cost_mult=Decimal("1.15"),
        fixed_cost_mult=Decimal("1.10"),
        acq_spend_mult=Decimal("1.25"),
        churn_mult=Decimal("1.35"),
    )
    base = run_scenario(inputs, scenario_name="base")
    optimistic = run_scenario(
        inputs,
        scenario_name="optimistic",
        price_mult=Decimal("1.10"),
        new_cust_mult=Decimal("1.30"),
        var_cost_mult=Decimal("0.95"),
        fixed_cost_mult=Decimal("1.00"),
        acq_spend_mult=Decimal("0.90"),
        churn_mult=Decimal("0.80"),
    )

    from ideastress.finance.montecarlo import run_monte_carlo

    sensitivity = run_sensitivity_analysis(inputs, base)
    frontier = solve_reverse_frontier(inputs)
    mc = run_monte_carlo(inputs, simulations=1000, seed=42)

    limitations = [
        "Scenario outputs are deterministic projections of user/model assumptions, not revenue guarantees.",
        f"Tax included: {'Yes' if inputs.tax_included else 'No (corporate/sales taxes, depreciation, and working capital are excluded)'}.",
        f"All figures strictly denominated in {inputs.currency.upper()}; cross-currency aggregation is disabled.",
    ]
    if inputs.business_type == BusinessType.SAAS:
        limitations.append("ARR is reported as annualized Month-12 MRR run-rate, not recognized annual revenue.")

    return FinancialAnalysis(
        currency=inputs.currency.upper(),
        business_type=inputs.business_type,
        tax_included=inputs.tax_included,
        scenarios={
            "conservative": conservative,
            "base": base,
            "optimistic": optimistic,
        },
        sensitivity=sensitivity,
        reverse_frontier=frontier,
        monte_carlo=mc,
        limitations=limitations,
    )
