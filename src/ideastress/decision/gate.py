"""Deterministic Decision Gate & Kill-Test Generator.

Never averages arbitrary AI scores. Applies explicit, inspectable blocking rules
from the Reverse Unit-Economics Frontier, Base Rate Checks, Evidence Audit, and Red Team.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List

from ideastress.domain.models import (
    AnalysisRequest,
    AuditReport,
    ChannelFalsificationResult,
    BaseRateCheck,
    Claim,
    ClaimStatus,
    Competitor,
    DecisionSummary,
    DimensionScore,
    FinancialAnalysis,
    KillTest,
    RedTeamReport,
    RiskItem,
    Verdict,
)


def evaluate_decision_gate(
    request: AnalysisRequest,
    financials: FinancialAnalysis,
    base_rate_checks: List[BaseRateCheck],
    claims: List[Claim],
    competitors: List[Competitor],
    risks: List[RiskItem],
    red_team: RedTeamReport,
    audit: AuditReport,
    channel_falsification: ChannelFalsificationResult | None = None,
) -> DecisionSummary:
    """Compute final GO / CONDITIONAL_GO / PIVOT / NO_GO / INSUFFICIENT_DATA verdict."""
    base = financials.scenarios["base"]
    cons = financials.scenarios["conservative"]
    frontier = financials.reverse_frontier

    blocking_conditions: List[str] = []
    reasons: List[str] = []
    critical_unknowns: List[str] = []

    # 0. Paid channel CPC falsification blocker
    if channel_falsification is not None and channel_falsification.verdict == 'CHANNEL_IMPOSSIBLE':
        blocking_conditions.append(channel_falsification.explanation)

    # 1. Hard financial impossibility check
    if frontier.mathematical_verdict == "UNIT_ECONOMICS_IMPOSSIBLE":
        blocking_conditions.extend(frontier.impossibility_reasons)

    # 2. Evidence completeness & demand check
    verified_or_supported = [
        c for c in claims if c.status in (ClaimStatus.VERIFIED, ClaimStatus.SUPPORTED)
    ]
    contradicted = [c for c in claims if c.status == ClaimStatus.CONTRADICTED]
    unknown_claims = [c for c in claims if c.status == ClaimStatus.UNKNOWN]

    if not verified_or_supported:
        blocking_conditions.append("No verified or externally supported demand/market claims yet.")
    if contradicted:
        blocking_conditions.append(
            f"{len(contradicted)} key claim(s) have contradicting evidence that must be resolved."
        )
    for uc in unknown_claims[:3]:
        critical_unknowns.append(uc.statement)

    # 3. Base-rate outlier checks
    severe_outliers = [b for b in base_rate_checks if b.status == "SEVERE_OUTLIER"]
    opt_warnings = [b for b in base_rate_checks if b.status == "OPTIMISTIC_WARNING"]
    for s in severe_outliers:
        blocking_conditions.append(f"Severe base-rate outlier on {s.metric}: {s.user_value} vs {s.benchmark_value}.")

    # 4. Critical risks & customer clarity
    critical_risks = [r for r in risks if r.severity == "critical"]
    if not request.customer_segment:
        blocking_conditions.append("Target customer segment is unspecified; ICP must be narrowed before building.")
    if critical_risks:
        blocking_conditions.append(
            f"{len(critical_risks)} critical risk(s) identified (e.g., {critical_risks[0].title})."
        )

    # 5. Dimension breakdown (explicit, no single fake score)
    unit_econ_rating = (
        "weak"
        if frontier.mathematical_verdict == "UNIT_ECONOMICS_IMPOSSIBLE"
        else ("moderate" if frontier.mathematical_verdict == "TIGHT_FRONTIER" else "strong")
    )
    demand_rating = (
        "unknown"
        if not verified_or_supported
        else ("weak" if contradicted else ("strong" if len(verified_or_supported) >= 3 else "moderate"))
    )
    comp_rating = (
        "unknown"
        if not competitors
        else ("weak" if len(competitors) >= 5 else "moderate")
    )
    risk_rating = "weak" if critical_risks else ("moderate" if len(risks) >= 3 else "strong")

    dimensions = [
        DimensionScore(
            dimension="Unit Economics & Survival Frontier",
            rating=unit_econ_rating,
            rationale=(
                f"Frontier={frontier.mathematical_verdict}; Base ending cash={base.currency} {base.ending_cash_balance:,.2f}; "
                f"Max viable CAC={frontier.max_viable_cac}."
            ),
        ),
        DimensionScore(
            dimension="Demand & Evidence Coverage",
            rating=demand_rating,
            rationale=f"{len(verified_or_supported)} supported/verified claims, {len(contradicted)} contradicted, {len(unknown_claims)} unknown.",
        ),
        DimensionScore(
            dimension="Competitive Position",
            rating=comp_rating,
            rationale=f"{len(competitors)} competitor/substitute entries mapped across direct, indirect, and substitute tiers.",
        ),
        DimensionScore(
            dimension="Risk & Red-Team Exposure",
            rating=risk_rating,
            rationale=f"{len(critical_risks)} critical risks; {len(red_team.strongest_counterarguments)} Red Team counterarguments raised.",
        ),
    ]

    # 6. Verdict determination
    if frontier.mathematical_verdict == "UNIT_ECONOMICS_IMPOSSIBLE":
        verdict = Verdict.NO_GO
        headline = "Unit economics are mathematically unviable under current assumptions."
        reasons.append("Reverse Unit-Economics Solver proved cash exhaustion or negative unit contribution margin.")
        if frontier.min_viable_unit_price:
            reasons.append(
                f"Reaching survival requires raising price to at least {frontier.currency} {frontier.min_viable_unit_price:,.2f} "
                "or radically cutting variable/fixed costs."
            )
        next_action = "Do NOT write code or buy inventory yet. Re-price or restructure the business model and re-run `ideastress solve`."
    elif len(verified_or_supported) == 0 and len(competitors) == 0:
        verdict = Verdict.INSUFFICIENT_DATA
        headline = "Insufficient external evidence to issue a go/no-go decision."
        reasons.append("No externally verified demand or competitor evidence was retrieved.")
        next_action = "Run with a live Search Provider or supply customer interview / pricing evidence in your ledger."
    elif severe_outliers or (cons.min_cash_balance < Decimal("0") and base.min_cash_balance < Decimal("0")):
        verdict = Verdict.PIVOT
        headline = "Current pricing, channel, or cost structure is likely to fail under realistic base rates."
        reasons.append("Base-case cash runs negative or relies on severe outlier assumptions vs 2026 industry benchmarks.")
        if opt_warnings:
            reasons.append(f"{len(opt_warnings)} additional assumption(s) exceed industry medians.")
        next_action = "Pivot ICP, pricing tier, or acquisition channel, then run the top Kill Test before building."
    elif blocking_conditions or opt_warnings or cons.min_cash_balance < Decimal("0"):
        verdict = Verdict.CONDITIONAL_GO
        headline = "Viable unit-economics frontier, but critical real-world assumptions remain unvalidated."
        reasons.append(
            f"Base scenario survives with {base.currency} {base.ending_cash_balance:,.2f} ending cash "
            f"(max viable CAC: {frontier.currency} {frontier.max_viable_cac})."
        )
        if cons.min_cash_balance < Decimal("0"):
            reasons.append("Conservative downside scenario runs out of cash; validate CAC and churn early.")
        if red_team.decision_changing_conditions:
            critical_unknowns.append(red_team.decision_changing_conditions[0])
        next_action = "Execute the #1 lowest-cost Kill Test and feed real numbers back via `ideastress diff`."
    else:
        verdict = Verdict.GO
        headline = "Core unit economics and evidence support proceeding to MVP build."
        reasons.append("Both base and conservative scenarios stay cash-positive with aligned industry base rates.")
        next_action = "Proceed to scoped MVP while tracking real CAC and retention against the solved survival ceilings."

    if not critical_unknowns and red_team.critical_assumptions:
        critical_unknowns.extend(red_team.critical_assumptions[:2])

    return DecisionSummary(
        verdict=verdict,
        headline=headline,
        reasons=reasons,
        blocking_conditions=blocking_conditions,
        critical_unknowns=critical_unknowns,
        dimensions=dimensions,
        next_action=next_action,
    )


def generate_kill_tests(
    request: AnalysisRequest,
    financials: FinancialAnalysis,
    red_team: RedTeamReport,
) -> List[KillTest]:
    """Generate concrete, low-cost, threshold-bound falsification experiments."""
    frontier = financials.reverse_frontier
    cur = financials.currency
    seg = request.customer_segment or "target ICP buyers"
    max_cac_str = f"{cur} {frontier.max_viable_cac:,.2f}" if frontier.max_viable_cac is not None else "target CAC"

    tests: List[KillTest] = [
        KillTest(
            hypothesis=f"Paid acquisition can acquire {seg} at or below the mathematical CAC ceiling of {max_cac_str}.",
            target_segment=seg,
            method="smoke_test_landing_page_with_paid_intent",
            budget_estimate=min(Decimal("250"), max(Decimal("50"), request.budget * Decimal("0.05"))),
            currency=cur,
            duration_days=10,
            success_threshold=f">= 5% click-to-checkout-intent AND implied CAC <= {max_cac_str} across >= 200 qualified clicks.",
            failure_threshold=f"Implied CAC > 1.5x {max_cac_str} OR < 1.5% checkout/waitlist-with-card intent after 200 clicks.",
            sample_size_guidance="At least 200 targeted clicks from high-intent search or niche community placements (indicative, not statistical certainty).",
            measurement=["qualified_clicks", "cpc", "checkout_intent_clicks", "implied_cac"],
            decision_rule="If implied CAC exceeds the survival ceiling, pivot channel or raise unit price before writing production code.",
            limitations=["Click-to-intent overstates actual paid conversion; treat as an upper bound."],
        ),
        KillTest(
            hypothesis=f"{seg} already experience acute pain and pay (money or significant labor) for workarounds today.",
            target_segment=seg,
            method="customer_discovery_interviews",
            budget_estimate=Decimal("0"),
            currency=cur,
            duration_days=7,
            success_threshold=">= 8 of 15 qualified buyers paid for a competing tool, agency, or manual workaround in the last 30 days.",
            failure_threshold="< 4 of 15 can point to concrete past spend or weekly hours lost to this problem.",
            sample_size_guidance="15 structured interviews using past-behavior questions (Mom Test style; indicative threshold).",
            measurement=["interviews_completed", "verified_past_spend_count", "willingness_to_prepay_count"],
            decision_rule="If < 4 show verified past spend, kill or narrow the problem definition.",
            limitations=["Self-reported future willingness to pay is unreliable; count only past spend or signed deposits."],
        ),
    ]

    if red_team.recommended_kill_tests:
        tests.append(
            KillTest(
                hypothesis=red_team.recommended_kill_tests[0],
                target_segment=seg,
                method="concierge_mvp_pre_sale",
                budget_estimate=Decimal("100"),
                currency=cur,
                duration_days=14,
                success_threshold=">= 3 paying pilot customers commit at target price (with clear refund guarantee) before full automation.",
                failure_threshold="0 paying pilots after 25 direct outreach conversations.",
                sample_size_guidance="25 direct outreach conversations with decision-makers.",
                measurement=["outreach_sent", "demos_booked", "paid_pilots_closed"],
                decision_rule="Do not build full automated software until manual concierge delivery proves willingness to pay.",
                limitations=["Ensure transparent pilot terms and full refund option for pre-sales."],
            )
        )

    return tests
