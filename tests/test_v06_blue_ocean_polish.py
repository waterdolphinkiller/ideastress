"""Unit & integration tests for IdeaStress v0.6.0 Blue-Ocean features (Geo-Arbitrage, Scope-Creep FinOps, Proof Card)."""

import json
import unittest
from decimal import Decimal

from click.testing import CliRunner

from ideastress.cli import main as cli_main
from ideastress.domain.models import AnalysisRequest, BusinessType, FinancialInputs
from ideastress.finance.scope_gate import check_scope_creep_finops
from ideastress.mcp.server import handle_jsonrpc_request
from ideastress.orchestration.runner import AnalysisOrchestrator
from ideastress.providers.geo_arbitrage import scan_geo_arbitrage
from ideastress.reports.proof_card import render_proof_card_svg


class TestV06BlueOceanPolish(unittest.TestCase):
    def test_geo_arbitrage_finds_viable_market_when_us_is_impossible(self):
        # Accounting US mock CPC = $8.90 -> implied CAC $356 at 2.5% CVR.
        # With US max viable CAC = $200, US fails (CHANNEL_IMPOSSIBLE) while MY ($2.31 CPC -> $92 CAC vs $110 localized ceiling) succeeds!
        rep = scan_geo_arbitrage(
            ["small business accounting software"],
            us_max_viable_cac_usd=Decimal("200"),
            assumed_conversion_rate=Decimal("0.025"),
        )
        self.assertEqual(len(rep.markets), 5)
        us = next(m for m in rep.markets if m.market_code == "US")
        my = next(m for m in rep.markets if m.market_code == "MY")
        self.assertEqual(us.verdict, "CHANNEL_IMPOSSIBLE")
        self.assertNotEqual(my.verdict, "CHANNEL_IMPOSSIBLE")
        self.assertEqual(rep.best_market, "MY")

    def test_scope_creep_finops_blocks_margin_destroying_feature(self):
        base = FinancialInputs(
            business_type=BusinessType.SAAS,
            unit_price=Decimal("29"),
            variable_cost_per_unit=Decimal("3"),
            fixed_monthly_costs=Decimal("600"),
            monthly_new_customers=20,
            monthly_acquisition_spend=Decimal("400"),
            monthly_churn_rate=Decimal("0.05"),
            starting_cash=Decimal("10000"),
        )
        # Adding a $28/user/mo video API destroys margin -> BLOCK_SCOPE_CREEP
        res_bad = check_scope_creep_finops(
            base,
            feature_name="Unlimited 4K AI Video Generation",
            extra_monthly_cogs_per_user=Decimal("28"),
        )
        self.assertEqual(res_bad.verdict, "BLOCK_SCOPE_CREEP")
        self.assertGreater(res_bad.recommended_addon_price, Decimal("100"))

        # Adding a $1/user/mo webhook feature -> APPROVE_IN_BASE_PLAN
        res_ok = check_scope_creep_finops(
            base,
            feature_name="Slack Webhook Alerts",
            extra_monthly_cogs_per_user=Decimal("1"),
        )
        self.assertEqual(res_ok.verdict, "APPROVE_IN_BASE_PLAN")

    def test_proof_card_svg_renders_valid_1200x630_social_card(self):
        orch = AnalysisOrchestrator()
        res = orch.run(
            AnalysisRequest(
                idea="AI bookkeeping SaaS for freelancers",
                business_type=BusinessType.SAAS,
                financials=FinancialInputs(unit_price=Decimal("49"), starting_cash=Decimal("12000")),
            ),
            save_to_db=False,
        )
        svg = render_proof_card_svg(res)
        self.assertIn('viewBox="0 0 1200 630"', svg)
        self.assertIn("IDEASTRESS // PROOF CARD", svg)
        self.assertIn("Stress-tested with IdeaStress", svg)

    def test_v06_mcp_10_tools_and_cli_commands(self):
        list_resp = handle_jsonrpc_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = [t["name"] for t in list_resp["result"]["tools"]]
        self.assertGreaterEqual(len(names), 10)
        self.assertIn("scan_geo_arbitrage", names)
        self.assertIn("check_scope_creep_finops", names)

        m_geo = handle_jsonrpc_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "scan_geo_arbitrage", "arguments": {"keywords": ["accounting software"], "us_max_viable_cac_usd": 200}},
            }
        )
        p_geo = json.loads(m_geo["result"]["content"][0]["text"])
        self.assertEqual(p_geo["best_market"], "MY")

        runner = CliRunner()
        r1 = runner.invoke(cli_main, ["geo-scan", "--keywords", "accounting software", "--us-max-cac", "200"])
        self.assertEqual(r1.exit_code, 0)
        self.assertIn('"best_market": "MY"', r1.output)

        r2 = runner.invoke(cli_main, ["scope-gate", "--price", "29", "--feature", "4K AI Video", "--extra-cogs", "28"])
        self.assertEqual(r2.exit_code, 0)
        self.assertIn("BLOCK_SCOPE_CREEP", r2.output)


if __name__ == "__main__":
    unittest.main()
