"""Reverse Unit-Economics Solver (Goal-Seek Mathematical Survival Frontier).

Instead of only asking "If my guesses are right, how much will I make?",
this solver computes the HARD MATHEMATICAL CEILINGS & FLOORS required to
survive the planning horizon without running out of cash:
  - Maximum viable CAC
  - Minimum viable Unit Price
  - Maximum tolerable monthly churn (SaaS)
  - Minimum monthly new customers required to survive
  - Required conversion rate (when visitor volume is known)

These exact numbers are fed directly into the Independent Red Team and Decision Gate.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from ideastress.domain.models import BusinessType, FinancialInputs, ReverseFrontier
from ideastress.finance.engine import q2, run_scenario, validate_financial_inputs


def _copy_inputs(inputs: FinancialInputs, **updates) -> FinancialInputs:
    data = inputs.dict()
    data.update(updates)
    return FinancialInputs(**data)


def _survives(inputs: FinancialInputs) -> bool:
    sim = run_scenario(inputs, scenario_name="solver_probe")
    return sim.min_cash_balance >= Decimal("0")


def _solve_max_cac(inputs: FinancialInputs) -> Optional[Decimal]:
    """Binary search maximum sustainable CAC (per new customer) that keeps cash >= 0."""
    new_cust = inputs.monthly_new_customers
    if inputs.monthly_visitors and inputs.conversion_rate:
        new_cust = max(1, int(Decimal(inputs.monthly_visitors) * inputs.conversion_rate))
    if new_cust <= 0:
        return None

    # Check if even CAC = 0 survives
    zero_cac_inputs = _copy_inputs(inputs, monthly_acquisition_spend=Decimal("0"), observed_cac=Decimal("0"))
    if not _survives(zero_cac_inputs):
        return Decimal("0.00")

    lo = Decimal("0")
    hi = max(Decimal("10000"), inputs.unit_price * Decimal("24"))
    for _ in range(36):
        mid = (lo + hi) / Decimal("2")
        probe = _copy_inputs(
            inputs,
            monthly_acquisition_spend=mid * Decimal(new_cust),
            observed_cac=mid,
        )
        if _survives(probe):
            lo = mid
        else:
            hi = mid
    return q2(lo)


def _solve_min_price(inputs: FinancialInputs) -> Optional[Decimal]:
    """Binary search minimum unit price required to keep cash >= 0 over horizon."""
    lo = Decimal("0.01")
    hi = max(inputs.unit_price * Decimal("10"), Decimal("50000"))

    if not _survives(_copy_inputs(inputs, unit_price=hi)):
        return None

    for _ in range(36):
        mid = (lo + hi) / Decimal("2")
        if _survives(_copy_inputs(inputs, unit_price=mid)):
            hi = mid
        else:
            lo = mid
    return q2(hi)


def _solve_max_churn_pct(inputs: FinancialInputs) -> Optional[Decimal]:
    """Binary search maximum tolerable monthly churn (%) for SaaS to survive horizon."""
    if inputs.business_type != BusinessType.SAAS:
        return None
    if not _survives(_copy_inputs(inputs, monthly_churn_rate=Decimal("0.0001"))):
        return Decimal("0.00")
    if _survives(_copy_inputs(inputs, monthly_churn_rate=Decimal("0.90"))):
        return Decimal("90.00")

    lo = Decimal("0.0001")
    hi = Decimal("0.90")
    for _ in range(32):
        mid = (lo + hi) / Decimal("2")
        if _survives(_copy_inputs(inputs, monthly_churn_rate=mid)):
            lo = mid
        else:
            hi = mid
    return q2(lo * Decimal("100"))


def _solve_min_monthly_customers(inputs: FinancialInputs) -> Optional[int]:
    """Binary search minimum monthly new customers required to avoid running out of cash."""
    # Hold fixed costs & acquisition spend constant while varying customer count
    probe_base = _copy_inputs(inputs, monthly_visitors=None, conversion_rate=None, observed_conversion_rate=None)
    if _survives(_copy_inputs(probe_base, monthly_new_customers=0)):
        return 0

    lo, hi = 1, 100000
    if not _survives(_copy_inputs(probe_base, monthly_new_customers=hi)):
        return None

    while lo < hi:
        mid = (lo + hi) // 2
        if _survives(_copy_inputs(probe_base, monthly_new_customers=mid)):
            hi = mid
        else:
            lo = mid + 1
    return lo


def solve_reverse_frontier(inputs: FinancialInputs) -> ReverseFrontier:
    """Compute the complete mathematical survival frontier for a business idea."""
    validate_financial_inputs(inputs)

    base = run_scenario(inputs, scenario_name="frontier_base")
    max_cac = _solve_max_cac(inputs)
    min_price = _solve_min_price(inputs)
    max_churn_pct = _solve_max_churn_pct(inputs)
    min_customers = _solve_min_monthly_customers(inputs)

    max_cac_3x: Optional[Decimal] = None
    if base.ltv is not None and base.ltv > Decimal("0"):
        max_cac_3x = q2(base.ltv / Decimal("3"))

    req_cvr_pct: Optional[Decimal] = None
    if inputs.monthly_visitors and inputs.monthly_visitors > 0 and min_customers is not None:
        req_cvr_pct = q2((Decimal(min_customers) / Decimal(inputs.monthly_visitors)) * Decimal("100"))

    impossibility_reasons: List[str] = []
    hard_rules: List[str] = []

    if base.unit_contribution_margin <= Decimal("0"):
        impossibility_reasons.append(
            f"Negative or zero unit contribution margin ({inputs.currency} {base.unit_contribution_margin}): "
            "selling more units loses more money."
        )
    if max_cac is not None and max_cac <= Decimal("0"):
        impossibility_reasons.append(
            "Zero CAC headroom: even with $0 acquisition spend, the business runs out of cash before month "
            f"{inputs.horizon_months}."
        )
    if min_customers is None:
        impossibility_reasons.append(
            "No feasible customer acquisition volume (up to 100,000/mo) prevents cash exhaustion under current margins."
        )
    if req_cvr_pct is not None and req_cvr_pct > Decimal("15.0"):
        impossibility_reasons.append(
            f"Requires an unrealistic {req_cvr_pct}% visitor-to-paid conversion rate on {inputs.monthly_visitors:,} monthly visitors."
        )

    # Build hard mathematical rules for Red Team to stress-test against real-world channels
    if max_cac is not None:
        hard_rules.append(
            f"CAC Ceiling: To survive {inputs.horizon_months} months on {inputs.currency} {inputs.starting_cash:,.0f} cash, "
            f"real CAC must stay <= {inputs.currency} {max_cac:,.2f}."
        )
    if max_cac_3x is not None:
        hard_rules.append(
            f"3:1 LTV:CAC Ceiling: To hit healthy SaaS unit economics, CAC must stay <= {inputs.currency} {max_cac_3x:,.2f}."
        )
    if min_price is not None:
        hard_rules.append(
            f"Price Floor: Minimum viable unit price to avoid cash depletion is {inputs.currency} {min_price:,.2f}."
        )
    if max_churn_pct is not None:
        hard_rules.append(
            f"Churn Ceiling: Monthly customer churn cannot exceed {max_churn_pct:.2f}%."
        )
    if min_customers is not None:
        hard_rules.append(
            f"Volume Floor: Must acquire at least {min_customers:,} new paying customers/month."
        )

    # Determine mathematical verdict
    if impossibility_reasons:
        math_verdict = "UNIT_ECONOMICS_IMPOSSIBLE"
    else:
        tight_signals = 0
        if base.min_cash_balance < inputs.starting_cash * Decimal("0.20"):
            tight_signals += 1
        if max_cac is not None and base.cac is not None and max_cac < base.cac * Decimal("1.25"):
            tight_signals += 1
        if max_churn_pct is not None and max_churn_pct < Decimal("6.0"):
            tight_signals += 1
        if min_price is not None and inputs.unit_price < min_price * Decimal("1.15"):
            tight_signals += 1
        math_verdict = "TIGHT_FRONTIER" if tight_signals >= 2 else "VIABLE_FRONTIER"

    return ReverseFrontier(
        currency=inputs.currency.upper(),
        horizon_months=inputs.horizon_months,
        max_viable_cac=max_cac,
        max_cac_for_3x_ltv=max_cac_3x,
        min_viable_unit_price=min_price,
        max_tolerable_monthly_churn_pct=max_churn_pct,
        min_monthly_new_customers_to_survive=min_customers,
        required_conversion_rate_pct=req_cvr_pct,
        mathematical_verdict=math_verdict,
        impossibility_reasons=impossibility_reasons,
        hard_rules_for_red_team=hard_rules,
    )
