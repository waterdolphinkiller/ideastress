"""Tests for v0.4.0 Real CPC -> Implied CAC Falsification Engine & 30-day SQLite Cache."""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from click.testing import CliRunner

from ideastress.cli import main as cli_main
from ideastress.mcp.server import handle_jsonrpc_request
from ideastress.providers.cpc import MockCPCProvider, evaluate_paid_channel_falsification
from ideastress.storage.cache import SQLiteSignalCache


class TestCPCFalsifierAndSQLiteCache(unittest.TestCase):
    def test_sqlite_cache_hit_and_ttl_expiration(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = SQLiteSignalCache(Path(tmp) / "cache.db")
            val, hit = cache.get("keyword_cpc", "k1", now=1000.0)
            self.assertFalse(hit)
            self.assertIsNone(val)

            cache.set("keyword_cpc", "k1", {"cpc": "8.90"}, ttl_days=30.0, now=1000.0)
            val2, hit2 = cache.get("keyword_cpc", "k1", now=1000.0 + 86400.0)
            self.assertTrue(hit2)
            self.assertEqual(val2["cpc"], "8.90")

            # After 31 days -> expired
            val3, hit3 = cache.get("keyword_cpc", "k1", now=1000.0 + 31 * 86400.0)
            self.assertFalse(hit3)
            self.assertIsNone(val3)

    def test_cpc_falsifier_flags_channel_impossible_and_uses_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = SQLiteSignalCache(Path(tmp) / "cache.db")
            # Accounting keywords mock avg CPC = $8.90; at 2.5% CVR -> implied CAC = $356.00!
            # With max_viable_cac = $80 -> MUST be CHANNEL_IMPOSSIBLE
            res1 = evaluate_paid_channel_falsification(
                ["small business accounting software", "freelance bookkeeping"],
                max_viable_cac=Decimal("80.00"),
                assumed_conversion_rate=Decimal("0.025"),
                provider=MockCPCProvider(),
                cache=cache,
            )
            self.assertFalse(res1.cache_hit)
            self.assertEqual(res1.verdict, "CHANNEL_IMPOSSIBLE")
            self.assertEqual(res1.implied_paid_cac, Decimal("356.00"))
            self.assertGreater(res1.required_conversion_rate_for_cpc_pct, Decimal("10.00"))

            # Second identical call MUST hit SQLite cache
            res2 = evaluate_paid_channel_falsification(
                ["small business accounting software", "freelance bookkeeping"],
                max_viable_cac=Decimal("80.00"),
                assumed_conversion_rate=Decimal("0.025"),
                provider=MockCPCProvider(),
                cache=cache,
            )
            self.assertTrue(res2.cache_hit)
            self.assertEqual(res2.keywords_analyzed[0].source, "sqlite_cache")
            self.assertEqual(res2.verdict, "CHANNEL_IMPOSSIBLE")

    def test_cpc_falsifier_channel_viable_when_headroom_high(self):
        # Supplement mock CPC = $2.45; at 2.5% CVR -> implied CAC = $98.00; max_viable_cac = $250 -> VIABLE
        res = evaluate_paid_channel_falsification(
            ["magnesium sleep supplement"],
            max_viable_cac=Decimal("250.00"),
            assumed_conversion_rate=Decimal("0.025"),
            provider=MockCPCProvider(),
        )
        self.assertEqual(res.verdict, "CHANNEL_VIABLE")
        self.assertEqual(res.implied_paid_cac, Decimal("98.00"))

    def test_mcp_falsify_paid_channel_and_cli_cpc_check(self):
        resp = handle_jsonrpc_request(
            {
                "jsonrpc": "2.0",
                "id": 99,
                "method": "tools/call",
                "params": {
                    "name": "falsify_paid_channel",
                    "arguments": {
                        "keywords": ["small business accounting software"],
                        "max_viable_cac": 60,
                        "assumed_conversion_rate": 0.02,
                    },
                },
            }
        )
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(payload["verdict"], "CHANNEL_IMPOSSIBLE")
        self.assertEqual(payload["implied_paid_cac"], 445.0)

        runner = CliRunner()
        r = runner.invoke(
            cli_main,
            ["cpc-check", "--keywords", "small business accounting software", "--max-cac", "60", "--cvr", "0.02"],
        )
        self.assertEqual(r.exit_code, 0)
        self.assertIn("CHANNEL_IMPOSSIBLE", r.output)


if __name__ == "__main__":
    unittest.main()
