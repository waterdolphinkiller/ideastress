"""Unit tests for EvidenceStore, automatic downgrade audit, and Ledger Diff."""

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from ideastress.domain.models import (
    AnalysisRequest,
    BusinessType,
    Claim,
    ClaimStatus,
    Evidence,
    FinancialInputs,
    SourceReliability,
    Verdict,
)
from ideastress.evidence.store import EvidenceStore
from ideastress.ledger.diff import diff_ledgers, load_ledger_yaml, save_ledger_yaml


class TestEvidenceAuditAndLedgerDiff(unittest.TestCase):
    def test_unbacked_verified_claim_is_downgraded(self):
        store = EvidenceStore()
        c = Claim(
            statement="Market is growing at 40% CAGR.",
            claim_type="market_growth",
            status=ClaimStatus.VERIFIED,
        )
        store.add_claim(c)
        audit = store.audit_claims()
        self.assertFalse(audit.passed)
        self.assertEqual(audit.downgraded_claims, 1)
        self.assertEqual(store.all_claims()[0].status, ClaimStatus.UNKNOWN)

    def test_user_input_cannot_remain_verified(self):
        store = EvidenceStore()
        ev = store.add_evidence(
            Evidence(
                title="Founder estimate",
                snippet="I think conversion will be 10%",
                source_reliability=SourceReliability.USER_INPUT,
            )
        )
        c = store.add_claim(
            Claim(
                statement="Conversion will be 10%",
                claim_type="conversion",
                status=ClaimStatus.VERIFIED,
                supporting_evidence_ids=[ev.evidence_id],
            )
        )
        audit = store.audit_claims()
        self.assertFalse(audit.passed)
        self.assertEqual(c.status, ClaimStatus.ASSUMPTION)

    def test_contradicting_evidence_forces_contradicted(self):
        store = EvidenceStore()
        e1 = store.add_evidence(
            Evidence(
                title="Official pricing",
                url="https://example.com/pricing",
                snippet="Free tier included",
                source_reliability=SourceReliability.PRIMARY,
            )
        )
        e2 = store.add_evidence(
            Evidence(
                title="Changelog",
                url="https://example.com/changelog",
                snippet="Free tier sunset on Oct 2026",
                source_reliability=SourceReliability.PRIMARY,
            )
        )
        c = store.add_claim(
            Claim(
                statement="Competitor offers a free tier.",
                claim_type="competitor_pricing",
                status=ClaimStatus.VERIFIED,
                supporting_evidence_ids=[e1.evidence_id],
                contradicting_evidence_ids=[e2.evidence_id],
            )
        )
        audit = store.audit_claims()
        self.assertEqual(audit.contradictions_found, 1)
        self.assertEqual(c.status, ClaimStatus.CONTRADICTED)

    def test_ledger_yaml_roundtrip_and_verdict_diff(self):
        req_before = AnalysisRequest(
            idea="AI Bookkeeping SaaS for freelancers",
            customer_segment="US solo freelancers",
            business_type=BusinessType.SAAS,
            budget=Decimal("15000"),
            currency="USD",
            financials=FinancialInputs(
                business_type=BusinessType.SAAS,
                currency="USD",
                unit_price=Decimal("49"),
                variable_cost_per_unit=Decimal("5"),
                fixed_monthly_costs=Decimal("800"),
                monthly_new_customers=15,
                monthly_acquisition_spend=Decimal("450"),
                monthly_churn_rate=Decimal("0.05"),
                starting_cash=Decimal("15000"),
            ),
        )
        # After running real ad test: unit cost jumps and price drops -> mathematically impossible
        req_after = AnalysisRequest(
            idea="AI Bookkeeping SaaS for freelancers",
            customer_segment="US solo freelancers",
            business_type=BusinessType.SAAS,
            budget=Decimal("15000"),
            currency="USD",
            financials=FinancialInputs(
                business_type=BusinessType.SAAS,
                currency="USD",
                unit_price=Decimal("15"),
                variable_cost_per_unit=Decimal("18"),
                fixed_monthly_costs=Decimal("800"),
                monthly_new_customers=15,
                monthly_acquisition_spend=Decimal("1200"),
                monthly_churn_rate=Decimal("0.08"),
                starting_cash=Decimal("15000"),
            ),
        )

        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "v1.yaml"
            save_ledger_yaml(req_before, p1)
            loaded = load_ledger_yaml(p1)
            self.assertEqual(loaded.idea, req_before.idea)

        diff = diff_ledgers(req_before, req_after)
        self.assertTrue(diff.verdict_changed)
        self.assertEqual(diff.new_verdict, Verdict.NO_GO)
        self.assertLess(diff.ending_cash_delta, Decimal("0"))
        self.assertGreaterEqual(len(diff.changed_assumptions), 3)


if __name__ == "__main__":
    unittest.main()
