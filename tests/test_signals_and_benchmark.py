"""Tests for Competitor Complaint Signal Adapters and the 10-Case Industry Benchmark Suite."""

import json
import unittest

from click.testing import CliRunner

from ideastress.benchmarks.suite import run_benchmark_suite
from ideastress.cli import main as cli_main
from ideastress.domain.models import SourceReliability
from ideastress.mcp.server import handle_jsonrpc_request
from ideastress.providers.signals import (
    aggregate_pain_themes,
    classify_pain_tags,
    collect_complaint_signals,
)


class TestSignalsAndBenchmarkSuite(unittest.TestCase):
    def test_pain_tag_classification_and_evidence_conversion(self):
        tags = classify_pain_tags("Way too expensive after price hike and customer support ghosted me.")
        self.assertIn("pricing_and_billing", tags)
        self.assertIn("customer_support", tags)

        signals = collect_complaint_signals("AI accounting SaaS", mode="mock")
        self.assertGreaterEqual(len(signals), 3)
        ev = signals[0].to_evidence()
        self.assertEqual(ev.source_reliability, SourceReliability.QUALITATIVE)
        self.assertTrue(ev.url.startswith("https://"))

        themes = aggregate_pain_themes(signals)
        self.assertIn("pricing_and_billing", themes)

    def test_mcp_scan_competitor_complaints_tool(self):
        resp = handle_jsonrpc_request(
            {
                "jsonrpc": "2.0",
                "id": 42,
                "method": "tools/call",
                "params": {
                    "name": "scan_competitor_complaints",
                    "arguments": {"query": "accounting SaaS", "mode": "mock"},
                },
            }
        )
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertGreaterEqual(payload["total_signals"], 3)
        self.assertIn("pain_themes", payload)

    def test_ten_case_benchmark_suite_passes_100_pct(self):
        summary = run_benchmark_suite()
        self.assertEqual(summary["total_cases"], 10)
        self.assertEqual(summary["passed_cases"], 10)
        self.assertEqual(summary["unsupported_verified_claim_rate_pct"], 0.0)
        self.assertEqual(summary["kill_test_coverage_pct"], 100.0)

    def test_cli_signals_and_benchmark_run(self):
        runner = CliRunner()
        r1 = runner.invoke(cli_main, ["signals", "accounting SaaS"])
        self.assertEqual(r1.exit_code, 0)
        self.assertIn("pricing_and_billing", r1.output)

        r2 = runner.invoke(cli_main, ["benchmark-run"])
        self.assertEqual(r2.exit_code, 0)
        self.assertIn('"passed_cases": 10', r2.output)


if __name__ == "__main__":
    unittest.main()
