"""Auto-Fix Minimum Viable Rescue Prescription Engine (with Annual Prepay Cash-Flow Rescue).

When a business model has <85% Monte Carlo survival probability, this deterministic
optimizer searches 4 independent levers to tell the founder the EXACT smallest change
needed to rescue the business:
  1. Price Raise (exact minimum unit price)
  2. Churn Reduction (SaaS exact target monthly churn %)
  3. Acquisition Spend Cap (exact max monthly ad spend)
  4. Annual Prepay Plan (e.g., 25% of new SaaS customers prepaying 12 months at 20% off)
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

import numpy as np
from pydantic import BaseModel

from ideastress.domain.models import BusinessType, FinancialInputs
from ideastress.finance.engine import compute_payment_fee_per_unit, q2, validate_financial_inputs
from ideastress.finance.montecarlo import run_monte_carlo


class FixPrescription(BaseModel):
    lever: str  # price_raise | churn_reduction | acq_spend_cap | annual_prepay_plan
    title: str
    current_value: str
    target_value: str
    resulting_survival_pct: Decimal
    resulting_p10_min_cash: Decimal
    achievable: bool
    summary: str


class AutoFixReport(BaseModel):
    currency: str
    baseline_survival_pct: Decimal
    baseline_p10_min_cash: Decimal
    target_survival_pct: Decimal
    already_healthy: bool
    prescriptions: List[FixPrescription]
    best_single_lever: Optional[str] = None


def _copy_inputs(inputs: FinancialInputs, **updates) -> FinancialInputs:
    d = inputs.dict()
    d.update(updates)
    return FinancialInputs(**d)


def _simulate_annual_prepay_survival(
    inputs: FinancialInputs,
    *,
    annual_adoption_pct: float = 0.25,
    annual_discount_pct: float = 0.20,
    simulations: int = 1000,
    seed: int = 42,
) -> tuple[Decimal, Decimal]:
    """Simulate SaaS survival when `annual_adoption_pct` of new buyers prepay 12m upfront at a discount."""
    rng = np.random.default_rng(seed)
    fee = float(compute_payment_fee_per_unit(inputs))
    base_var = float(inputs.variable_cost_per_unit) * (1.0 + float(inputs.us_payroll_tax_burden_pct)) + fee
    unit_price = float(inputs.unit_price)
    refund = float(inputs.refund_rate)
    tax_rate = float(inputs.effective_tax_rate)
    fixed = float(inputs.fixed_monthly_costs)
    base_new = inputs.monthly_new_customers
    base_spend = float(inputs.monthly_acquisition_spend)
    base_churn = float(inputs.monthly_churn_rate)

    cash = np.full(simulations, float(inputs.starting_cash), dtype=np.float64)
    min_cash = np.full(simulations, float(inputs.starting_cash), dtype=np.float64)
    active_monthly = np.full(simulations, float(inputs.starting_customers), dtype=np.float64)
    active_annual = np.zeros(simulations, dtype=np.float64)

    cac_mult = np.clip(rng.lognormal(mean=0.05, sigma=0.22, size=simulations), 0.65, 2.40)
    churn_mult = np.clip(rng.normal(loc=1.02, scale=0.20, size=simulations), 0.50, 2.20)

    annual_upfront = unit_price * 12.0 * (1.0 - annual_discount_pct) * (1.0 - refund)
    monthly_net = unit_price * (1.0 - refund)

    for m in range(1, inputs.horizon_months + 1):
        new_total = np.maximum(0.0, np.round(rng.normal(loc=base_new, scale=max(1.0, base_new * 0.22), size=simulations)))
        new_ann = np.round(new_total * annual_adoption_pct)
        new_mo = np.maximum(0.0, new_total - new_ann)

        spike = 1.35 if m == 1 else (1.15 if m == 2 else 1.0)
        m_churn = np.clip(base_churn * churn_mult * spike, 0.0, 0.90)
        active_monthly = np.maximum(0.0, active_monthly - np.round(active_monthly * m_churn)) + new_mo
        active_annual = active_annual + new_ann

        cash_in = active_monthly * monthly_net + new_ann * annual_upfront
        cogs = (active_monthly + active_annual) * base_var
        ebt = cash_in - cogs - fixed - base_spend * cac_mult
        taxes = np.where(ebt > 0.0, ebt * tax_rate, 0.0)
        cash = cash + (ebt - taxes)
        min_cash = np.minimum(min_cash, cash)

    surv = q2(Decimal(str(float(np.mean(min_cash >= 0.0)) * 100.0)))
    p10_min = q2(Decimal(str(float(np.percentile(min_cash, 10)))))
    return surv, p10_min


def generate_autofix_prescriptions(
    inputs: FinancialInputs,
    *,
    target_survival_pct: Decimal = Decimal("85.00"),
    simulations: int = 1000,
    seed: int = 42,
) -> AutoFixReport:
    """Compute exact minimum adjustments across 4 levers to reach `target_survival_pct`."""
    validate_financial_inputs(inputs)
    cur = inputs.currency.upper()
    base_mc = run_monte_carlo(inputs, simulations=simulations, seed=seed)

    if base_mc.survival_probability_pct >= target_survival_pct:
        return AutoFixReport(
            currency=cur,
            baseline_survival_pct=base_mc.survival_probability_pct,
            baseline_p10_min_cash=base_mc.p10_min_cash,
            target_survival_pct=target_survival_pct,
            already_healthy=True,
            prescriptions=[],
            best_single_lever=None,
        )

    prescriptions: List[FixPrescription] = []

    # Lever 1: Binary search minimum unit price
    lo_p = inputs.unit_price
    hi_p = max(inputs.unit_price * Decimal("8"), Decimal("2000"))
    hi_mc = run_monte_carlo(_copy_inputs(inputs, unit_price=hi_p), simulations=simulations, seed=seed)
    if hi_mc.survival_probability_pct >= target_survival_pct:
        for _ in range(18):
            mid = q2((lo_p + hi_p) / Decimal("2"))
            mc_m = run_monte_carlo(_copy_inputs(inputs, unit_price=mid), simulations=simulations, seed=seed)
            if mc_m.survival_probability_pct >= target_survival_pct:
                hi_p = mid
                hi_mc = mc_m
            else:
                lo_p = mid
        prescriptions.append(
            FixPrescription(
                lever="price_raise",
                title="Raise Unit Price",
                current_value=f"{cur} {inputs.unit_price}",
                target_value=f"{cur} {hi_p}",
                resulting_survival_pct=hi_mc.survival_probability_pct,
                resulting_p10_min_cash=hi_mc.p10_min_cash,
                achievable=True,
                summary=f"Raising price from {cur} {inputs.unit_price} to {cur} {hi_p} lifts 12m survival from {base_mc.survival_probability_pct}% to {hi_mc.survival_probability_pct}%.",
            )
        )

    # Lever 2: Churn reduction (SaaS only)
    if inputs.business_type == BusinessType.SAAS and inputs.monthly_churn_rate > Decimal("0.01"):
        zero_c_mc = run_monte_carlo(_copy_inputs(inputs, monthly_churn_rate=Decimal("0.005")), simulations=simulations, seed=seed)
        if zero_c_mc.survival_probability_pct >= target_survival_pct:
            lo_c = Decimal("0.005")
            hi_c = inputs.monthly_churn_rate
            best_mc = zero_c_mc
            for _ in range(16):
                mid_c = (lo_c + hi_c) / Decimal("2")
                mc_c = run_monte_carlo(_copy_inputs(inputs, monthly_churn_rate=mid_c), simulations=simulations, seed=seed)
                if mc_c.survival_probability_pct >= target_survival_pct:
                    lo_c = mid_c
                    best_mc = mc_c
                else:
                    hi_c = mid_c
            cur_pct = q2(inputs.monthly_churn_rate * Decimal("100"))
            tgt_pct = q2(lo_c * Decimal("100"))
            prescriptions.append(
                FixPrescription(
                    lever="churn_reduction",
                    title="Cut Monthly Churn",
                    current_value=f"{cur_pct}%/mo",
                    target_value=f"{tgt_pct}%/mo",
                    resulting_survival_pct=best_mc.survival_probability_pct,
                    resulting_p10_min_cash=best_mc.p10_min_cash,
                    achievable=True,
                    summary=f"Cutting monthly churn from {cur_pct}% to {tgt_pct}% raises survival to {best_mc.survival_probability_pct}%.",
                )
            )

    # Lever 3: Cap monthly acquisition spend
    if inputs.monthly_acquisition_spend > Decimal("0"):
        zero_sp_mc = run_monte_carlo(_copy_inputs(inputs, monthly_acquisition_spend=Decimal("0")), simulations=simulations, seed=seed)
        if zero_sp_mc.survival_probability_pct >= target_survival_pct:
            lo_s = Decimal("0")
            hi_s = inputs.monthly_acquisition_spend
            best_sp_mc = zero_sp_mc
            for _ in range(16):
                mid_s = q2((lo_s + hi_s) / Decimal("2"))
                mc_s = run_monte_carlo(_copy_inputs(inputs, monthly_acquisition_spend=mid_s), simulations=simulations, seed=seed)
                if mc_s.survival_probability_pct >= target_survival_pct:
                    lo_s = mid_s
                    best_sp_mc = mc_s
                else:
                    hi_s = mid_s
            prescriptions.append(
                FixPrescription(
                    lever="acq_spend_cap",
                    title="Cap Monthly Ad Spend",
                    current_value=f"{cur} {inputs.monthly_acquisition_spend}/mo",
                    target_value=f"{cur} {lo_s}/mo",
                    resulting_survival_pct=best_sp_mc.survival_probability_pct,
                    resulting_p10_min_cash=best_sp_mc.p10_min_cash,
                    achievable=True,
                    summary=f"Capping paid spend from {cur} {inputs.monthly_acquisition_spend}/mo to {cur} {lo_s}/mo lifts survival to {best_sp_mc.survival_probability_pct}%.",
                )
            )

    # Lever 4: Annual Prepay Plan (25% adoption at 20% off) for SaaS
    if inputs.business_type == BusinessType.SAAS:
        ann_surv, ann_p10_min = _simulate_annual_prepay_survival(inputs, simulations=simulations, seed=seed)
        prescriptions.append(
            FixPrescription(
                lever="annual_prepay_plan",
                title="Add Annual Prepay Plan (20% Off, 25% Adoption)",
                current_value="Monthly billing only",
                target_value="25% annual upfront",
                resulting_survival_pct=ann_surv,
                resulting_p10_min_cash=ann_p10_min,
                achievable=ann_surv >= target_survival_pct,
                summary=(
                    f"Collecting 12m upfront (20% off) from 25% of new buyers moves survival from "
                    f"{base_mc.survival_probability_pct}% to {ann_surv}% (P10 cash trough: {cur} {ann_p10_min:,.0f})."
                ),
            )
        )

    achievable = [p for p in prescriptions if p.achievable]
    best_lever = achievable[0].lever if achievable else (prescriptions[0].lever if prescriptions else None)

    return AutoFixReport(
        currency=cur,
        baseline_survival_pct=base_mc.survival_probability_pct,
        baseline_p10_min_cash=base_mc.p10_min_cash,
        target_survival_pct=target_survival_pct,
        already_healthy=False,
        prescriptions=prescriptions,
        best_single_lever=best_lever,
    )
