"""Deterministic seeded Monte Carlo survival probability simulator.

Uses NumPy with a fixed default seed (42) for reproducible 1,000-path stress testing:
  - Perturbs monthly new customer acquisition (normal variance)
  - Perturbs acquisition spend / CAC with realistic upward skew (ads tend to overrun)
  - Perturbs monthly churn with a realistic Month 1-2 early-churn spike for SaaS
  - Applies payment processor fees (Stripe US 2.9%+$0.30, Stripe Billing +0.7%, MoR 5%+$0.50)
    and optional US effective tax reserve on positive monthly profit
"""

from __future__ import annotations

from decimal import Decimal
import numpy as np

from ideastress.domain.models import BusinessType, FinancialInputs, MonteCarloSummary
from ideastress.finance.engine import compute_payment_fee_per_unit, q2, validate_financial_inputs


def run_monte_carlo(
    inputs: FinancialInputs,
    *,
    simulations: int = 1000,
    seed: int = 42,
) -> MonteCarloSummary:
    """Run N reproducible Monte Carlo paths and compute survival probability & cash percentiles."""
    validate_financial_inputs(inputs)
    rng = np.random.default_rng(seed)

    is_saas = inputs.business_type == BusinessType.SAAS
    is_marketplace = inputs.business_type == BusinessType.MARKETPLACE
    take_rate = float(inputs.take_rate if inputs.take_rate is not None else Decimal("0.15"))
    refund_rate = float(inputs.refund_rate)
    tax_rate = float(inputs.effective_tax_rate)
    payroll_burden = float(inputs.us_payroll_tax_burden_pct)

    unit_price = float(inputs.unit_price)
    payment_fee = float(compute_payment_fee_per_unit(inputs))
    base_var_cost = float(inputs.variable_cost_per_unit) * (1.0 + payroll_burden) + payment_fee
    fixed_cost = float(inputs.fixed_monthly_costs)

    base_new = inputs.monthly_new_customers
    if inputs.monthly_visitors is not None and (
        inputs.observed_conversion_rate is not None or inputs.conversion_rate is not None
    ):
        cvr = float(inputs.observed_conversion_rate if inputs.observed_conversion_rate is not None else inputs.conversion_rate)
        base_new = int(round(inputs.monthly_visitors * cvr))

    base_spend = float(inputs.monthly_acquisition_spend)
    if inputs.observed_cac is not None and base_spend == 0.0:
        base_spend = float(inputs.observed_cac) * base_new

    base_churn = float(inputs.monthly_churn_rate)
    starting_cash = float(inputs.starting_cash)
    horizon = inputs.horizon_months

    # Vectorized across `simulations` paths
    cash = np.full(simulations, starting_cash, dtype=np.float64)
    min_cash = np.full(simulations, starting_cash, dtype=np.float64)
    active = np.full(simulations, float(inputs.starting_customers), dtype=np.float64)

    # Path-level structural multipliers (e.g., whether channel CAC & churn are structurally better/worse)
    cac_mult = np.clip(rng.lognormal(mean=0.05, sigma=0.22, size=simulations), 0.65, 2.40)
    churn_mult = np.clip(rng.normal(loc=1.02, scale=0.20, size=simulations), 0.50, 2.20)
    var_cost_mult = np.clip(rng.normal(loc=1.0, scale=0.08, size=simulations), 0.80, 1.35)

    unit_net_rev = (unit_price * take_rate if is_marketplace else unit_price) * (1.0 - refund_rate)

    for m in range(1, horizon + 1):
        # Month-by-month acquisition noise
        new_c = np.maximum(0.0, np.round(rng.normal(loc=base_new, scale=max(1.0, base_new * 0.22), size=simulations)))
        if is_saas:
            # Realistic Month 1-2 early onboarding churn spike (1.35x in M1, 1.15x in M2)
            early_spike = 1.35 if m == 1 else (1.15 if m == 2 else 1.0)
            m_churn = np.clip(base_churn * churn_mult * early_spike, 0.0, 0.90)
            churned = np.round(active * m_churn)
            active = np.maximum(0.0, active - churned) + new_c
            billable = active
        else:
            active = new_c
            billable = new_c

        rev = billable * unit_net_rev
        cogs = billable * (base_var_cost * var_cost_mult)
        acq = base_spend * cac_mult
        ebt = rev - cogs - fixed_cost - acq
        taxes = np.where(ebt > 0.0, ebt * tax_rate, 0.0)
        net_cf = ebt - taxes

        cash = cash + net_cf
        min_cash = np.minimum(min_cash, cash)

    survived_mask = min_cash >= 0.0
    survival_pct = q2(Decimal(str(float(np.mean(survived_mask)) * 100.0)))

    p10_end = q2(Decimal(str(float(np.percentile(cash, 10)))))
    p50_end = q2(Decimal(str(float(np.percentile(cash, 50)))))
    p90_end = q2(Decimal(str(float(np.percentile(cash, 90)))))
    p10_min = q2(Decimal(str(float(np.percentile(min_cash, 10)))))

    if survival_pct >= Decimal("85.00"):
        risk_label = "LOW_RISK"
    elif survival_pct >= Decimal("60.00"):
        risk_label = "MODERATE_RISK"
    elif survival_pct >= Decimal("30.00"):
        risk_label = "HIGH_RISK"
    else:
        risk_label = "CRITICAL_RISK"

    return MonteCarloSummary(
        simulations=simulations,
        seed=seed,
        currency=inputs.currency.upper(),
        horizon_months=horizon,
        survival_probability_pct=survival_pct,
        p10_ending_cash=p10_end,
        p50_ending_cash=p50_end,
        p90_ending_cash=p90_end,
        p10_min_cash=p10_min,
        bankruptcy_risk_label=risk_label,
    )
