"""End-to-end integration tests for Orchestrator, Budget Cutoff, SQLite, Reports, MCP Server, and CLI."""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from click.testing import CliRunner

from ideastress.cli import main as cli_main
from ideastress.config import BudgetConfig, IdeaStressConfig
from ideastress.domain.models import AnalysisRequest, BusinessType, FinancialInputs, RunStatus
from ideastress.mcp.server import handle_jsonrpc_request
from ideastress.orchestration.runner import AnalysisOrchestrator
from ideastress.reports.renderer import render_html, render_json, render_markdown
from ideastress.storage.sqlite_store import SQLiteAnalysisStore


class TestEndToEndPipelineMcpCli(unittest.TestCase):
    def test_orchestrator_full_run_sqlite_and_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            store = SQLiteAnalysisStore(db_path)
            orch = AnalysisOrchestrator(store=store)
            req = AnalysisRequest(
                idea="AI bookkeeping SaaS for US freelancers",
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
            )
            res = orch.run(req)
            self.assertEqual(res.status, RunStatus.COMPLETED)
            self.assertGreaterEqual(len(res.competitors), 3)
            self.assertGreaterEqual(len(res.base_rate_checks), 2)
            self.assertGreaterEqual(len(res.kill_tests), 2)

            # SQLite roundtrip
            loaded = store.get(res.analysis_id)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.analysis_id, res.analysis_id)
            self.assertEqual(len(store.list_recent()), 1)

            # Reports
            md = render_markdown(res)
            html = render_html(res)
            js = render_json(res)
            self.assertIn("Reverse Unit-Economics Survival Frontier", md)
            self.assertIn("Interactive Live Reverse Unit-Economics Stress Tester", html)
            self.assertEqual(json.loads(js)["analysis_id"], res.analysis_id)

    def test_budget_cutoff_returns_partial_budget_limit(self):
        cfg = IdeaStressConfig(
            budget=BudgetConfig(max_search_calls=0, max_pages_fetched=0, max_llm_calls=1)
        )
        orch = AnalysisOrchestrator(config=cfg)
        req = AnalysisRequest(idea="Test budget cutoff SaaS", business_type=BusinessType.SAAS)
        res = orch.run(req, save_to_db=False)
        self.assertEqual(res.status, RunStatus.PARTIAL_BUDGET_LIMIT)
        self.assertTrue(res.budget_usage.limit_reached)

    def test_mcp_jsonrpc_server_initialize_list_and_call(self):
        init_resp = handle_jsonrpc_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(init_resp["result"]["serverInfo"]["name"], "ideastress-mcp")

        list_resp = handle_jsonrpc_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tool_names = [t["name"] for t in list_resp["result"]["tools"]]
        self.assertIn("precode_gate_check", tool_names)
        self.assertIn("solve_unit_frontiers", tool_names)
        self.assertIn("diff_assumption_ledger", tool_names)
        self.assertIn("get_industry_base_rates", tool_names)

        call_resp = handle_jsonrpc_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "precode_gate_check",
                    "arguments": {
                        "idea": "Micro-SaaS invoice reminder tool",
                        "unit_price": 29,
                        "fixed_monthly_costs": 400,
                        "monthly_new_customers": 15,
                        "starting_cash": 8000,
                    },
                },
            }
        )
        payload = json.loads(call_resp["result"]["content"][0]["text"])
        self.assertIn("verdict", payload)
        self.assertIn("reverse_frontier", payload)
        self.assertIn("top_kill_test", payload)

    def test_cli_commands_work_end_to_end(self):
        runner = CliRunner()
        r_doc = runner.invoke(cli_main, ["doctor"])
        self.assertEqual(r_doc.exit_code, 0)
        self.assertIn("llm_provider", r_doc.output)

        r_solve = runner.invoke(cli_main, ["solve", "--price", "49", "--cash", "10000"])
        self.assertEqual(r_solve.exit_code, 0)
        self.assertIn("max_viable_cac", r_solve.output)

        r_bench = runner.invoke(cli_main, ["benchmarks", "--type", "saas"])
        self.assertEqual(r_bench.exit_code, 0)
        self.assertIn("chartmogul.com", r_bench.output)


if __name__ == "__main__":
    unittest.main()
