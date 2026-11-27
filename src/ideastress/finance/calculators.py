"""Additional deterministic startup calculators for IdeaStress v0.8.0:
  1. Quit-Your-Job MRR & US Solo Founder Take-Home + Stripe vs. MoR Comparator
  2. Freemium Economics & Free-User Drag Stress-Tester
  3. Meta / TikTok Paid Social CPM -> CTR -> CVR -> CPA Funnel Falsifier
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from ideastress.finance.engine import q2


class QuitJobMRRResult(BaseModel):
    target_annual_take_home_usd: Decimal
    required_monthly_pre_tax_profit_usd: Decimal
    required_mrr_usd: Decimal
    required_paying_customers: int
    annual_stripe_fees_usd: Decimal
    annual_mor_fees_usd: Decimal
    annual_fee_savings_with_stripe_usd: Decimal


def solve_quit_job_mrr(
    *,
    target_annual_salary_usd: Decimal,
    effective_tax_rate: Decimal = Decimal("0.30"),
    monthly_operating_costs_usd: Decimal = Decimal("1500"),
    unit_price_usd: Decimal = Decimal("49"),
    payment_processor: str = "stripe_us",
) -> QuitJobMRRResult:
    """Compute exact MRR and customer count needed to replace a target annual salary after US taxes & fees."""
    monthly_target_net = target_annual_salary_usd / Decimal("12")
    tax_divisor = max(Decimal("0.10"), Decimal("1") - effective_tax_rate)
    req_pre_tax_profit = monthly_target_net / tax_divisor

    fee_pct = Decimal("0.050") if payment_processor == "mor_paddle" else Decimal("0.029")
    fee_flat = Decimal("0.50") if payment_processor == "mor_paddle" else Decimal("0.30")

    net_per_cust = unit_price_usd * (Decimal("1") - fee_pct) - fee_flat
    if net_per_cust <= Decimal("0"):
        raise ValueError("Unit price is too low to cover payment processing fees.")

    needed_monthly_rev_after_fees = req_pre_tax_profit + monthly_operating_costs_usd
    req_customers = int(math.ceil(float(needed_monthly_rev_after_fees / net_per_cust)))
    req_mrr = q2(Decimal(req_customers) * unit_price_usd)

    ann_stripe = q2(Decimal(req_customers) * (unit_price_usd * Decimal("0.029") + Decimal("0.30")) * Decimal("12"))
    ann_mor = q2(Decimal(req_customers) * (unit_price_usd * Decimal("0.050") + Decimal("0.50")) * Decimal("12"))

    return QuitJobMRRResult(
        target_annual_take_home_usd=q2(target_annual_salary_usd),
        required_monthly_pre_tax_profit_usd=q2(req_pre_tax_profit),
        required_mrr_usd=req_mrr,
        required_paying_customers=req_customers,
        annual_stripe_fees_usd=ann_stripe,
        annual_mor_fees_usd=ann_mor,
        annual_fee_savings_with_stripe_usd=q2(ann_mor - ann_stripe),
    )


class FreemiumEconomicsResult(BaseModel):
    monthly_free_users: int
    monthly_paid_users: int
    monthly_paid_revenue_usd: Decimal
    monthly_free_tier_drag_usd: Decimal
    monthly_net_gross_profit_usd: Decimal
    blended_gross_margin_pct: Decimal
    min_conversion_rate_to_break_even_pct: Optional[Decimal] = None
    verdict: str  # FREEMIUM_HEALTHY | FREEMIUM_COMPRESSED | FREEMIUM_BLEEDING


def evaluate_freemium_economics(
    *,
    total_monthly_active_users: int,
    free_to_paid_conversion_rate: Decimal,
    paid_price_usd: Decimal,
    monthly_cost_per_free_user_usd: Decimal,
    monthly_cost_per_paid_user_usd: Decimal,
) -> FreemiumEconomicsResult:
    """Stress-test whether free-tier infrastructure/AI costs overwhelm paid subscription revenue."""
    paid_users = int(round(total_monthly_active_users * float(free_to_paid_conversion_rate)))
    free_users = max(0, total_monthly_active_users - paid_users)

    paid_rev = q2(Decimal(paid_users) * paid_price_usd)
    free_drag = q2(Decimal(free_users) * monthly_cost_per_free_user_usd)
    paid_cogs = q2(Decimal(paid_users) * (monthly_cost_per_paid_user_usd + paid_price_usd * Decimal("0.029") + Decimal("0.30")))
    net_gp = q2(paid_rev - free_drag - paid_cogs)
    gm_pct = q2((net_gp / paid_rev) * Decimal("100")) if paid_rev > Decimal("0") else Decimal("-100.00")

    unit_paid_contrib = paid_price_usd * Decimal("0.971") - Decimal("0.30") - monthly_cost_per_paid_user_usd
    denom = unit_paid_contrib + monthly_cost_per_free_user_usd
    min_cvr_pct: Optional[Decimal] = None
    if denom > Decimal("0") and unit_paid_contrib > Decimal("0"):
        min_cvr_pct = q2((monthly_cost_per_free_user_usd / denom) * Decimal("100"))

    if net_gp <= Decimal("0"):
        verdict = "FREEMIUM_BLEEDING"
    elif gm_pct < Decimal("60.00"):
        verdict = "FREEMIUM_COMPRESSED"
    else:
        verdict = "FREEMIUM_HEALTHY"

    return FreemiumEconomicsResult(
        monthly_free_users=free_users,
        monthly_paid_users=paid_users,
        monthly_paid_revenue_usd=paid_rev,
        monthly_free_tier_drag_usd=free_drag,
        monthly_net_gross_profit_usd=net_gp,
        blended_gross_margin_pct=gm_pct,
        min_conversion_rate_to_break_even_pct=min_cvr_pct,
        verdict=verdict,
    )


class PaidSocialFunnelResult(BaseModel):
    effective_cpc_usd: Decimal
    implied_cpa_usd: Decimal
    pre_ad_margin_usd: Decimal
    break_even_roas: Optional[Decimal] = None
    net_profit_per_order_usd: Decimal
    verdict: str  # SOCIAL_VIABLE | SOCIAL_UNPROFITABLE


def evaluate_paid_social_cpm(
    *,
    cpm_usd: Decimal,
    ctr_pct: Decimal,
    landing_cvr_pct: Decimal,
    aov_usd: Decimal,
    pre_ad_margin_pct: Decimal,
) -> PaidSocialFunnelResult:
    """Evaluate Meta / TikTok paid social funnel from CPM -> CTR -> CVR -> CPA."""
    ctr = ctr_pct / Decimal("100")
    cvr = landing_cvr_pct / Decimal("100")
    clicks_per_1k = Decimal("1000") * ctr
    eff_cpc = q2(cpm_usd / clicks_per_1k) if clicks_per_1k > 0 else Decimal("999.99")
    implied_cpa = q2(eff_cpc / cvr) if cvr > 0 else Decimal("9999.99")
    pre_ad_margin = q2(aov_usd * (pre_ad_margin_pct / Decimal("100")))
    be_roas = q2(aov_usd / pre_ad_margin) if pre_ad_margin > 0 else None
    net_profit = q2(pre_ad_margin - implied_cpa)
    verdict = "SOCIAL_VIABLE" if net_profit >= Decimal("0") else "SOCIAL_UNPROFITABLE"

    return PaidSocialFunnelResult(
        effective_cpc_usd=eff_cpc,
        implied_cpa_usd=implied_cpa,
        pre_ad_margin_usd=pre_ad_margin,
        break_even_roas=be_roas,
        net_profit_per_order_usd=net_profit,
        verdict=verdict,
    )
