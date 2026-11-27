"""Core Pydantic domain models for IdeaStress (compatible with Pydantic v1 & v2)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


class BusinessType(str, Enum):
    SAAS = "saas"
    DIGITAL_PRODUCT = "digital_product"
    ECOMMERCE = "ecommerce"
    LOCAL_SERVICE = "local_service"
    MARKETPLACE = "marketplace"


class AnalysisMode(str, Enum):
    QUICK = "quick"
    DEEP = "deep"


class ClaimStatus(str, Enum):
    VERIFIED = "VERIFIED"
    SUPPORTED = "SUPPORTED"
    ASSUMPTION = "ASSUMPTION"
    INFERENCE = "INFERENCE"
    UNKNOWN = "UNKNOWN"
    CONTRADICTED = "CONTRADICTED"


class SourceReliability(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    QUALITATIVE = "qualitative"
    DISCOVERY_ONLY = "discovery_only"
    LOW = "low"
    USER_INPUT = "user_input"


class CompetitorCategory(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    SUBSTITUTE = "substitute"
    EMERGING = "emerging"


class Verdict(str, Enum):
    GO = "GO"
    CONDITIONAL_GO = "CONDITIONAL_GO"
    PIVOT = "PIVOT"
    NO_GO = "NO_GO"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class RunStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PARTIAL_BUDGET_LIMIT = "PARTIAL_BUDGET_LIMIT"
    FAILED = "FAILED"


class FinancialInputs(BaseModel):
    """Deterministic financial model inputs. All monetary values use Decimal."""

    business_type: BusinessType = BusinessType.SAAS
    currency: str = "USD"
    tax_included: bool = False
    period: str = "monthly"

    # Pricing & volume
    unit_price: Decimal = Field(..., description="Price per customer/order/unit (or average GMV for marketplace)")
    variable_cost_per_unit: Decimal = Field(Decimal("0"), description="COGS + payment fees + fulfillment per unit")
    fixed_monthly_costs: Decimal = Field(Decimal("0"), description="Rent, software, baseline salaries, tools")

    # Growth & acquisition
    starting_customers: int = 0
    monthly_new_customers: int = 10
    monthly_acquisition_spend: Decimal = Field(Decimal("0"), description="Paid ads + outbound + marketing spend")
    conversion_rate: Optional[Decimal] = Field(
        None, description="Visitor-to-paid conversion rate as decimal, e.g., 0.02 for 2%"
    )
    monthly_visitors: Optional[int] = None

    # Retention / Repeat / Marketplace
    monthly_churn_rate: Decimal = Field(
        Decimal("0.05"), description="Monthly customer churn as decimal, e.g., 0.05 for 5%"
    )
    take_rate: Optional[Decimal] = Field(
        None, description="Marketplace take rate as decimal, e.g., 0.15 for 15%"
    )
    refund_rate: Decimal = Field(Decimal("0.02"), description="Refund/chargeback rate as decimal")

    # Capital & horizon
    starting_cash: Decimal = Field(Decimal("10000"), description="Available startup cash")
    horizon_months: int = 12

    # US Market / Payment Processor / Tax Realism Presets
    payment_processor: str = Field(
        "none",
        description="Payment fee preset: none | stripe_us (2.9%+$0.30) | stripe_saas (3.6%+$0.30) | mor_paddle (5%+$0.50)",
    )
    effective_tax_rate: Decimal = Field(
        Decimal("0.00"),
        description="Optional effective income/corporate tax rate on positive monthly profit (e.g. 0.21 US fed corp)",
    )
    us_payroll_tax_burden_pct: Decimal = Field(
        Decimal("0.00"),
        description="Optional employer payroll tax burden on variable labor cost (e.g. 0.12 for US FICA/FUTA/SUTA)",
    )

    # Optional real-world experiment overrides
    observed_cac: Optional[Decimal] = None
    observed_conversion_rate: Optional[Decimal] = None


class AnalysisRequest(BaseModel):
    """Top-level user or AI-agent request to stress-test a business idea."""

    idea: str
    target_market: List[str] = Field(default_factory=lambda: ["United States"])
    customer_segment: Optional[str] = None
    business_type: BusinessType = BusinessType.SAAS
    budget: Decimal = Decimal("10000")
    currency: str = "USD"
    timeline_months: int = 12
    team_size: int = 1
    founder_strengths: List[str] = Field(default_factory=list)
    existing_assets: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    mode: AnalysisMode = AnalysisMode.QUICK
    financials: Optional[FinancialInputs] = None
    industry_vertical: Optional[str] = None


class Assumption(BaseModel):
    assumption_id: str = Field(default_factory=lambda: new_id("asm"))
    key: str
    value: Any
    unit: Optional[str] = None
    source: str = "user_input"  # user_input | default_model | experiment_verified
    criticality: str = "high"  # low | medium | high
    rationale: str = ""
    validated: bool = False


class Evidence(BaseModel):
    evidence_id: str = Field(default_factory=lambda: new_id("ev"))
    source_type: str = "official_website"
    title: str
    url: Optional[str] = None
    publisher: Optional[str] = None
    published_at: Optional[str] = None
    retrieved_at: str = Field(default_factory=utc_now_iso)
    snippet: str
    content_hash: Optional[str] = None
    language: str = "en"
    region: str = "global"
    source_reliability: SourceReliability = SourceReliability.SECONDARY
    freshness_status: str = "current_at_retrieval"
    access_status: str = "success"
    limitations: List[str] = Field(default_factory=list)


class Claim(BaseModel):
    claim_id: str = Field(default_factory=lambda: new_id("cl"))
    statement: str
    claim_type: str
    status: ClaimStatus = ClaimStatus.ASSUMPTION
    confidence_label: str = "low"  # low | medium | high
    scope_market: str = "global"
    as_of: str = Field(default_factory=lambda: utc_now_iso()[:10])
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    assumption_ids: List[str] = Field(default_factory=list)
    reasoning_summary: str = ""
    limitations: List[str] = Field(default_factory=list)
    audit_notes: List[str] = Field(default_factory=list)


class Competitor(BaseModel):
    name: str
    category: CompetitorCategory
    url: Optional[str] = None
    description: str
    target_customer: str = "unknown"
    pricing_summary: str = "unknown"
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    overlap_summary: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    last_checked_at: str = Field(default_factory=utc_now_iso)


class IdeaBrief(BaseModel):
    problem_statement: str
    proposed_solution: str
    customer_segments: List[str]
    value_proposition: str
    revenue_model: str
    channels: List[str]
    missing_information: List[str] = Field(default_factory=list)
    ambiguities: List[str] = Field(default_factory=list)


class RiskItem(BaseModel):
    risk_id: str = Field(default_factory=lambda: new_id("rsk"))
    category: str
    title: str
    severity: str  # low | medium | high | critical
    likelihood: str  # low | medium | high
    evidence_ids: List[str] = Field(default_factory=list)
    impact: str
    mitigation: str
    early_warning_signal: str


class RedTeamReport(BaseModel):
    strongest_counterarguments: List[str]
    critical_assumptions: List[str]
    failure_paths: List[str]
    evidence_conflicts: List[str] = Field(default_factory=list)
    decision_changing_conditions: List[str]
    recommended_kill_tests: List[str]


class KillTest(BaseModel):
    experiment_id: str = Field(default_factory=lambda: new_id("exp"))
    hypothesis: str
    target_segment: str
    method: str
    budget_estimate: Decimal
    currency: str = "USD"
    duration_days: int
    success_threshold: str
    failure_threshold: str
    sample_size_guidance: str
    measurement: List[str]
    decision_rule: str
    limitations: List[str] = Field(default_factory=list)


class MonthlyProjection(BaseModel):
    month: int
    active_customers: int
    new_customers: int
    churned_customers: int
    revenue: Decimal
    cogs: Decimal
    gross_profit: Decimal
    acquisition_spend: Decimal
    fixed_costs: Decimal
    net_cash_flow: Decimal
    ending_cash: Decimal


class ScenarioMetrics(BaseModel):
    scenario_name: str  # conservative | base | optimistic
    currency: str
    horizon_months: int
    unit_contribution_margin: Decimal
    gross_margin_pct: Optional[Decimal] = None
    break_even_units: Optional[int] = None
    break_even_status: str = "REACHABLE"
    cac: Optional[Decimal] = None
    ltv: Optional[Decimal] = None
    ltv_status: str = "CALCULATED"
    ltv_to_cac: Optional[Decimal] = None
    cac_payback_months: Optional[Decimal] = None
    month_12_mrr: Decimal = Decimal("0")
    month_12_arr_run_rate: Decimal = Decimal("0")
    total_revenue: Decimal = Decimal("0")
    total_net_cash_flow: Decimal = Decimal("0")
    min_cash_balance: Decimal = Decimal("0")
    ending_cash_balance: Decimal = Decimal("0")
    runway_months: Optional[Decimal] = None
    runway_status: str = "CASH_FLOW_POSITIVE"
    projections: List[MonthlyProjection] = Field(default_factory=list)
    assumptions_applied: Dict[str, str] = Field(default_factory=dict)


class SensitivityPoint(BaseModel):
    variable: str
    change_label: str
    ending_cash: Decimal
    delta_ending_cash: Decimal
    break_even_units: Optional[int] = None
    survives_horizon: bool


class ReverseFrontier(BaseModel):
    """Reverse Unit-Economics Solver output: mathematical survival boundaries."""

    currency: str
    horizon_months: int
    max_viable_cac: Optional[Decimal] = None
    max_cac_for_3x_ltv: Optional[Decimal] = None
    min_viable_unit_price: Optional[Decimal] = None
    max_tolerable_monthly_churn_pct: Optional[Decimal] = None
    min_monthly_new_customers_to_survive: Optional[int] = None
    required_conversion_rate_pct: Optional[Decimal] = None
    mathematical_verdict: str  # VIABLE_FRONTIER | TIGHT_FRONTIER | UNIT_ECONOMICS_IMPOSSIBLE
    impossibility_reasons: List[str] = Field(default_factory=list)
    hard_rules_for_red_team: List[str] = Field(default_factory=list)


class MonteCarloSummary(BaseModel):
    """Seeded 1,000-path Monte Carlo survival probability & cash distribution."""

    simulations: int = 1000
    seed: int = 42
    currency: str = "USD"
    horizon_months: int = 12
    survival_probability_pct: Decimal
    p10_ending_cash: Decimal
    p50_ending_cash: Decimal
    p90_ending_cash: Decimal
    p10_min_cash: Decimal
    bankruptcy_risk_label: str  # LOW_RISK | MODERATE_RISK | HIGH_RISK | CRITICAL_RISK


class FinancialAnalysis(BaseModel):
    currency: str
    business_type: BusinessType
    tax_included: bool
    scenarios: Dict[str, ScenarioMetrics]
    sensitivity: List[SensitivityPoint]
    reverse_frontier: ReverseFrontier
    monte_carlo: Optional[MonteCarloSummary] = None
    limitations: List[str] = Field(default_factory=list)


class BaseRateCheck(BaseModel):
    metric: str
    user_value: str
    benchmark_value: str
    status: str  # ALIGNED | OPTIMISTIC_WARNING | SEVERE_OUTLIER | INFO
    source_title: str
    source_url: str
    retrieved_at: str
    commentary: str


class DimensionScore(BaseModel):
    dimension: str
    rating: str  # weak | moderate | strong | unknown
    rationale: str


class DecisionSummary(BaseModel):
    verdict: Verdict
    headline: str
    reasons: List[str]
    blocking_conditions: List[str] = Field(default_factory=list)
    critical_unknowns: List[str] = Field(default_factory=list)
    dimensions: List[DimensionScore] = Field(default_factory=list)
    next_action: str


class AuditReport(BaseModel):
    passed: bool
    total_claims: int
    verified_claims: int
    downgraded_claims: int
    contradictions_found: int
    issues: List[str] = Field(default_factory=list)


class BudgetUsage(BaseModel):
    search_calls: int = 0
    pages_fetched: int = 0
    llm_calls: int = 0
    estimated_cost_usd: Decimal = Decimal("0.00")
    runtime_seconds: float = 0.0
    limit_reached: bool = False


class KeywordCPCRecord(BaseModel):
    keyword: str
    monthly_search_volume: int = 0
    cpc_low: Decimal = Decimal("0.00")
    cpc_high: Decimal = Decimal("0.00")
    cpc_avg: Decimal = Decimal("0.00")
    competition_level: str = "MEDIUM"
    currency: str = "USD"
    location_code: int = 2840
    source: str = "mock_cpc"
    retrieved_at: str = Field(default_factory=utc_now_iso)


class ChannelFalsificationResult(BaseModel):
    keywords_analyzed: List[KeywordCPCRecord] = Field(default_factory=list)
    weighted_avg_cpc: Decimal
    assumed_conversion_rate_pct: Decimal
    implied_paid_cac: Decimal
    max_viable_cac: Optional[Decimal] = None
    required_conversion_rate_for_cpc_pct: Optional[Decimal] = None
    verdict: str  # CHANNEL_VIABLE | CHANNEL_TIGHT | CHANNEL_IMPOSSIBLE
    cache_hit: bool = False
    explanation: str


class AnalysisResult(BaseModel):
    analysis_id: str = Field(default_factory=lambda: new_id("anl"))
    created_at: str = Field(default_factory=utc_now_iso)
    status: RunStatus = RunStatus.COMPLETED
    request: AnalysisRequest
    brief: IdeaBrief
    assumptions: List[Assumption]
    evidences: List[Evidence]
    claims: List[Claim]
    competitors: List[Competitor]
    financials: FinancialAnalysis
    base_rate_checks: List[BaseRateCheck] = Field(default_factory=list)
    channel_falsification: Optional[ChannelFalsificationResult] = None
    risks: List[RiskItem]
    red_team: RedTeamReport
    kill_tests: List[KillTest]
    audit: AuditReport
    decision: DecisionSummary
    budget_usage: BudgetUsage = Field(default_factory=BudgetUsage)
    provider_metadata: Dict[str, Any] = Field(default_factory=dict)


class LedgerDiffResult(BaseModel):
    previous_verdict: Verdict
    new_verdict: Verdict
    verdict_changed: bool
    changed_assumptions: List[Dict[str, Any]]
    ending_cash_delta: Decimal
    max_viable_cac_delta: Optional[Decimal] = None
    summary: str
