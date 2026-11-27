"""Zero-dependency JSON-RPC 2.0 stdio MCP Server for IdeaStress v0.5.0 (8 Tools)."""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from typing import Any, Dict, List

from ideastress.benchmarks.base_rates import get_base_rates_for
from ideastress.config import IdeaStressConfig
from ideastress.domain.models import AnalysisMode, AnalysisRequest, BusinessType, FinancialInputs
from ideastress.experiments.kit import generate_kill_test_kit
from ideastress.finance.ai_unit import AITokenMarginInputs, stress_test_ai_token_margin
from ideastress.finance.autofix import generate_autofix_prescriptions
from ideastress.finance.repo_scanner import scan_repo_api_costs
from ideastress.finance.scope_gate import check_scope_creep_finops
from ideastress.finance.solver import solve_reverse_frontier
from ideastress.providers.geo_arbitrage import scan_geo_arbitrage
from ideastress.ledger.diff import diff_ledgers, load_ledger_yaml
from ideastress.orchestration.runner import AnalysisOrchestrator
from ideastress.providers.cpc import DataForSEOCPCProvider, MockCPCProvider, evaluate_paid_channel_falsification
from ideastress.providers.signals import aggregate_pain_themes, collect_complaint_signals
from ideastress.storage.cache import SQLiteSignalCache

MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "precode_gate_check",
        "description": "Fast, token-efficient Pre-Code Gate Check before writing code. Returns verdict, mathematical CAC/price/churn bounds, 1,000-run Monte Carlo survival probability, CPC channel falsification, base-rate warnings, and #1 Kill Test.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "idea": {"type": "string"},
                "business_type": {"type": "string", "enum": ["saas", "digital_product", "ecommerce", "local_service", "marketplace"]},
                "customer_segment": {"type": "string"},
                "unit_price": {"type": "number"},
                "variable_cost_per_unit": {"type": "number", "default": 5},
                "fixed_monthly_costs": {"type": "number", "default": 500},
                "monthly_new_customers": {"type": "integer", "default": 10},
                "monthly_acquisition_spend": {"type": "number", "default": 300},
                "monthly_churn_rate": {"type": "number", "default": 0.06},
                "starting_cash": {"type": "number", "default": 10000},
                "currency": {"type": "string", "default": "USD"},
            },
            "required": ["idea", "unit_price"],
        },
    },
    {
        "name": "solve_unit_frontiers",
        "description": "Deterministic Reverse Unit-Economics Solver ($0 LLM cost). Computes max_viable_cac, min_viable_unit_price, max_tolerable_monthly_churn_pct, and min_monthly_new_customers_to_survive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "business_type": {"type": "string", "default": "saas"},
                "unit_price": {"type": "number"},
                "variable_cost_per_unit": {"type": "number", "default": 0},
                "fixed_monthly_costs": {"type": "number", "default": 0},
                "monthly_new_customers": {"type": "integer", "default": 10},
                "monthly_acquisition_spend": {"type": "number", "default": 0},
                "monthly_churn_rate": {"type": "number", "default": 0.05},
                "starting_cash": {"type": "number", "default": 10000},
                "horizon_months": {"type": "integer", "default": 12},
                "currency": {"type": "string", "default": "USD"},
            },
            "required": ["unit_price"],
        },
    },
    {
        "name": "falsify_paid_channel",
        "description": "Cross-check Google Ads keyword CPCs (DataForSEO or offline mock + 30-day SQLite cache) against max_viable_cac to detect CHANNEL_IMPOSSIBLE paid acquisition traps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keywords": {"type": "array", "items": {"type": "string"}},
                "max_viable_cac": {"type": "number"},
                "assumed_conversion_rate": {"type": "number", "default": 0.025},
                "location_code": {"type": "integer", "default": 2840},
            },
            "required": ["keywords", "max_viable_cac"],
        },
    },
    {
        "name": "stress_test_ai_margin",
        "description": "Stress-test an AI wrapper SaaS subscription price against LLM token COGS, Stripe US fees, and calculate the Whale Bankruptcy daily request threshold.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subscription_price_usd": {"type": "number"},
                "daily_requests_per_user": {"type": "integer", "default": 20},
                "avg_input_tokens": {"type": "integer", "default": 2500},
                "avg_output_tokens": {"type": "integer", "default": 800},
                "model_preset": {"type": "string", "enum": ["budget_fast", "mid_balanced", "frontier_reasoning"], "default": "mid_balanced"},
            },
            "required": ["subscription_price_usd"],
        },
    },
    {
        "name": "generate_kill_test_kit",
        "description": "Generate an executable smoke-test bundle: 3 ad copies, 15 Mom-Test discovery questions, and a deploy-ready landing page HTML.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "idea": {"type": "string"},
                "customer_segment": {"type": "string"},
                "unit_price": {"type": "number", "default": 49},
            },
            "required": ["idea"],
        },
    },
    {
        "name": "scan_competitor_complaints",
        "description": "Scan Reddit, App Store (1-3 star reviews), and G2 for real competitor complaint signals and clustered pain themes (with 7-day SQLite cache).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "mode": {"type": "string", "enum": ["mock", "live"], "default": "mock"},
                "limit_per_platform": {"type": "integer", "default": 3},
            },
            "required": ["query"],
        },
    },
    {
        "name": "diff_assumption_ledger",
        "description": "Compare two venture.yaml assumption ledgers (before vs. after a real-world experiment) and return exact cash, CAC ceiling, and verdict delta.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "before_yaml_path": {"type": "string"},
                "after_yaml_path": {"type": "string"},
            },
            "required": ["before_yaml_path", "after_yaml_path"],
        },
    },
    {
        "name": "get_industry_base_rates",
        "description": "Retrieve source-cited 2025-2026 industry base rates (churn, conversion rate, CAC, margins, take rates) for reality calibration.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "business_type": {"type": "string", "enum": ["saas", "digital_product", "ecommerce", "local_service", "marketplace"]}
            },
            "required": ["business_type"],
        },
    },
    {
        "name": "scan_geo_arbitrage",
        "description": "Compare paid search CPC & localized survival viability across 5 countries (US, UK, DE, SG, MY) to find blue-ocean geo-arbitrage markets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keywords": {"type": "array", "items": {"type": "string"}},
                "us_max_viable_cac_usd": {"type": "number"},
                "assumed_conversion_rate": {"type": "number", "default": 0.025}
            },
            "required": ["keywords", "us_max_viable_cac_usd"]
        }
    },
    {
        "name": "check_scope_creep_finops",
        "description": "Coding-time FinOps gate: checks how a proposed feature's extra per-user monthly COGS impacts gross margin and 1,000-run Monte Carlo survival before writing code.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "unit_price": {"type": "number"},
                "current_variable_cost": {"type": "number", "default": 5},
                "fixed_monthly_costs": {"type": "number", "default": 600},
                "starting_cash": {"type": "number", "default": 10000},
                "feature_name": {"type": "string"},
                "extra_monthly_cogs_per_user": {"type": "number"}
            },
            "required": ["unit_price", "feature_name", "extra_monthly_cogs_per_user"]
        }
    },
    {
        "name": "auto_fix_unit_economics",
        "description": "Compute exact Minimum Viable Fix prescriptions (price raise, churn cut, ad spend cap, or 20%-off annual prepay plan) to lift 12m Monte Carlo survival to >=85%.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "business_type": {"type": "string", "default": "saas"},
                "unit_price": {"type": "number"},
                "variable_cost_per_unit": {"type": "number", "default": 5},
                "fixed_monthly_costs": {"type": "number", "default": 1000},
                "monthly_new_customers": {"type": "integer", "default": 12},
                "monthly_acquisition_spend": {"type": "number", "default": 400},
                "monthly_churn_rate": {"type": "number", "default": 0.08},
                "starting_cash": {"type": "number", "default": 6000},
                "target_survival_pct": {"type": "number", "default": 85}
            },
            "required": ["unit_price"]
        }
    },
    {
        "name": "scan_repo_api_costs",
        "description": "Statically scan a local Python/JS/TS repository for AI/media SDKs, expensive models, LLM calls inside loops, and missing max_tokens caps, and compute real gross margin impact.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "subscription_price_usd": {"type": "number", "default": 29},
                "assumed_daily_calls_per_user": {"type": "integer", "default": 20}
            },
            "required": ["repo_path"]
        }
    },
]


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an MCP tool call and return compact structured JSON payload."""
    if name == "auto_fix_unit_economics":
        fin = FinancialInputs(
            business_type=BusinessType(arguments.get("business_type", "saas")),
            unit_price=Decimal(str(arguments["unit_price"])),
            variable_cost_per_unit=Decimal(str(arguments.get("variable_cost_per_unit", 5))),
            fixed_monthly_costs=Decimal(str(arguments.get("fixed_monthly_costs", 1000))),
            monthly_new_customers=int(arguments.get("monthly_new_customers", 12)),
            monthly_acquisition_spend=Decimal(str(arguments.get("monthly_acquisition_spend", 400))),
            monthly_churn_rate=Decimal(str(arguments.get("monthly_churn_rate", 0.08))),
            starting_cash=Decimal(str(arguments.get("starting_cash", 6000))),
        )
        rep = generate_autofix_prescriptions(fin, target_survival_pct=Decimal(str(arguments.get("target_survival_pct", 85))))
        return json.loads(rep.json() if hasattr(rep, "json") else rep.model_dump_json())

    if name == "scan_repo_api_costs":
        rep = scan_repo_api_costs(
            arguments["repo_path"],
            subscription_price_usd=Decimal(str(arguments.get("subscription_price_usd", 29))),
            assumed_daily_calls_per_user=int(arguments.get("assumed_daily_calls_per_user", 20)),
        )
        return json.loads(rep.json() if hasattr(rep, "json") else rep.model_dump_json())

    if name == "scan_geo_arbitrage":
        cfg = IdeaStressConfig.from_env()
        cache = SQLiteSignalCache(cfg.cache_db_path)
        live = (
            DataForSEOCPCProvider(cfg.dataforseo_login, cfg.dataforseo_password)
            if cfg.cpc_provider == "dataforseo" and cfg.dataforseo_login and cfg.dataforseo_password
            else None
        )
        rep = scan_geo_arbitrage(
            arguments["keywords"],
            us_max_viable_cac_usd=Decimal(str(arguments["us_max_viable_cac_usd"])),
            assumed_conversion_rate=Decimal(str(arguments.get("assumed_conversion_rate", 0.025))),
            live_provider=live,
            cache=cache,
        )
        return json.loads(rep.json() if hasattr(rep, "json") else rep.model_dump_json())

    if name == "check_scope_creep_finops":
        fin = FinancialInputs(
            business_type=BusinessType.SAAS,
            unit_price=Decimal(str(arguments["unit_price"])),
            variable_cost_per_unit=Decimal(str(arguments.get("current_variable_cost", 5))),
            fixed_monthly_costs=Decimal(str(arguments.get("fixed_monthly_costs", 600))),
            starting_cash=Decimal(str(arguments.get("starting_cash", 10000))),
        )
        res = check_scope_creep_finops(
            fin,
            feature_name=str(arguments["feature_name"]),
            extra_monthly_cogs_per_user=Decimal(str(arguments["extra_monthly_cogs_per_user"])),
        )
        return json.loads(res.json() if hasattr(res, "json") else res.model_dump_json())

    if name == "stress_test_ai_margin":
        inp = AITokenMarginInputs(
            subscription_price_usd=Decimal(str(arguments["subscription_price_usd"])),
            daily_requests_per_user=int(arguments.get("daily_requests_per_user", 20)),
            avg_input_tokens=int(arguments.get("avg_input_tokens", 2500)),
            avg_output_tokens=int(arguments.get("avg_output_tokens", 800)),
            model_preset=str(arguments.get("model_preset", "mid_balanced")),
        )
        r = stress_test_ai_token_margin(inp)
        return json.loads(r.json() if hasattr(r, "json") else r.model_dump_json())

    if name == "generate_kill_test_kit":
        req = AnalysisRequest(
            idea=arguments["idea"],
            customer_segment=arguments.get("customer_segment"),
            financials=FinancialInputs(unit_price=Decimal(str(arguments.get("unit_price", 49)))),
        )
        kit = generate_kill_test_kit(req)
        return {
            "idea": kit.idea,
            "target_price_label": kit.target_price_label,
            "ad_copies": kit.ad_copies,
            "mom_test_questions": kit.mom_test_questions,
            "landing_page_html_bytes": len(kit.landing_page_html),
        }

    if name == "falsify_paid_channel":
        cfg = IdeaStressConfig.from_env()
        prov = (
            DataForSEOCPCProvider(cfg.dataforseo_login, cfg.dataforseo_password)
            if cfg.cpc_provider == "dataforseo" and cfg.dataforseo_login and cfg.dataforseo_password
            else MockCPCProvider()
        )
        cache = SQLiteSignalCache(cfg.cache_db_path)
        res = evaluate_paid_channel_falsification(
            arguments["keywords"],
            max_viable_cac=Decimal(str(arguments["max_viable_cac"])),
            assumed_conversion_rate=Decimal(str(arguments.get("assumed_conversion_rate", 0.025))),
            provider=prov,
            cache=cache,
            location_code=int(arguments.get("location_code", 2840)),
        )
        return json.loads(res.json() if hasattr(res, "json") else res.model_dump_json())

    if name == "solve_unit_frontiers":
        inputs = FinancialInputs(
            business_type=BusinessType(arguments.get("business_type", "saas")),
            currency=str(arguments.get("currency", "USD")),
            unit_price=Decimal(str(arguments["unit_price"])),
            variable_cost_per_unit=Decimal(str(arguments.get("variable_cost_per_unit", 0))),
            fixed_monthly_costs=Decimal(str(arguments.get("fixed_monthly_costs", 0))),
            monthly_new_customers=int(arguments.get("monthly_new_customers", 10)),
            monthly_acquisition_spend=Decimal(str(arguments.get("monthly_acquisition_spend", 0))),
            monthly_churn_rate=Decimal(str(arguments.get("monthly_churn_rate", 0.05))),
            starting_cash=Decimal(str(arguments.get("starting_cash", 10000))),
            horizon_months=int(arguments.get("horizon_months", 12)),
        )
        fr = solve_reverse_frontier(inputs)
        return json.loads(fr.json() if hasattr(fr, "json") else fr.model_dump_json())

    if name == "scan_competitor_complaints":
        cfg = IdeaStressConfig.from_env()
        cache = SQLiteSignalCache(cfg.cache_db_path)
        signals = collect_complaint_signals(
            arguments["query"],
            mode=str(arguments.get("mode", "mock")),
            limit_per_platform=int(arguments.get("limit_per_platform", 3)),
            cache=cache,
        )
        return {
            "query": arguments["query"],
            "total_signals": len(signals),
            "pain_themes": aggregate_pain_themes(signals),
            "signals": [
                {
                    "platform": s.platform,
                    "title": s.title,
                    "rating": s.rating,
                    "pain_tags": s.pain_tags,
                    "excerpt": s.excerpt,
                    "url": s.url,
                }
                for s in signals
            ],
        }

    if name == "precode_gate_check":
        btype = BusinessType(arguments.get("business_type", "saas"))
        cur = str(arguments.get("currency", "USD"))
        cash = Decimal(str(arguments.get("starting_cash", 10000)))
        fin = FinancialInputs(
            business_type=btype,
            currency=cur,
            unit_price=Decimal(str(arguments["unit_price"])),
            variable_cost_per_unit=Decimal(str(arguments.get("variable_cost_per_unit", 5))),
            fixed_monthly_costs=Decimal(str(arguments.get("fixed_monthly_costs", 500))),
            monthly_new_customers=int(arguments.get("monthly_new_customers", 10)),
            monthly_acquisition_spend=Decimal(str(arguments.get("monthly_acquisition_spend", 300))),
            monthly_churn_rate=Decimal(str(arguments.get("monthly_churn_rate", 0.06))),
            starting_cash=cash,
        )
        req = AnalysisRequest(
            idea=arguments["idea"],
            customer_segment=arguments.get("customer_segment"),
            business_type=btype,
            budget=cash,
            currency=cur,
            mode=AnalysisMode.QUICK,
            financials=fin,
        )
        orch = AnalysisOrchestrator(config=IdeaStressConfig.from_env())
        res = orch.run(req, save_to_db=False)
        return {
            "analysis_id": res.analysis_id,
            "verdict": res.decision.verdict.value,
            "headline": res.decision.headline,
            "next_action": res.decision.next_action,
            "reverse_frontier": {
                "mathematical_verdict": res.financials.reverse_frontier.mathematical_verdict,
                "max_viable_cac": str(res.financials.reverse_frontier.max_viable_cac),
                "min_viable_unit_price": str(res.financials.reverse_frontier.min_viable_unit_price),
                "max_tolerable_monthly_churn_pct": str(res.financials.reverse_frontier.max_tolerable_monthly_churn_pct),
                "min_monthly_new_customers_to_survive": res.financials.reverse_frontier.min_monthly_new_customers_to_survive,
            },
            "monte_carlo": {
                "simulations": res.financials.monte_carlo.simulations,
                "survival_probability_pct": str(res.financials.monte_carlo.survival_probability_pct),
                "p10_ending_cash": str(res.financials.monte_carlo.p10_ending_cash),
                "p50_ending_cash": str(res.financials.monte_carlo.p50_ending_cash),
                "bankruptcy_risk_label": res.financials.monte_carlo.bankruptcy_risk_label,
            }
            if res.financials.monte_carlo
            else None,
            "channel_falsification": {
                "verdict": res.channel_falsification.verdict,
                "weighted_avg_cpc": str(res.channel_falsification.weighted_avg_cpc),
                "implied_paid_cac": str(res.channel_falsification.implied_paid_cac),
                "cache_hit": res.channel_falsification.cache_hit,
            }
            if res.channel_falsification
            else None,
            "pain_themes": res.provider_metadata.get("pain_themes", {}),
            "base_rate_warnings": [
                {"metric": b.metric, "status": b.status, "benchmark": b.benchmark_value, "source": b.source_url}
                for b in res.base_rate_checks
                if b.status != "ALIGNED"
            ],
            "top_red_team_counterarguments": res.red_team.strongest_counterarguments[:3],
            "top_kill_test": {
                "method": res.kill_tests[0].method,
                "hypothesis": res.kill_tests[0].hypothesis,
                "success_threshold": res.kill_tests[0].success_threshold,
                "failure_threshold": res.kill_tests[0].failure_threshold,
            }
            if res.kill_tests
            else None,
        }

    if name == "diff_assumption_ledger":
        b = load_ledger_yaml(arguments["before_yaml_path"])
        a = load_ledger_yaml(arguments["after_yaml_path"])
        diff = diff_ledgers(b, a)
        return json.loads(diff.json() if hasattr(diff, "json") else diff.model_dump_json())

    if name == "get_industry_base_rates":
        btype = BusinessType(arguments["business_type"])
        recs = get_base_rates_for(btype)
        return {
            "business_type": btype.value,
            "benchmarks": [
                {
                    "metric": r.metric,
                    "value": r.value_label,
                    "source_title": r.source_title,
                    "source_url": r.source_url,
                }
                for r in recs
            ],
        }

    raise ValueError(f"Unknown MCP tool: {name}")


def handle_jsonrpc_request(req: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single JSON-RPC 2.0 MCP message."""
    req_id = req.get("id")
    method = req.get("method", "")
    params = req.get("params") or {}

    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "ideastress-mcp", "version": "0.8.1"},
                },
            }
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": MCP_TOOLS}}
        if method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments") or {}
            payload = handle_tool_call(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
                    "isError": False,
                },
            }
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": str(exc)},
        }


def run_stdio_server() -> None:
    """Run the JSON-RPC 2.0 stdio loop for Claude Code / Cursor / Codex."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        if "id" not in req:
            continue
        resp = handle_jsonrpc_request(req)
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
