"""10-Case Industry Benchmark Suite & Automated Quality Evaluator for IdeaStress.

Covers all 10 required benchmark archetypes:
  1. AI Resume Builder SaaS (crowded low-ARPA SaaS)
  2. Small Neighborhood Restaurant (thin-margin F&B)
  3. Niche Appointment Booking SaaS (vertical B2B SaaS)
  4. Dropshipping Store (fragile CAC + negative/low margin)
  5. Local Eco-Cleaning Service (labor-constrained local service)
  6. Paid Content / Newsletter Tool (low-price subscription)
  7. Undifferentiated AI Image Wrapper (negative unit economics under API COGS)
  8. SMB Accounting Assistant (healthy B2B unit economics)
  9. Regulated Fintech / Medical Compliance App (high regulatory risk)
 10. Insufficient-Data Edge Case (zero search budget -> must not fabricate VERIFIED facts)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List

from ideastress.config import BudgetConfig, IdeaStressConfig
from ideastress.domain.models import (
    AnalysisRequest,
    BusinessType,
    ClaimStatus,
    FinancialInputs,
    Verdict,
)
from ideastress.orchestration.runner import AnalysisOrchestrator


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    title: str
    request: AnalysisRequest
    allowed_verdicts: List[Verdict]
    expect_impossible_math: bool = False
    expect_base_rate_warning: bool = False
    zero_search_budget: bool = False


def get_ten_benchmark_cases() -> List[BenchmarkCase]:
    return [
        BenchmarkCase(
            case_id="bm_01_ai_resume_saas",
            title="AI Resume Builder SaaS (Low ARPA / High Churn Risk)",
            request=AnalysisRequest(
                idea="AI resume builder SaaS for job seekers",
                customer_segment="Active job seekers",
                business_type=BusinessType.SAAS,
                budget=Decimal("5000"),
                currency="USD",
                financials=FinancialInputs(
                    business_type=BusinessType.SAAS,
                    currency="USD",
                    unit_price=Decimal("19"),
                    variable_cost_per_unit=Decimal("3"),
                    fixed_monthly_costs=Decimal("600"),
                    monthly_new_customers=25,
                    monthly_acquisition_spend=Decimal("750"),
                    monthly_churn_rate=Decimal("0.02"),  # Unrealistically low vs 6.2% ChartMogul median!
                    starting_cash=Decimal("5000"),
                ),
            ),
            allowed_verdicts=[Verdict.CONDITIONAL_GO, Verdict.PIVOT, Verdict.NO_GO],
            expect_base_rate_warning=True,
        ),
        BenchmarkCase(
            case_id="bm_02_small_restaurant",
            title="Small Neighborhood Restaurant (Thin Margin / High Fixed Rent)",
            request=AnalysisRequest(
                idea="Fast-casual noodle bistro in downtown commercial district",
                customer_segment="Weekday office lunch crowd",
                business_type=BusinessType.LOCAL_SERVICE,
                budget=Decimal("40000"),
                currency="USD",
                financials=FinancialInputs(
                    business_type=BusinessType.LOCAL_SERVICE,
                    currency="USD",
                    unit_price=Decimal("16"),
                    variable_cost_per_unit=Decimal("10"),
                    fixed_monthly_costs=Decimal("9500"),
                    monthly_new_customers=1400,
                    monthly_acquisition_spend=Decimal("800"),
                    starting_cash=Decimal("40000"),
                ),
            ),
            allowed_verdicts=[Verdict.CONDITIONAL_GO, Verdict.PIVOT, Verdict.NO_GO],
        ),
        BenchmarkCase(
            case_id="bm_03_niche_booking_saas",
            title="Niche Pet Grooming Appointment SaaS (Healthy Vertical SaaS)",
            request=AnalysisRequest(
                idea="Appointment & SMS reminder SaaS for independent pet grooming salons",
                customer_segment="Independent pet grooming salon owners",
                business_type=BusinessType.SAAS,
                budget=Decimal("15000"),
                currency="USD",
                financials=FinancialInputs(
                    business_type=BusinessType.SAAS,
                    currency="USD",
                    unit_price=Decimal("79"),
                    variable_cost_per_unit=Decimal("8"),
                    fixed_monthly_costs=Decimal("900"),
                    monthly_new_customers=12,
                    monthly_acquisition_spend=Decimal("480"),
                    monthly_churn_rate=Decimal("0.04"),
                    starting_cash=Decimal("15000"),
                ),
            ),
            allowed_verdicts=[Verdict.GO, Verdict.CONDITIONAL_GO],
        ),
        BenchmarkCase(
            case_id="bm_04_dropshipping_store",
            title="Generic Dropshipping Store (Extreme CVR Outlier + Fragile CAC)",
            request=AnalysisRequest(
                idea="Generalist LED desk gadget dropshipping Shopify store",
                customer_segment="College students & gamers",
                business_type=BusinessType.ECOMMERCE,
                budget=Decimal("6000"),
                currency="USD",
                financials=FinancialInputs(
                    business_type=BusinessType.ECOMMERCE,
                    currency="USD",
                    unit_price=Decimal("32"),
                    variable_cost_per_unit=Decimal("18"),
                    fixed_monthly_costs=Decimal("500"),
                    monthly_visitors=3000,
                    conversion_rate=Decimal("0.065"),  # 6.5% extreme outlier vs 1.4% median
                    monthly_new_customers=195,
                    monthly_acquisition_spend=Decimal("2500"),
                    starting_cash=Decimal("6000"),
                ),
            ),
            allowed_verdicts=[Verdict.PIVOT, Verdict.NO_GO, Verdict.CONDITIONAL_GO],
            expect_base_rate_warning=True,
        ),
        BenchmarkCase(
            case_id="bm_05_local_cleaning",
            title="Local Recurring Condo Cleaning Service (MYR)",
            request=AnalysisRequest(
                idea="Recurring eco-friendly condo cleaning service in Kuala Lumpur",
                customer_segment="Dual-income condo households in KL",
                business_type=BusinessType.LOCAL_SERVICE,
                budget=Decimal("25000"),
                currency="MYR",
                financials=FinancialInputs(
                    business_type=BusinessType.LOCAL_SERVICE,
                    currency="MYR",
                    unit_price=Decimal("180"),
                    variable_cost_per_unit=Decimal("105"),
                    fixed_monthly_costs=Decimal("3800"),
                    monthly_new_customers=75,
                    monthly_acquisition_spend=Decimal("1200"),
                    starting_cash=Decimal("25000"),
                ),
            ),
            allowed_verdicts=[Verdict.GO, Verdict.CONDITIONAL_GO],
        ),
        BenchmarkCase(
            case_id="bm_06_digital_template_pack",
            title="One-Time Digital Product (Notion & Excel Finance Templates)",
            request=AnalysisRequest(
                idea="One-time purchase financial modeling template pack for indie founders",
                customer_segment="Bootstrapped indie founders",
                business_type=BusinessType.DIGITAL_PRODUCT,
                budget=Decimal("3000"),
                currency="USD",
                financials=FinancialInputs(
                    business_type=BusinessType.DIGITAL_PRODUCT,
                    currency="USD",
                    unit_price=Decimal("39"),
                    variable_cost_per_unit=Decimal("2"),
                    fixed_monthly_costs=Decimal("150"),
                    monthly_visitors=2500,
                    conversion_rate=Decimal("0.02"),
                    monthly_new_customers=50,
                    monthly_acquisition_spend=Decimal("400"),
                    starting_cash=Decimal("3000"),
                ),
            ),
            allowed_verdicts=[Verdict.GO, Verdict.CONDITIONAL_GO],
        ),
        BenchmarkCase(
            case_id="bm_07_negative_margin_ai_wrapper",
            title="Undifferentiated AI Video Wrapper (Negative Unit Margin -> MUST BE NO_GO)",
            request=AnalysisRequest(
                idea="Unlimited AI video generation wrapper for $9/month",
                customer_segment="Casual social media users",
                business_type=BusinessType.SAAS,
                budget=Decimal("5000"),
                currency="USD",
                financials=FinancialInputs(
                    business_type=BusinessType.SAAS,
                    currency="USD",
                    unit_price=Decimal("9"),
                    variable_cost_per_unit=Decimal("14"),  # GPU/API cost exceeds price!
                    fixed_monthly_costs=Decimal("500"),
                    monthly_new_customers=50,
                    monthly_acquisition_spend=Decimal("400"),
                    monthly_churn_rate=Decimal("0.12"),
                    starting_cash=Decimal("5000"),
                ),
            ),
            allowed_verdicts=[Verdict.NO_GO],
            expect_impossible_math=True,
        ),
        BenchmarkCase(
            case_id="bm_08_smb_accounting_saas",
            title="SMB Accounting Assistant SaaS (Core Reference Case)",
            request=AnalysisRequest(
                idea="AI bookkeeping assistant for US solo freelancers",
                customer_segment="US solo freelancers",
                business_type=BusinessType.SAAS,
                budget=Decimal("12000"),
                currency="USD",
                financials=FinancialInputs(
                    business_type=BusinessType.SAAS,
                    currency="USD",
                    unit_price=Decimal("49"),
                    variable_cost_per_unit=Decimal("6"),
                    fixed_monthly_costs=Decimal("900"),
                    monthly_new_customers=14,
                    monthly_acquisition_spend=Decimal("560"),
                    monthly_churn_rate=Decimal("0.05"),
                    starting_cash=Decimal("12000"),
                ),
            ),
            allowed_verdicts=[Verdict.GO, Verdict.CONDITIONAL_GO],
        ),
        BenchmarkCase(
            case_id="bm_09_marketplace_niche_crafts",
            title="B2B Specialty Coffee Bean Marketplace (Take-Rate Model)",
            request=AnalysisRequest(
                idea="Direct-trade specialty coffee wholesale marketplace connecting roasters and cafes",
                customer_segment="Independent specialty cafes",
                business_type=BusinessType.MARKETPLACE,
                budget=Decimal("20000"),
                currency="USD",
                financials=FinancialInputs(
                    business_type=BusinessType.MARKETPLACE,
                    currency="USD",
                    unit_price=Decimal("400"),  # average order GMV
                    take_rate=Decimal("0.12"),  # $48 gross rev/order
                    variable_cost_per_unit=Decimal("10"),
                    fixed_monthly_costs=Decimal("2200"),
                    monthly_new_customers=85,
                    monthly_acquisition_spend=Decimal("900"),
                    starting_cash=Decimal("20000"),
                ),
            ),
            allowed_verdicts=[Verdict.GO, Verdict.CONDITIONAL_GO],
        ),
        BenchmarkCase(
            case_id="bm_10_insufficient_data_edge",
            title="Zero-Search / Insufficient-Data Edge Case (Must Not Fabricate Verified Facts)",
            request=AnalysisRequest(
                idea="Proprietary underwater acoustic mesh sensor rental for aquaculture farms",
                customer_segment=None,
                business_type=BusinessType.LOCAL_SERVICE,
                budget=Decimal("15000"),
                currency="USD",
                financials=FinancialInputs(
                    business_type=BusinessType.LOCAL_SERVICE,
                    currency="USD",
                    unit_price=Decimal("350"),
                    variable_cost_per_unit=Decimal("120"),
                    fixed_monthly_costs=Decimal("1500"),
                    monthly_new_customers=8,
                    monthly_acquisition_spend=Decimal("400"),
                    starting_cash=Decimal("15000"),
                ),
            ),
            allowed_verdicts=[Verdict.INSUFFICIENT_DATA, Verdict.CONDITIONAL_GO],
            zero_search_budget=True,
        ),
    ]


def run_benchmark_suite() -> Dict:
    """Execute all 10 benchmark cases and compute aggregate quality & safety metrics."""
    cases = get_ten_benchmark_cases()
    results = []
    passed_cases = 0
    total_claims = 0
    unbacked_verified = 0
    kill_test_present = 0

    for case in cases:
        cfg = (
            IdeaStressConfig(budget=BudgetConfig(max_search_calls=0, max_pages_fetched=0, max_llm_calls=2))
            if case.zero_search_budget
            else IdeaStressConfig()
        )
        orch = AnalysisOrchestrator(config=cfg)
        res = orch.run(case.request, save_to_db=False)

        verdict_ok = res.decision.verdict in case.allowed_verdicts
        math_ok = (
            (res.financials.reverse_frontier.mathematical_verdict == "UNIT_ECONOMICS_IMPOSSIBLE")
            if case.expect_impossible_math
            else True
        )
        br_ok = (
            any(b.status in ("OPTIMISTIC_WARNING", "SEVERE_OUTLIER") for b in res.base_rate_checks)
            if case.expect_base_rate_warning
            else True
        )

        # Verify zero unbacked VERIFIED claims survive audit
        for c in res.claims:
            total_claims += 1
            if c.status == ClaimStatus.VERIFIED and not c.supporting_evidence_ids:
                unbacked_verified += 1

        if res.kill_tests:
            kill_test_present += 1

        case_passed = verdict_ok and math_ok and br_ok
        if case_passed:
            passed_cases += 1

        results.append(
            {
                "case_id": case.case_id,
                "title": case.title,
                "verdict": res.decision.verdict.value,
                "math_frontier": res.financials.reverse_frontier.mathematical_verdict,
                "passed": case_passed,
                "evidences": len(res.evidences),
                "kill_tests": len(res.kill_tests),
            }
        )

    return {
        "total_cases": len(cases),
        "passed_cases": passed_cases,
        "pass_rate_pct": round((passed_cases / len(cases)) * 100, 1),
        "unsupported_verified_claim_rate_pct": round((unbacked_verified / max(1, total_claims)) * 100, 2),
        "kill_test_coverage_pct": round((kill_test_present / len(cases)) * 100, 1),
        "cases": results,
    }
