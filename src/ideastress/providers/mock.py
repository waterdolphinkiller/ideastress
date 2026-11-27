"""Deterministic offline Mock providers for zero-API-key demos and CI tests."""

from __future__ import annotations

from typing import Any, Dict, List, Type, TypeVar

from pydantic import BaseModel

from ideastress.domain.models import (
    BusinessType,
    Competitor,
    CompetitorCategory,
    IdeaBrief,
    RedTeamReport,
    RiskItem,
    utc_now_iso,
)
from ideastress.providers.interfaces import FetchedPage, SearchResult

T = TypeVar("T", bound=BaseModel)


class MockSearchProvider:
    name = "mock_search"

    def search(self, query: str, *, limit: int = 8) -> List[SearchResult]:
        q_lower = query.lower()
        if "accounting" in q_lower or "bookkeeping" in q_lower or "saas" in q_lower:
            return [
                SearchResult(
                    title="QuickBooks Online Pricing & Plans",
                    url="https://quickbooks.intuit.com/pricing/",
                    snippet="Small business accounting software starting at $35/mo with bank feeds, invoicing, and tax prep.",
                    publisher="Intuit QuickBooks",
                ),
                SearchResult(
                    title="Xero Accounting Software Pricing",
                    url="https://www.xero.com/pricing-plans/",
                    snippet="Cloud accounting for small businesses with automated reconciliation and multi-currency support.",
                    publisher="Xero",
                ),
                SearchResult(
                    title="Wave Free Accounting Software",
                    url="https://www.waveapps.com/pricing",
                    snippet="Free starter bookkeeping and invoicing for solo entrepreneurs; paid Pro plan at $16/mo.",
                    publisher="Wave Financial",
                ),
            ][:limit]
        if "supplement" in q_lower or "ecommerce" in q_lower or "shopify" in q_lower:
            return [
                SearchResult(
                    title="DTC Supplement Market & Margin Benchmarks",
                    url="https://www.hycos.ai/benchmarks/ecommerce-gross-margin-by-category",
                    snippet="Health & Supplements gross margins typically range 55%-70%, while blended ecommerce CAC runs $53-$91.",
                    publisher="Hycos Benchmarks",
                ),
                SearchResult(
                    title="AG1 Subscription Pricing",
                    url="https://drinkag1.com/",
                    snippet="Category-leading daily nutrition subscription at $79/mo with massive influencer and podcast distribution.",
                    publisher="AG1",
                ),
            ][:limit]
        return [
            SearchResult(
                title="Local Service Pricing & Market Overview",
                url="https://www.thumbtack.com/",
                snippet="Marketplace connecting homeowners with vetted local service pros; high lead competition.",
                publisher="Thumbtack",
            ),
            SearchResult(
                title="Small Business Margin Benchmarks",
                url="https://christopholivierconsulting.com/profit-margin-by-industry/",
                snippet="US 94-sector average net profit margin sits around 9.74% with labor as primary cost driver.",
                publisher="NYU Stern / Industry Benchmarks",
            ),
        ][:limit]


class MockFetchProvider:
    name = "mock_fetch"

    def fetch(self, url: str) -> FetchedPage:
        return FetchedPage(
            url=url,
            final_url=url,
            title=f"Snapshot of {url}",
            snippet=f"Verified public page excerpt retrieved from {url} showing active product positioning and pricing.",
            status_code=200,
            retrieved_at=utc_now_iso(),
            access_status="success",
            limitations=["Mock snapshot used in offline mode; run with live fetch for real-time pricing."],
        )


class MockLLMProvider:
    """Deterministic structured generator for offline testing and demos."""

    name = "mock_llm"

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_schema: Type[T],
        context: Dict[str, Any] | None = None,
    ) -> T:
        ctx = context or {}
        idea = ctx.get("idea", "Business idea")
        btype = ctx.get("business_type", BusinessType.SAAS)
        seg = ctx.get("customer_segment") or "Small business owners & independent operators"
        frontier_rules = ctx.get("frontier_rules", [])

        if output_schema is IdeaBrief:
            return IdeaBrief(
                problem_statement=f"{seg} lose time and money on manual workflows related to: {idea}.",
                proposed_solution=idea,
                customer_segments=[seg],
                value_proposition="Faster execution with lower operational overhead than incumbent tools.",
                revenue_model=f"{btype.value if isinstance(btype, BusinessType) else btype} pricing model",
                channels=["Organic search / free utility tools", "Targeted paid search", "Direct outbound & communities"],
                missing_information=[
                    "Direct proof of buyer willingness to switch from current free/manual workaround",
                    "Verified channel-specific CAC from a live paid test",
                ],
                ambiguities=["Exact switching trigger and primary acquisition channel need empirical validation."],
            )  # type: ignore[return-value]

        if output_schema is RedTeamReport:
            counterargs = [
                "Incumbents and free substitutes (spreadsheets, free-tier SaaS, or manual agencies) already cover 80% of the core workflow.",
                "Paid acquisition channels in this category are crowded; cold-traffic CAC frequently breaks unit economics before retention compounds.",
                "Self-reported founder optimism rarely survives first contact with real checkout friction.",
            ]
            if frontier_rules:
                counterargs.insert(0, f"Mathematical Stress Boundary: {frontier_rules[0]}")
            return RedTeamReport(
                strongest_counterarguments=counterargs,
                critical_assumptions=[
                    "Target buyers will pay the modeled unit price rather than stay on free alternatives.",
                    "Real blended CAC stays below the Reverse Frontier mathematical ceiling.",
                    "Monthly churn/refund rate does not exceed 2026 industry medians.",
                ],
                failure_paths=[
                    "Paid acquisition CAC comes in 2x higher than modeled, exhausting starting cash before break-even.",
                    "High Month 1-3 churn prevents LTV from paying back acquisition spend.",
                ],
                evidence_conflicts=[],
                decision_changing_conditions=[
                    "If a 10-day paid smoke test shows implied CAC > max_viable_cac, the current GTM channel is unviable.",
                    "If fewer than 4/15 interviewed ICPs spent money on this problem recently, demand is too weak.",
                ],
                recommended_kill_tests=[
                    "Pre-sell 3 concierge pilot customers at full target price before writing automation code."
                ],
            )  # type: ignore[return-value]

        raise ValueError(f"MockLLMProvider does not handle schema: {output_schema}")


def build_default_competitors(btype: BusinessType, search_results: List[SearchResult], evidence_ids: List[str]) -> List[Competitor]:
    """Construct categorized direct, indirect, and substitute competitors grounded in search results."""
    comps: List[Competitor] = []
    for idx, sr in enumerate(search_results[:3]):
        cat = CompetitorCategory.DIRECT if idx == 0 else CompetitorCategory.INDIRECT
        comps.append(
            Competitor(
                name=sr.publisher or sr.title[:40],
                category=cat,
                url=sr.url,
                description=sr.snippet,
                target_customer="Overlapping SMB / consumer segment",
                pricing_summary="See official pricing URL" if "pric" in sr.url.lower() else "unknown",
                strengths=["Established brand trust", "Existing distribution channels"],
                weaknesses=["Complex onboarding or bloated feature set for niche workflows"],
                overlap_summary="Directly competes for the same customer budget.",
                evidence_ids=[evidence_ids[idx]] if idx < len(evidence_ids) else [],
            )
        )
    # Always include realistic Substitute (Excel / manual / free DIY)
    comps.append(
        Competitor(
            name="Manual Spreadsheets / Free DIY Workaround",
            category=CompetitorCategory.SUBSTITUTE,
            url=None,
            description="Customers doing the job manually with Google Sheets, Notion, or free generalist tools.",
            target_customer="Budget-conscious early buyers",
            pricing_summary="$0 direct software cost (time cost only)",
            strengths=["Zero switching friction", "Zero cash outlay"],
            weaknesses=["Time-consuming and error-prone at scale"],
            overlap_summary="Primary reason early prospects delay paying for a new tool.",
            evidence_ids=[],
        )
    )
    return comps


def build_default_risks(btype: BusinessType, has_impossible_math: bool) -> List[RiskItem]:
    risks = [
        RiskItem(
            category="Distribution Risk",
            title="Paid Acquisition CAC Exceeds Survival Ceiling",
            severity="critical" if has_impossible_math else "high",
            likelihood="high",
            impact="Exhausts starting cash before reaching break-even customer volume.",
            mitigation="Run a capped $100-$250 smoke test and build SEO/free-tool organic acquisition.",
            early_warning_signal="CPC > 15% of unit contribution margin during initial ad test.",
        ),
        RiskItem(
            category="Competitive Risk",
            title="Incumbent Bundling & Free Substitutes",
            severity="high",
            likelihood="medium",
            impact="Prospects stick with free spreadsheets or existing all-in-one suites.",
            mitigation="Narrow ICP to a high-pain wedge workflow incumbents neglect.",
            early_warning_signal="Prospects praise the demo but refuse to put a card down.",
        ),
        RiskItem(
            category="Financial Risk",
            title="Retention / Churn Erosion",
            severity="high" if btype == BusinessType.SAAS else "medium",
            likelihood="medium",
            impact="High early churn collapses LTV and breaks CAC payback.",
            mitigation="Track cohort retention weekly and anchor onboarding to one measurable ROI outcome.",
            early_warning_signal="Month-1 churn exceeds 8% or refund rate exceeds 5%.",
        ),
    ]
    return risks
