"""Git-Friendly Assumption Ledger (`venture.yaml`) loader & Diff engine."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

import yaml

from ideastress.benchmarks.base_rates import calibrate_against_base_rates
from ideastress.decision.gate import evaluate_decision_gate
from ideastress.domain.models import (
    AnalysisRequest,
    AuditReport,
    Claim,
    ClaimStatus,
    Competitor,
    FinancialInputs,
    LedgerDiffResult,
    RedTeamReport,
    RiskItem,
)
from ideastress.exceptions import LedgerValidationError
from ideastress.finance.engine import q2, run_full_financial_analysis


def _to_yaml_safe(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _to_yaml_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_yaml_safe(v) for v in obj]
    return obj


def load_ledger_yaml(path: str | Path) -> AnalysisRequest:
    """Parse a venture.yaml assumption ledger into a validated AnalysisRequest."""
    p = Path(path)
    if not p.exists():
        raise LedgerValidationError(f"Ledger file not found: {p}")
    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise LedgerValidationError("Ledger YAML must be a mapping/object at the root.")
        return AnalysisRequest(**raw)
    except Exception as exc:
        raise LedgerValidationError(f"Failed to parse ledger '{p}': {exc}") from exc


def save_ledger_yaml(request: AnalysisRequest, path: str | Path) -> Path:
    """Serialize an AnalysisRequest into a clean, Git-friendly YAML file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = _to_yaml_safe(request.dict())
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return p


def _ensure_financials(req: AnalysisRequest) -> FinancialInputs:
    if req.financials is not None:
        return req.financials
    return FinancialInputs(
        business_type=req.business_type,
        currency=req.currency,
        unit_price=Decimal("49"),
        variable_cost_per_unit=Decimal("5"),
        fixed_monthly_costs=Decimal("500"),
        monthly_new_customers=10,
        monthly_acquisition_spend=Decimal("300"),
        starting_cash=req.budget,
        horizon_months=req.timeline_months,
    )


def _flatten_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten_dict(v, key))
        else:
            out[key] = v
    return out


def diff_ledgers(
    before: AnalysisRequest,
    after: AnalysisRequest,
    *,
    claims_before: List[Claim] | None = None,
    claims_after: List[Claim] | None = None,
    competitors: List[Competitor] | None = None,
    risks: List[RiskItem] | None = None,
    red_team: RedTeamReport | None = None,
) -> LedgerDiffResult:
    """Deterministically diff two ledger versions and compute financial + verdict impact."""
    fin_before_in = _ensure_financials(before)
    fin_after_in = _ensure_financials(after)

    fin_before = run_full_financial_analysis(fin_before_in)
    fin_after = run_full_financial_analysis(fin_after_in)

    br_before = calibrate_against_base_rates(fin_before_in, fin_before)
    br_after = calibrate_against_base_rates(fin_after_in, fin_after)

    default_claim = [
        Claim(
            statement="Baseline demand signal recorded in ledger.",
            claim_type="market_demand",
            status=ClaimStatus.SUPPORTED,
        )
    ]
    default_rt = red_team or RedTeamReport(
        strongest_counterarguments=["Channel CAC may exceed modeled ceiling."],
        critical_assumptions=["Paid conversion holds at modeled rate."],
        failure_paths=["Cash exhaustion before break-even."],
        decision_changing_conditions=["Real CAC exceeds solved max_viable_cac."],
        recommended_kill_tests=["Run 10-day paid intent smoke test."],
    )
    audit_ok = AuditReport(passed=True, total_claims=1, verified_claims=0, downgraded_claims=0, contradictions_found=0)

    dec_before = evaluate_decision_gate(
        before, fin_before, br_before, claims_before or default_claim, competitors or [], risks or [], default_rt, audit_ok
    )
    dec_after = evaluate_decision_gate(
        after, fin_after, br_after, claims_after or default_claim, competitors or [], risks or [], default_rt, audit_ok
    )

    flat_b = _flatten_dict(_to_yaml_safe(before.dict()))
    flat_a = _flatten_dict(_to_yaml_safe(after.dict()))
    changed: List[Dict[str, Any]] = []
    for k in sorted(set(flat_b.keys()) | set(flat_a.keys())):
        if flat_b.get(k) != flat_a.get(k):
            changed.append({"field": k, "before": flat_b.get(k), "after": flat_a.get(k)})

    cash_delta = q2(
        fin_after.scenarios["base"].ending_cash_balance
        - fin_before.scenarios["base"].ending_cash_balance
    )
    cac_b = fin_before.reverse_frontier.max_viable_cac
    cac_a = fin_after.reverse_frontier.max_viable_cac
    cac_delta = q2(cac_a - cac_b) if (cac_a is not None and cac_b is not None) else None

    verdict_changed = dec_before.verdict != dec_after.verdict
    summary = (
        f"Verdict shifted {dec_before.verdict.value} -> {dec_after.verdict.value} "
        if verdict_changed
        else f"Verdict held at {dec_after.verdict.value} "
    ) + f"after {len(changed)} assumption change(s); base ending cash delta: {fin_after.currency} {cash_delta:+,.2f}."

    return LedgerDiffResult(
        previous_verdict=dec_before.verdict,
        new_verdict=dec_after.verdict,
        verdict_changed=verdict_changed,
        changed_assumptions=changed,
        ending_cash_delta=cash_delta,
        max_viable_cac_delta=cac_delta,
        summary=summary,
    )
