"""Budget-tracked Orchestrator connecting domain engines, providers, complaint signals, and audit rules."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from typing import List

from ideastress.benchmarks.base_rates import calibrate_against_base_rates
from ideastress.config import IdeaStressConfig
from ideastress.decision.gate import evaluate_decision_gate, generate_kill_tests
from ideastress.domain.models import (
    AnalysisMode,
    AnalysisRequest,
    AnalysisResult,
    Assumption,
    BudgetUsage,
    Claim,
    ClaimStatus,
    Competitor,
    Evidence,
    FinancialInputs,
    IdeaBrief,
    RedTeamReport,
    RunStatus,
    SourceReliability,
)
from ideastress.evidence.store import EvidenceStore
from ideastress.finance.engine import run_full_financial_analysis
from ideastress.providers.interfaces import FetchProvider, LLMProvider, SearchProvider
from ideastress.providers.mock import (
    MockFetchProvider,
    MockLLMProvider,
    MockSearchProvider,
    build_default_competitors,
    build_default_risks,
)
from ideastress.providers.openai_compat import OpenAICompatibleLLMProvider, TavilySearchProvider
from ideastress.providers.safe_fetch import SafeHTTPFetcher
from ideastress.providers.signals import aggregate_pain_themes, collect_complaint_signals
from ideastress.providers.cpc import DataForSEOCPCProvider, MockCPCProvider, derive_default_keywords, evaluate_paid_channel_falsification
from ideastress.storage.cache import SQLiteSignalCache
from ideastress.storage.sqlite_store import SQLiteAnalysisStore


class AnalysisOrchestrator:
    """Runs the end-to-end Evidence-First Business Feasibility & Falsification workflow."""

    def __init__(
        self,
        config: IdeaStressConfig | None = None,
        llm: LLMProvider | None = None,
        search: SearchProvider | None = None,
        fetcher: FetchProvider | None = None,
        store: SQLiteAnalysisStore | None = None,
    ) -> None:
        self.config = config or IdeaStressConfig.from_env()
        self.llm = llm or self._resolve_llm()
        self.search = search or self._resolve_search()
        self.fetcher = fetcher or self._resolve_fetcher()
        self.store = store
        self.cache = SQLiteSignalCache(self.config.cache_db_path)

    def _resolve_llm(self) -> LLMProvider:
        if self.config.llm_provider == "openai_compatible" and self.config.llm_api_key:
            return OpenAICompatibleLLMProvider(
                api_key=self.config.llm_api_key,
                base_url=self.config.llm_base_url,
                model=self.config.llm_model,
            )
        return MockLLMProvider()

    def _resolve_search(self) -> SearchProvider:
        if self.config.search_provider == "tavily" and self.config.search_api_key:
            return TavilySearchProvider(api_key=self.config.search_api_key)
        return MockSearchProvider()

    def _resolve_fetcher(self) -> FetchProvider:
        if self.config.fetch_provider == "mock" or self.config.search_provider == "mock":
            return MockFetchProvider()
        return SafeHTTPFetcher()

    def _default_financials(self, request: AnalysisRequest) -> FinancialInputs:
        if request.financials is not None:
            return request.financials
        return FinancialInputs(
            business_type=request.business_type,
            currency=request.currency,
            unit_price=Decimal("49"),
            variable_cost_per_unit=Decimal("5"),
            fixed_monthly_costs=Decimal("800"),
            monthly_new_customers=12,
            monthly_acquisition_spend=Decimal("400"),
            monthly_churn_rate=Decimal("0.06"),
            starting_cash=request.budget,
            horizon_months=request.timeline_months,
        )

    def run(self, request: AnalysisRequest, *, save_to_db: bool = True) -> AnalysisResult:
        t0 = time.monotonic()
        budget_cfg = self.config.budget
        usage = BudgetUsage()
        ev_store = EvidenceStore()

        # 1. Record core assumptions explicitly
        fin_inputs = self._default_financials(request)
        assumptions: List[Assumption] = [
            Assumption(
                key="unit_price",
                value=str(fin_inputs.unit_price),
                unit=fin_inputs.currency,
                source="user_input" if request.financials else "default_model",
                criticality="high",
            ),
            Assumption(
                key="variable_cost_per_unit",
                value=str(fin_inputs.variable_cost_per_unit),
                unit=fin_inputs.currency,
                source="user_input" if request.financials else "default_model",
                criticality="high",
            ),
            Assumption(
                key="fixed_monthly_costs",
                value=str(fin_inputs.fixed_monthly_costs),
                unit=fin_inputs.currency,
                source="user_input" if request.financials else "default_model",
                criticality="medium",
            ),
            Assumption(
                key="monthly_new_customers",
                value=fin_inputs.monthly_new_customers,
                unit="customers/month",
                source="user_input" if request.financials else "default_model",
                criticality="high",
            ),
            Assumption(
                key="monthly_churn_rate",
                value=str(fin_inputs.monthly_churn_rate),
                unit="decimal_ratio",
                source="user_input" if request.financials else "default_model",
                criticality="high",
            ),
        ]

        # 2. Deterministic Financial Engine + Reverse Unit-Economics Frontier ($0 LLM cost)
        financials = run_full_financial_analysis(fin_inputs)
        base_rate_checks = calibrate_against_base_rates(fin_inputs, financials)

        # 2b. Real CPC -> Implied CAC Channel Falsification (with 30-day SQLite Cache)
        cpc_prov = (
            DataForSEOCPCProvider(self.config.dataforseo_login, self.config.dataforseo_password)
            if self.config.cpc_provider == 'dataforseo' and self.config.dataforseo_login and self.config.dataforseo_password
            else MockCPCProvider()
        )
        assumed_cvr = fin_inputs.observed_conversion_rate or fin_inputs.conversion_rate or Decimal('0.025')
        channel_falsification = evaluate_paid_channel_falsification(
            derive_default_keywords(request.idea, request.business_type.value),
            max_viable_cac=financials.reverse_frontier.max_viable_cac,
            assumed_conversion_rate=assumed_cvr,
            provider=cpc_prov,
            cache=self.cache,
        )

        # 3. Idea Structuring Agent
        if usage.llm_calls >= budget_cfg.max_llm_calls:
            usage.limit_reached = True
            brief = IdeaBrief(
                problem_statement=request.idea,
                proposed_solution=request.idea,
                customer_segments=[request.customer_segment or "Unspecified"],
                value_proposition="Pending LLM structuring (budget limit reached).",
                revenue_model=request.business_type.value,
                channels=[],
            )
        else:
            usage.llm_calls += 1
            usage.estimated_cost_usd += Decimal("0.01")
            brief = self.llm.generate_structured(
                system_prompt="Structure the user's business idea into a concise IdeaBrief. Do not fabricate numbers.",
                user_prompt=f"Idea: {request.idea}\nMarket: {request.target_market}\nSegment: {request.customer_segment}",
                output_schema=IdeaBrief,
                context={
                    "idea": request.idea,
                    "business_type": request.business_type,
                    "customer_segment": request.customer_segment,
                },
            )

        # 4. Market & Competitor Research + Complaint Signal Intelligence
        search_results = []
        evidence_ids: List[str] = []
        max_queries = 1 if request.mode == AnalysisMode.QUICK else 2
        queries = [
            f"{request.idea} competitors pricing {' '.join(request.target_market[:1])}",
            f"{request.idea} user complaints alternatives reddit G2",
        ][:max_queries]

        for q in queries:
            if usage.search_calls >= budget_cfg.max_search_calls or usage.estimated_cost_usd >= budget_cfg.max_estimated_cost_usd:
                usage.limit_reached = True
                break
            usage.search_calls += 1
            usage.estimated_cost_usd += Decimal("0.01")
            batch = self.search.search(q, limit=4)
            search_results.extend(batch)

        seen_urls = set()
        for sr in search_results:
            if sr.url in seen_urls:
                continue
            seen_urls.add(sr.url)
            if usage.pages_fetched >= budget_cfg.max_pages_fetched:
                usage.limit_reached = True
                break
            try:
                page = self.fetcher.fetch(sr.url)
                usage.pages_fetched += 1
                ev = ev_store.add_evidence(
                    Evidence(
                        source_type="official_website",
                        title=page.title or sr.title,
                        url=page.final_url,
                        publisher=sr.publisher,
                        retrieved_at=page.retrieved_at,
                        snippet=page.snippet or sr.snippet,
                        region=request.target_market[0] if request.target_market else "global",
                        source_reliability=SourceReliability.PRIMARY
                        if "pricing" in sr.url.lower()
                        else SourceReliability.SECONDARY,
                        access_status=page.access_status,
                        limitations=page.limitations,
                    )
                )
            except Exception:
                ev = ev_store.add_evidence(
                    Evidence(
                        source_type="search_snippet",
                        title=sr.title,
                        url=sr.url,
                        publisher=sr.publisher,
                        snippet=sr.snippet,
                        source_reliability=SourceReliability.DISCOVERY_ONLY,
                        access_status="fetch_failed",
                        limitations=["Direct page fetch unavailable; snippet only."],
                    )
                )
            evidence_ids.append(ev.evidence_id)

        # 4b. Collect Competitor Complaint Signals (Reddit / App Store / G2 or Mock)
        pain_themes = {}
        complaint_ev_ids: List[str] = []
        if not usage.limit_reached and budget_cfg.max_search_calls > 0:
            signal_mode = "live" if self.config.search_provider != "mock" else "mock"
            signals = collect_complaint_signals(
                request.idea,
                mode=signal_mode,
                search_provider=self.search if signal_mode == "live" else None,
                limit_per_platform=2,
                cache=self.cache,
            )
            pain_themes = aggregate_pain_themes(signals)
            for sig in signals:
                sev = ev_store.add_evidence(sig.to_evidence())
                complaint_ev_ids.append(sev.evidence_id)

        competitors: List[Competitor] = build_default_competitors(
            request.business_type, search_results, evidence_ids
        )

        # Record Claims linked to Evidence
        if evidence_ids:
            ev_store.add_claim(
                Claim(
                    statement=f"Active commercial competitors exist in {', '.join(request.target_market)} with published pricing or positioning.",
                    claim_type="competitor_landscape",
                    status=ClaimStatus.VERIFIED,
                    confidence_label="medium",
                    scope_market=", ".join(request.target_market),
                    supporting_evidence_ids=evidence_ids[:2],
                    reasoning_summary="Verified via retrieved competitor pages and public snippets.",
                )
            )
        if complaint_ev_ids:
            top_theme = next(iter(pain_themes.keys()), "general_friction")
            ev_store.add_claim(
                Claim(
                    statement=f"Public user complaints highlight recurring competitor friction around '{top_theme}'.",
                    claim_type="pain_point_signal",
                    status=ClaimStatus.SUPPORTED,
                    confidence_label="medium",
                    scope_market=", ".join(request.target_market),
                    supporting_evidence_ids=complaint_ev_ids[:3],
                    reasoning_summary="Derived from qualitative Reddit/G2/App Store complaint signals (friction != proven willingness to pay).",
                )
            )
        ev_store.add_claim(
            Claim(
                statement=f"Target buyers will pay {fin_inputs.currency} {fin_inputs.unit_price} at modeled conversion rate.",
                claim_type="willingness_to_pay",
                status=ClaimStatus.ASSUMPTION,
                confidence_label="low",
                scope_market=", ".join(request.target_market),
                assumption_ids=[assumptions[0].assumption_id],
                reasoning_summary="Founder pricing hypothesis; requires live pre-sale or paid smoke test.",
            )
        )

        # 5. Risks + Independent Red Team
        has_impossible = financials.reverse_frontier.mathematical_verdict == "UNIT_ECONOMICS_IMPOSSIBLE"
        risks = build_default_risks(request.business_type, has_impossible)

        if usage.llm_calls >= budget_cfg.max_llm_calls:
            usage.limit_reached = True
            red_team = RedTeamReport(
                strongest_counterarguments=financials.reverse_frontier.hard_rules_for_red_team
                or ["Budget limit reached before Red Team LLM pass."],
                critical_assumptions=["Unit economics and channel CAC remain unvalidated."],
                failure_paths=["Cash exhaustion prior to break-even."],
                decision_changing_conditions=["Real CAC exceeds max_viable_cac."],
                recommended_kill_tests=["Run capped paid smoke test."],
            )
        else:
            usage.llm_calls += 1
            usage.estimated_cost_usd += Decimal("0.02")
            red_team = self.llm.generate_structured(
                system_prompt="You are an Independent Red Team analyst. Attack the weakest assumptions using the exact Reverse Frontier math bounds.",
                user_prompt=(
                    f"Idea: {request.idea}\n"
                    f"Hard Math Rules:\n" + "\n".join(financials.reverse_frontier.hard_rules_for_red_team)
                ),
                output_schema=RedTeamReport,
                context={
                    "idea": request.idea,
                    "business_type": request.business_type,
                    "frontier_rules": financials.reverse_frontier.hard_rules_for_red_team,
                },
            )

        # 6. Deterministic Evidence Audit + Decision Gate + Kill Tests
        audit = ev_store.audit_claims()
        claims = ev_store.all_claims()
        evidences = ev_store.all_evidences()

        if channel_falsification.verdict == 'CHANNEL_IMPOSSIBLE':
            red_team.strongest_counterarguments.insert(0, channel_falsification.explanation)

        decision = evaluate_decision_gate(
            request=request,
            financials=financials,
            base_rate_checks=base_rate_checks,
            claims=claims,
            competitors=competitors,
            risks=risks,
            red_team=red_team,
            audit=audit,
            channel_falsification=channel_falsification,
        )
        kill_tests = generate_kill_tests(request, financials, red_team)

        usage.runtime_seconds = round(time.monotonic() - t0, 3)
        run_status = RunStatus.PARTIAL_BUDGET_LIMIT if usage.limit_reached else RunStatus.COMPLETED

        result = AnalysisResult(
            status=run_status,
            request=request,
            brief=brief,
            assumptions=assumptions,
            evidences=evidences,
            claims=claims,
            competitors=competitors,
            financials=financials,
            base_rate_checks=base_rate_checks,
            channel_falsification=channel_falsification,
            risks=risks,
            red_team=red_team,
            kill_tests=kill_tests,
            audit=audit,
            decision=decision,
            budget_usage=usage,
            provider_metadata={
                "llm_provider": getattr(self.llm, "name", "unknown"),
                "search_provider": getattr(self.search, "name", "unknown"),
                "fetch_provider": getattr(self.fetcher, "name", "unknown"),
                "complaint_signals_count": len(complaint_ev_ids),
                "pain_themes": pain_themes,
            },
        )

        if save_to_db and self.store is not None:
            self.store.save(result)

        return result
