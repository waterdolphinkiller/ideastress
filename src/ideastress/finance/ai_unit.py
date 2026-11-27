"""AI Wrapper Token Cost, Gross Margin & Power-User Bankruptcy Stress-Tester.

Solves a critical 2026 SaaS problem: AI-heavy apps often quote 80% traditional SaaS
margins while ignoring LLM token COGS and heavy power-user ("whale") loss risk.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Dict, Optional

from pydantic import BaseModel

from ideastress.finance.engine import q2

# Illustrative per-1M-token USD pricing presets (user can override with exact current model rates)
MODEL_TOKEN_PRESETS: Dict[str, tuple[Decimal, Decimal, str]] = {
    "budget_fast": (Decimal("0.15"), Decimal("0.60"), "Fast/Mini tier ($0.15 in / $0.60 out per 1M tokens)"),
    "mid_balanced": (Decimal("1.25"), Decimal("5.00"), "Mid/Balanced tier ($1.25 in / $5.00 out per 1M tokens)"),
    "frontier_reasoning": (Decimal("3.00"), Decimal("15.00"), "Frontier tier ($3.00 in / $15.00 out per 1M tokens)"),
}


class AITokenMarginInputs(BaseModel):
    subscription_price_usd: Decimal
    daily_requests_per_user: int = 20
    avg_input_tokens: int = 2500
    avg_output_tokens: int = 800
    model_preset: str = "mid_balanced"
    custom_input_per_1m_usd: Optional[Decimal] = None
    custom_output_per_1m_usd: Optional[Decimal] = None
    include_stripe_us_fee: bool = True
    other_monthly_infra_per_user_usd: Decimal = Decimal("1.00")


class AITokenMarginResult(BaseModel):
    subscription_price_usd: Decimal
    cost_per_request_usd: Decimal
    monthly_ai_cogs_per_user_usd: Decimal
    stripe_fee_usd: Decimal
    total_variable_cost_per_user_usd: Decimal
    monthly_gross_profit_per_user_usd: Decimal
    gross_margin_pct: Decimal
    whale_break_even_daily_requests: Optional[int] = None
    verdict: str  # HEALTHY_AI_MARGIN | COMPRESSED_MARGIN | NEGATIVE_UNIT_MARGIN
    warning: str


def stress_test_ai_token_margin(inputs: AITokenMarginInputs) -> AITokenMarginResult:
    """Compute exact monthly AI inference COGS, net margin, and power-user bankruptcy threshold."""
    if inputs.custom_input_per_1m_usd is not None and inputs.custom_output_per_1m_usd is not None:
        in_rate = inputs.custom_input_per_1m_usd
        out_rate = inputs.custom_output_per_1m_usd
    else:
        in_rate, out_rate, _ = MODEL_TOKEN_PRESETS.get(
            inputs.model_preset, MODEL_TOKEN_PRESETS["mid_balanced"]
        )

    one_m = Decimal("1000000")
    cost_per_req = (Decimal(inputs.avg_input_tokens) / one_m) * in_rate + (
        Decimal(inputs.avg_output_tokens) / one_m
    ) * out_rate
    monthly_reqs = Decimal(inputs.daily_requests_per_user * 30)
    monthly_ai_cogs = q2(cost_per_req * monthly_reqs)

    stripe_fee = (
        q2(inputs.subscription_price_usd * Decimal("0.029") + Decimal("0.30"))
        if inputs.include_stripe_us_fee
        else Decimal("0.00")
    )
    total_var = q2(monthly_ai_cogs + stripe_fee + inputs.other_monthly_infra_per_user_usd)
    gp = q2(inputs.subscription_price_usd - total_var)
    gm_pct = q2((gp / inputs.subscription_price_usd) * Decimal("100")) if inputs.subscription_price_usd > 0 else Decimal("0.00")

    # Whale bankruptcy threshold: how many daily requests before this user loses money?
    net_budget_for_tokens = inputs.subscription_price_usd - stripe_fee - inputs.other_monthly_infra_per_user_usd
    if cost_per_req > Decimal("0") and net_budget_for_tokens > Decimal("0"):
        whale_daily = int(math.floor(float((net_budget_for_tokens / cost_per_req) / Decimal("30"))))
    else:
        whale_daily = 0

    if gp <= Decimal("0"):
        verdict = "NEGATIVE_UNIT_MARGIN"
        warning = (
            f"UNVIABLE AI PRICING: Average user costs ${total_var}/mo vs ${inputs.subscription_price_usd}/mo price. "
            "Add usage caps, credit packs, or route routine prompts to a cheaper model tier."
        )
    elif gm_pct < Decimal("60.00"):
        verdict = "COMPRESSED_MARGIN"
        warning = (
            f"COMPRESSED AI MARGIN ({gm_pct}% vs 80% SaaS median): Any power user exceeding "
            f"{whale_daily} requests/day turns unprofitable. Enforce rate limits or tiered credits."
        )
    else:
        verdict = "HEALTHY_AI_MARGIN"
        warning = (
            f"HEALTHY MARGIN ({gm_pct}%): Safe up to {whale_daily} daily requests/user before turning unprofitable."
        )

    return AITokenMarginResult(
        subscription_price_usd=q2(inputs.subscription_price_usd),
        cost_per_request_usd=cost_per_req.quantize(Decimal("0.00001")),
        monthly_ai_cogs_per_user_usd=monthly_ai_cogs,
        stripe_fee_usd=stripe_fee,
        total_variable_cost_per_user_usd=total_var,
        monthly_gross_profit_per_user_usd=gp,
        gross_margin_pct=gm_pct,
        whale_break_even_daily_requests=whale_daily,
        verdict=verdict,
        warning=warning,
    )
