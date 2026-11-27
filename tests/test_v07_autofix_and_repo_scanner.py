"""Tests for IdeaStress v0.7.0 Auto-Fix Prescriptions (incl. Annual Prepay) & Repo Cost Scanner."""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from click.testing import CliRunner

from ideastress.cli import main as cli_main
from ideastress.domain.models import BusinessType, FinancialInputs
from ideastress.finance.autofix import generate_autofix_prescriptions
from ideastress.finance.repo_scanner import scan_repo_api_costs
from ideastress.mcp.server import handle_jsonrpc_request


class TestV07AutoFixAndRepoScanner(unittest.TestCase):
    def test_autofix_generates_exact_rescue_prescriptions_and_annual_prepay(self):
        # Struggling SaaS: $18 price, $4 var cost, $1500 fixed, $450 ad spend, 9% churn, $5000 cash -> low survival
        struggling = FinancialInputs(
            business_type=BusinessType.SAAS,
            currency="USD",
            unit_price=Decimal("18"),
            variable_cost_per_unit=Decimal("4"),
            fixed_monthly_costs=Decimal("1500"),
            monthly_new_customers=14,
            monthly_acquisition_spend=Decimal("450"),
            monthly_churn_rate=Decimal("0.09"),
            starting_cash=Decimal("5000"),
        )
        rep = generate_autofix_prescriptions(struggling, target_survival_pct=Decimal("85.00"))
        self.assertFalse(rep.already_healthy)
        self.assertLess(rep.baseline_survival_pct, Decimal("85.00"))
        levers = {p.lever: p for p in rep.prescriptions}
        self.assertIn("price_raise", levers)
        self.assertTrue(levers["price_raise"].achievable)
        self.assertGreaterEqual(levers["price_raise"].resulting_survival_pct, Decimal("85.00"))
        self.assertIn("annual_prepay_plan", levers)
        self.assertGreater(levers["annual_prepay_plan"].resulting_survival_pct, rep.baseline_survival_pct)

    def test_repo_cost_scanner_detects_expensive_model_loop_and_missing_cap(self):
        sample_code = """
import openai

def process_batch(items):
    for item in items:
        resp = openai.chat.completions.create(
            model="o1",
            messages=[{"role": "user", "content": item}],
        )
    return resp
"""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "worker.py"
            p.write_text(sample_code, encoding="utf-8")
            audit = scan_repo_api_costs(tmp, subscription_price_usd=Decimal("19"), assumed_daily_calls_per_user=20)
            self.assertEqual(audit.files_scanned, 1)
            self.assertIn("openai", audit.sdks_detected)
            self.assertIn("o1", audit.models_detected)
            rule_ids = {f.rule_id for f in audit.findings}
            self.assertIn("UNBOUNDED_LOOP_COST", rule_ids)
            self.assertIn("MISSING_TOKEN_CAP", rule_ids)
            self.assertIn("HIGH_COST_MODEL", rule_ids)
            self.assertEqual(audit.verdict, "BANKRUPTCY_RISK")

    def test_v07_mcp_12_tools_and_cli_commands(self):
        list_resp = handle_jsonrpc_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = [t["name"] for t in list_resp["result"]["tools"]]
        self.assertEqual(len(names), 12)
        self.assertIn("auto_fix_unit_economics", names)
        self.assertIn("scan_repo_api_costs", names)

        m_fix = handle_jsonrpc_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "auto_fix_unit_economics",
                    "arguments": {"unit_price": 18, "fixed_monthly_costs": 1500, "starting_cash": 5000, "monthly_churn_rate": 0.09},
                },
            }
        )
        p_fix = json.loads(m_fix["result"]["content"][0]["text"])
        self.assertFalse(p_fix["already_healthy"])
        self.assertGreaterEqual(len(p_fix["prescriptions"]), 2)

        runner = CliRunner()
        r_fix = runner.invoke(cli_main, ["autofix", "--price", "18", "--fixed-cost", "1500", "--cash", "5000", "--churn", "0.09"])
        self.assertEqual(r_fix.exit_code, 0)
        self.assertIn("price_raise", r_fix.output)

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "app.py").write_text('import anthropic\nclient.messages.create(model="claude-3-opus", max_tokens=500)\n', encoding="utf-8")
            r_scan = runner.invoke(cli_main, ["scan-repo", tmp, "--price", "19"])
            self.assertEqual(r_scan.exit_code, 0)
            self.assertIn("BANKRUPTCY_RISK", r_scan.output)


if __name__ == "__main__":
    unittest.main()
