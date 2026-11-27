"""Scope-Creep FinOps Gate for Coding Agents (Claude Code / Cursor / Codex).

Before a developer or AI coding agent adds an expensive feature (e.g., multimodal video,
real-time voice, heavy third-party APIs), this deterministic gate checks how the extra
per-user monthly COGS impacts gross margin and 1,000-run Monte Carlo survival probability.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from ideastress.domain.models import FinancialInputs
from ideastress.finance.engine import q2, run_scenario
from ideastress.finance.montecarlo import run_monte_carlo


class ScopeCreepResult(BaseModel):
    feature_name: str
    extra_monthly_cogs_per_user: Decimal
    before_gross_margin_pct: Optional[Decimal] = None
    after_gross_margin_pct: Optional[Decimal] = None
    before_survival_pct: Decimal
    after_survival_pct: Decimal
    recommended_addon_price: Decimal
    verdict: str  # APPROVE_IN_BASE_PLAN | MOVE_TO_PAID_ADDON | BLOCK_SCOPE_CREEP
    explanation: str


def check_scope_creep_finops(
    base_inputs: FinancialInputs,
    *,
    feature_name: str,
    extra_monthly_cogs_per_user: Decimal,
    extra_fixed_monthly_cost: Decimal = Decimal("0"),
) -> ScopeCreepResult:
    """Evaluate whether a proposed feature breaks unit economics or requires a paid add-on."""
    before_sim = run_scenario(base_inputs, "before_feature")
    before_mc = run_monte_carlo(base_inputs, simulations=1000, seed=42)

    after_data = base_inputs.dict()
    after_data["variable_cost_per_unit"] = base_inputs.variable_cost_per_unit + extra_monthly_cogs_per_user
    after_data["fixed_monthly_costs"] = base_inputs.fixed_monthly_costs + extra_fixed_monthly_cost
    after_inputs = FinancialInputs(**after_data)

    after_sim = run_scenario(after_inputs, "after_feature")
    after_mc = run_monte_carlo(after_inputs, simulations=1000, seed=42)

    # Price required to preserve a 75% gross margin on the add-on itself
    addon_price = q2(extra_monthly_cogs_per_user * Decimal("4")) if extra_monthly_cogs_per_user > 0 else Decimal("0.00")

    gm_after = after_sim.gross_margin_pct or Decimal("0")
    surv_drop = before_mc.survival_probability_pct - after_mc.survival_probability_pct

    if after_sim.unit_contribution_margin <= Decimal("0") or after_mc.survival_probability_pct < Decimal("50.00"):
        verdict = "BLOCK_SCOPE_CREEP"
        explanation = (
            f"BLOCK '{feature_name}': Adding {base_inputs.currency} {extra_monthly_cogs_per_user}/user COGS "
            f"collapses gross margin to {gm_after}% and drops 12m survival from {before_mc.survival_probability_pct}% to {after_mc.survival_probability_pct}%. "
            f"Cut feature or gate behind a +{base_inputs.currency} {addon_price}/mo add-on."
        )
    elif gm_after < Decimal("60.00") or surv_drop >= Decimal("10.00"):
        verdict = "MOVE_TO_PAID_ADDON"
        explanation = (
            f"GATE '{feature_name}' AS ADD-ON: Margin drops from {before_sim.gross_margin_pct}% to {gm_after}% "
            f"(survival {before_mc.survival_probability_pct}% -> {after_mc.survival_probability_pct}%). "
            f"Charge +{base_inputs.currency} {addon_price}/mo to protect 75% margin."
        )
    else:
        verdict = "APPROVE_IN_BASE_PLAN"
        explanation = (
            f"APPROVE '{feature_name}': Gross margin stays healthy at {gm_after}% and 12m survival holds at {after_mc.survival_probability_pct}%."
        )

    return ScopeCreepResult(
        feature_name=feature_name,
        extra_monthly_cogs_per_user=q2(extra_monthly_cogs_per_user),
        before_gross_margin_pct=before_sim.gross_margin_pct,
        after_gross_margin_pct=after_sim.gross_margin_pct,
        before_survival_pct=before_mc.survival_probability_pct,
        after_survival_pct=after_mc.survival_probability_pct,
        recommended_addon_price=addon_price,
        verdict=verdict,
        explanation=explanation,
    )
