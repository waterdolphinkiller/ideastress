"""Real, source-cited 2025-2026 industry Base Rates for reality calibration.

Every figure in this module carries its exact retrieved source title, URL,
and retrieval date so IdeaStress can flag unrealistic founder assumptions
without fabricating industry averages.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List

from ideastress.domain.models import (
    BaseRateCheck,
    BusinessType,
    FinancialAnalysis,
    FinancialInputs,
)

RETRIEVED_DATE = "2026-11-27"


@dataclass(frozen=True)
class BenchmarkRecord:
    business_type: BusinessType
    metric: str
    value_label: str
    numeric_reference: Decimal
    source_title: str
    source_url: str
    notes: str


INDUSTRY_BASE_RATES: List[BenchmarkRecord] = [
    # --- SaaS ---
    BenchmarkRecord(
        business_type=BusinessType.SAAS,
        metric="software_gross_margin_pct",
        value_label="80% median (AI-heavy products often run lower)",
        numeric_reference=Decimal("80"),
        source_title="SaaS Benchmarks 2026 (Benchmarkit / SubscriptionPlaybook)",
        source_url="https://www.subscriptionplaybook.com/benchmarks/",
        notes="Median private software gross margin; AI inference COGS can compress this materially.",
    ),
    BenchmarkRecord(
        business_type=BusinessType.SAAS,
        metric="monthly_churn_low_arpa_pct",
        value_label="6.2% median monthly customer churn (ARPA < $25)",
        numeric_reference=Decimal("6.2"),
        source_title="ChartMogul SaaS Churn & Retention Benchmarks (Nov 2026)",
        source_url="https://chartmogul.com/benchmarks/",
        notes="Low-ARPA self-serve SaaS experiences structurally higher monthly churn than enterprise SaaS (2.6% at >$1,000 ARPA).",
    ),
    BenchmarkRecord(
        business_type=BusinessType.SAAS,
        metric="monthly_churn_high_arpa_pct",
        value_label="2.6% median monthly customer churn (ARPA > $1,000)",
        numeric_reference=Decimal("2.6"),
        source_title="ChartMogul SaaS Churn & Retention Benchmarks (Nov 2026)",
        source_url="https://chartmogul.com/benchmarks/",
        notes="Higher-ACV B2B SaaS median monthly customer churn.",
    ),
    BenchmarkRecord(
        business_type=BusinessType.SAAS,
        metric="ltv_to_cac_ratio",
        value_label="3.0x rule of thumb; 4.1x 2026 private SaaS median",
        numeric_reference=Decimal("3.0"),
        source_title="ChartMogul LTV Guide & SubscriptionPlaybook 2026 Benchmarks",
        source_url="https://chartmogul.com/saas-metrics/ltv/",
        notes="Below 3.0x signals fragile acquisition economics unless payback is very fast.",
    ),
    BenchmarkRecord(
        business_type=BusinessType.SAAS,
        metric="indie_saas_median_mrr_usd",
        value_label="$145 median MRR (only 23.6% clear $1K MRR, 6.1% clear $10K MRR)",
        numeric_reference=Decimal("145"),
        source_title="TrustMRR / BigIdeasDB State of Indie SaaS Revenue (Sep 2026)",
        source_url="https://bigideasdb.com/dimeadozen-alternative",
        notes="Across 3,700+ reporting indie startups; essential base-rate reality check against optimistic projections.",
    ),
    # --- E-Commerce ---
    BenchmarkRecord(
        business_type=BusinessType.ECOMMERCE,
        metric="conversion_rate_pct",
        value_label="1.4% Shopify median (top 20% > 2.7%, top 10% > 3.7%)",
        numeric_reference=Decimal("1.4"),
        source_title="Littledata / Eulav Average Ecommerce Conversion Rate (Nov 2026)",
        source_url="https://eulav.io/insights/average-ecommerce-conversion-rate/",
        notes="Assuming >3.5% conversion at launch without an existing brand is an aggressive outlier.",
    ),
    BenchmarkRecord(
        business_type=BusinessType.ECOMMERCE,
        metric="blended_cac_usd",
        value_label="$53 to $91 blended ecommerce CAC across 13 verticals",
        numeric_reference=Decimal("53"),
        source_title="First Page Sage via Agency AI Shopify Ad Benchmarks (2026)",
        source_url="https://agencyai.app/blog/shopify-ad-benchmarks-2026",
        notes="Paid acquisition costs in DTC ecommerce frequently consume first-order contribution margin.",
    ),
    BenchmarkRecord(
        business_type=BusinessType.ECOMMERCE,
        metric="gross_margin_pct",
        value_label="45%-65% Apparel; 55%-70% Supplements; 60%-80% Beauty; 15%-30% Electronics",
        numeric_reference=Decimal("50"),
        source_title="Hycos Ecommerce Gross Margin by Category (2026)",
        source_url="https://www.hycos.ai/benchmarks/ecommerce-gross-margin-by-category",
        notes="Gross margin varies drastically by vertical; low-margin categories cannot sustain high paid CAC.",
    ),
    # --- Local Service ---
    BenchmarkRecord(
        business_type=BusinessType.LOCAL_SERVICE,
        metric="net_profit_margin_pct",
        value_label="3%-9% restaurants; ~10% healthy small business net margin (9.74% US 94-sector avg)",
        numeric_reference=Decimal("10"),
        source_title="VantaInsights Restaurant Margins (2026) & NYU Stern 94-Sector Margin Data (Jan 2026)",
        source_url="https://christopholivierconsulting.com/profit-margin-by-industry/",
        notes="Local services are often labor-constrained (e.g., cleaning labor runs 45%-65% of revenue).",
    ),
    # --- Marketplace ---
    BenchmarkRecord(
        business_type=BusinessType.MARKETPLACE,
        metric="take_rate_pct",
        value_label="2% to 70% depending on vertical (typical B2B/service marketplaces: 5%-20%)",
        numeric_reference=Decimal("15"),
        source_title="Flexprice Digital Marketplace Take Rates (Sep 2026)",
        source_url="https://flexprice.io/questions/typical-digital-marketplace-take-rates",
        notes="High take rates require deep liquidity or managed trust; low take rates demand massive GMV.",
    ),
    # --- Digital Product ---
    BenchmarkRecord(
        business_type=BusinessType.DIGITAL_PRODUCT,
        metric="conversion_rate_pct",
        value_label="1.4%-2.7% typical cold-traffic conversion benchmark",
        numeric_reference=Decimal("2.0"),
        source_title="Littledata / Eulav Ecommerce Conversion Benchmarks (Nov 2026)",
        source_url="https://eulav.io/insights/average-ecommerce-conversion-rate/",
        notes="One-time digital products enjoy high gross margin (>85%) but lack recurring MRR compounding.",
    ),
]


def get_base_rates_for(business_type: BusinessType) -> List[BenchmarkRecord]:
    return [r for r in INDUSTRY_BASE_RATES if r.business_type == business_type]


def calibrate_against_base_rates(
    inputs: FinancialInputs,
    analysis: FinancialAnalysis,
) -> List[BaseRateCheck]:
    """Compare user assumptions and base-case outputs against real 2025-2026 industry base rates."""
    checks: List[BaseRateCheck] = []
    base = analysis.scenarios["base"]
    btype = inputs.business_type

    if btype == BusinessType.SAAS:
        # 1. Churn check vs ChartMogul
        user_churn_pct = inputs.monthly_churn_rate * Decimal("100")
        if inputs.unit_price < Decimal("50"):
            ref = next(r for r in INDUSTRY_BASE_RATES if r.metric == "monthly_churn_low_arpa_pct")
            status = "OPTIMISTIC_WARNING" if user_churn_pct < Decimal("4.0") else "ALIGNED"
            commentary = (
                f"Your {user_churn_pct:.1f}% monthly churn assumption is more optimistic than ChartMogul's "
                f"6.2% median for sub-$25 ARPA SaaS."
                if status == "OPTIMISTIC_WARNING"
                else "Monthly churn assumption is realistic relative to low-ARPA SaaS benchmarks."
            )
        else:
            ref = next(r for r in INDUSTRY_BASE_RATES if r.metric == "monthly_churn_high_arpa_pct")
            status = "OPTIMISTIC_WARNING" if user_churn_pct < Decimal("1.5") else "ALIGNED"
            commentary = (
                f"Your {user_churn_pct:.1f}% monthly churn assumption is below the 2.6% high-ARPA median; verify with cohort data."
                if status == "OPTIMISTIC_WARNING"
                else "Monthly churn assumption is within normal B2B SaaS bounds."
            )
        checks.append(
            BaseRateCheck(
                metric="Monthly Customer Churn",
                user_value=f"{user_churn_pct:.1f}%",
                benchmark_value=ref.value_label,
                status=status,
                source_title=ref.source_title,
                source_url=ref.source_url,
                retrieved_at=RETRIEVED_DATE,
                commentary=commentary,
            )
        )

        # 2. Gross margin check
        gm_ref = next(r for r in INDUSTRY_BASE_RATES if r.metric == "software_gross_margin_pct")
        if base.gross_margin_pct is not None:
            gm_status = "OPTIMISTIC_WARNING" if base.gross_margin_pct > Decimal("92") else (
                "SEVERE_OUTLIER" if base.gross_margin_pct < Decimal("55") else "ALIGNED"
            )
            checks.append(
                BaseRateCheck(
                    metric="Gross Margin",
                    user_value=f"{base.gross_margin_pct:.1f}%",
                    benchmark_value=gm_ref.value_label,
                    status=gm_status,
                    source_title=gm_ref.source_title,
                    source_url=gm_ref.source_url,
                    retrieved_at=RETRIEVED_DATE,
                    commentary=(
                        "Check whether AI API inference, hosting, support, and payment fees are fully included in variable cost."
                        if gm_status != "ALIGNED"
                        else "Gross margin aligns with typical software benchmarks."
                    ),
                )
            )

        # 3. Indie SaaS MRR reality anchor
        mrr_ref = next(r for r in INDUSTRY_BASE_RATES if r.metric == "indie_saas_median_mrr_usd")
        m12 = base.month_12_mrr
        mrr_status = "OPTIMISTIC_WARNING" if m12 > Decimal("10000") and inputs.currency == "USD" else "INFO"
        checks.append(
            BaseRateCheck(
                metric="Month-12 MRR vs Indie Base Rate",
                user_value=f"{inputs.currency} {m12:,.2f}",
                benchmark_value=mrr_ref.value_label,
                status=mrr_status,
                source_title=mrr_ref.source_title,
                source_url=mrr_ref.source_url,
                retrieved_at=RETRIEVED_DATE,
                commentary=(
                    "Projected Month-12 MRR exceeds the top 6.1% indie SaaS threshold ($10K MRR); distribution proof is essential."
                    if mrr_status == "OPTIMISTIC_WARNING"
                    else "Base-rate anchor: most indie SaaS products earn under $1K MRR without a repeatable acquisition channel."
                ),
            )
        )

    elif btype == BusinessType.ECOMMERCE:
        cvr_ref = next(r for r in INDUSTRY_BASE_RATES if r.metric == "conversion_rate_pct")
        if inputs.conversion_rate is not None:
            user_cvr_pct = inputs.conversion_rate * Decimal("100")
            status = "SEVERE_OUTLIER" if user_cvr_pct > Decimal("4.5") else (
                "OPTIMISTIC_WARNING" if user_cvr_pct > Decimal("2.7") else "ALIGNED"
            )
            checks.append(
                BaseRateCheck(
                    metric="Store Conversion Rate",
                    user_value=f"{user_cvr_pct:.2f}%",
                    benchmark_value=cvr_ref.value_label,
                    status=status,
                    source_title=cvr_ref.source_title,
                    source_url=cvr_ref.source_url,
                    retrieved_at=RETRIEVED_DATE,
                    commentary=(
                        "Assumed conversion rate sits in the top 10%-20% of mature Shopify stores; cold launch traffic usually converts closer to 1.0%-1.5%."
                        if status != "ALIGNED"
                        else "Conversion rate assumption is realistic relative to Shopify medians."
                    ),
                )
            )

        cac_ref = next(r for r in INDUSTRY_BASE_RATES if r.metric == "blended_cac_usd")
        if base.cac is not None and inputs.currency == "USD":
            cac_status = "OPTIMISTIC_WARNING" if base.cac < Decimal("25") else "ALIGNED"
            checks.append(
                BaseRateCheck(
                    metric="Ecommerce CAC",
                    user_value=f"USD {base.cac:.2f}",
                    benchmark_value=cac_ref.value_label,
                    status=cac_status,
                    source_title=cac_ref.source_title,
                    source_url=cac_ref.source_url,
                    retrieved_at=RETRIEVED_DATE,
                    commentary=(
                        "Assumed CAC is far below the $53-$91 First Page Sage ecommerce benchmark; validate paid ad CPM/CPC before buying inventory."
                        if cac_status == "OPTIMISTIC_WARNING"
                        else "CAC assumption is consistent with paid ecommerce acquisition costs."
                    ),
                )
            )

    elif btype == BusinessType.LOCAL_SERVICE:
        ref = next(r for r in INDUSTRY_BASE_RATES if r.metric == "net_profit_margin_pct")
        checks.append(
            BaseRateCheck(
                metric="Local Service Profit Margin Anchor",
                user_value=f"{base.gross_margin_pct:.1f}% gross" if base.gross_margin_pct is not None else "N/A",
                benchmark_value=ref.value_label,
                status="INFO",
                source_title=ref.source_title,
                source_url=ref.source_url,
                retrieved_at=RETRIEVED_DATE,
                commentary="Ensure founder labor, scheduling overhead, insurance, and travel time are priced into unit costs.",
            )
        )

    elif btype == BusinessType.MARKETPLACE:
        ref = next(r for r in INDUSTRY_BASE_RATES if r.metric == "take_rate_pct")
        tr_pct = (inputs.take_rate or Decimal("0.10")) * Decimal("100")
        status = "OPTIMISTIC_WARNING" if tr_pct > Decimal("25") else "ALIGNED"
        checks.append(
            BaseRateCheck(
                metric="Marketplace Take Rate",
                user_value=f"{tr_pct:.1f}%",
                benchmark_value=ref.value_label,
                status=status,
                source_title=ref.source_title,
                source_url=ref.source_url,
                retrieved_at=RETRIEVED_DATE,
                commentary=(
                    "Take rates above 25% require strong payment/trust lock-in to prevent disintermediation."
                    if status == "OPTIMISTIC_WARNING"
                    else "Take rate sits within typical digital marketplace ranges."
                ),
            )
        )

    elif btype == BusinessType.DIGITAL_PRODUCT:
        ref = next(r for r in INDUSTRY_BASE_RATES if r.metric == "conversion_rate_pct")
        if inputs.conversion_rate is not None:
            cvr_pct = inputs.conversion_rate * Decimal("100")
            status = "OPTIMISTIC_WARNING" if cvr_pct > Decimal("3.5") else "ALIGNED"
            checks.append(
                BaseRateCheck(
                    metric="Digital Product Conversion Rate",
                    user_value=f"{cvr_pct:.2f}%",
                    benchmark_value=ref.value_label,
                    status=status,
                    source_title=ref.source_title,
                    source_url=ref.source_url,
                    retrieved_at=RETRIEVED_DATE,
                    commentary=(
                        "Cold-traffic conversion above 3.5% is hard without an existing audience or email list."
                        if status == "OPTIMISTIC_WARNING"
                        else "Conversion rate assumption is reasonable for cold-to-warm funnels."
                    ),
                )
            )

    return checks
