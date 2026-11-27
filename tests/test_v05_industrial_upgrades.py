"""Comprehensive tests for IdeaStress v0.5.0 industrial-grade upgrades."""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from click.testing import CliRunner

from ideastress.cli import main as cli_main
from ideastress.domain.models import AnalysisRequest, BusinessType, FinancialInputs, IdeaBrief
from ideastress.experiments.kit import generate_kill_test_kit, save_kill_test_kit
from ideastress.finance.ai_unit import AITokenMarginInputs, stress_test_ai_token_margin
from ideastress.mcp.server import handle_jsonrpc_request
from ideastress.orchestration.runner import AnalysisOrchestrator
from ideastress.providers.openai_compat import OpenAICompatibleLLMProvider
from ideastress.providers.price_radar import check_price_drift
from ideastress.providers.signals import collect_complaint_signals
from ideastress.reports.renderer import render_html, render_markdown
from ideastress.storage.cache import SQLiteSignalCache


class TestV05IndustrialUpgrades(unittest.TestCase):
    def test_self_healing_llm_retries_malformed_json_and_recovers(self):
        attempts = {"count": 0}

        def flaky_transport(messages):
            attempts["count"] += 1
            if attempts["count"] == 1:
                return '{"problem_statement": "missing required fields"}'
            return json.dumps(
                {
                    "problem_statement": "Manual invoicing wastes hours",
                    "proposed_solution": "Automated invoicing SaaS",
                    "customer_segments": ["US freelancers"],
                    "value_proposition": "Save 5 hours/week",
                    "revenue_model": "saas",
                    "channels": ["SEO"],
                }
            )

        prov = OpenAICompatibleLLMProvider(api_key="", max_retries=2, transport_fn=flaky_transport)
        brief = prov.generate_structured(
            system_prompt="Structure idea",
            user_prompt="Test",
            output_schema=IdeaBrief,
        )
        self.assertEqual(attempts["count"], 2)
        self.assertEqual(brief.revenue_model, "saas")

    def test_complaint_signals_use_7_day_sqlite_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = SQLiteSignalCache(Path(tmp) / "sig.db")
            s1 = collect_complaint_signals("accounting SaaS", mode="mock", cache=cache)
            self.assertGreaterEqual(len(s1), 3)
            self.assertEqual(cache.stats()["misses"], 1)

            s2 = collect_complaint_signals("accounting SaaS", mode="mock", cache=cache)
            self.assertEqual(len(s2), len(s1))
            self.assertEqual(cache.stats()["hits"], 1)

    def test_reports_include_monte_carlo_and_cpc_falsification(self):
        orch = AnalysisOrchestrator()
        res = orch.run(
            AnalysisRequest(
                idea="AI bookkeeping SaaS for US freelancers",
                business_type=BusinessType.SAAS,
                financials=FinancialInputs(unit_price=Decimal("49"), starting_cash=Decimal("12000")),
            ),
            save_to_db=False,
        )
        md = render_markdown(res)
        html = render_html(res)
        self.assertIn("Monte Carlo Survival Probability", md)
        self.assertIn("Paid Search CPC Falsification", md)
        self.assertIn("Monte Carlo Survival (1,000 runs)", html)
        self.assertIn("Paid Search CPC Check", html)

    def test_ai_token_margin_and_whale_bankruptcy_limit(self):
        # Frontier model on $19/mo flat plan with 40 reqs/day -> MUST be negative unit margin!
        bad = stress_test_ai_token_margin(
            AITokenMarginInputs(
                subscription_price_usd=Decimal("19"),
                daily_requests_per_user=40,
                avg_input_tokens=4000,
                avg_output_tokens=1200,
                model_preset="frontier_reasoning",
            )
        )
        self.assertEqual(bad.verdict, "NEGATIVE_UNIT_MARGIN")
        self.assertLess(bad.monthly_gross_profit_per_user_usd, Decimal("0"))

        good = stress_test_ai_token_margin(
            AITokenMarginInputs(
                subscription_price_usd=Decimal("49"),
                daily_requests_per_user=15,
                avg_input_tokens=2000,
                avg_output_tokens=600,
                model_preset="budget_fast",
            )
        )
        self.assertEqual(good.verdict, "HEALTHY_AI_MARGIN")
        self.assertGreater(good.whale_break_even_daily_requests, 500)

    def test_kill_test_kit_generation_and_disk_export(self):
        req = AnalysisRequest(
            idea="Simple bookkeeping for solo US freelancers",
            customer_segment="US solo freelancers",
            financials=FinancialInputs(unit_price=Decimal("39")),
        )
        kit = generate_kill_test_kit(req, pain_themes={"pricing_and_billing": 3}, max_viable_cac=Decimal("95"))
        self.assertEqual(len(kit.ad_copies), 3)
        self.assertEqual(len(kit.mom_test_questions), 15)
        self.assertIn("FOUNDING PILOT", kit.landing_page_html)

        with tempfile.TemporaryDirectory() as tmp:
            out = save_kill_test_kit(kit, Path(tmp) / "kit")
            self.assertTrue((out / "smoke_test_landing.html").exists())
            self.assertTrue((out / "kill_test_playbook.md").exists())

    def test_price_drift_radar_detects_price_hike_and_free_tier_sunset(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = SQLiteSignalCache(Path(tmp) / "radar.db")
            url = "https://competitor.example.com/pricing"
            r1 = check_price_drift(url, "Free tier forever! Pro plan $19/mo.", cache)
            self.assertEqual(r1.status, "INITIAL_BASELINE")

            r2 = check_price_drift(url, "Free tier forever! Pro plan $29/mo.", cache)
            self.assertEqual(r2.status, "PRICE_INCREASE")
            self.assertEqual(r2.previous_min_price, "19")
            self.assertEqual(r2.current_min_price, "29")

            r3 = check_price_drift(url, "Starter plan $29/mo. Enterprise $99/mo.", cache)
            self.assertEqual(r3.status, "FREE_TIER_REMOVED")

    def test_v05_mcp_and_cli_commands(self):
        m1 = handle_jsonrpc_request(
            {
                "jsonrpc": "2.0",
                "id": 101,
                "method": "tools/call",
                "params": {"name": "stress_test_ai_margin", "arguments": {"subscription_price_usd": 29, "model_preset": "mid_balanced"}},
            }
        )
        p1 = json.loads(m1["result"]["content"][0]["text"])
        self.assertIn("whale_break_even_daily_requests", p1)

        runner = CliRunner()
        r_ai = runner.invoke(cli_main, ["ai-margin", "--price", "29", "--model", "mid_balanced"])
        self.assertEqual(r_ai.exit_code, 0)
        self.assertIn("whale_break_even_daily_requests", r_ai.output)


if __name__ == "__main__":
    unittest.main()
