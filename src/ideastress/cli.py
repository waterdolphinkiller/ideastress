"""IdeaStress CLI v0.2.0 — analyze, solve, diff, signals, benchmarks, benchmark-run, mcp, doctor."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ideastress import __version__
from ideastress.benchmarks.base_rates import get_base_rates_for
from ideastress.benchmarks.suite import run_benchmark_suite
from ideastress.config import IdeaStressConfig
from ideastress.domain.models import AnalysisMode, AnalysisRequest, BusinessType, FinancialInputs
from ideastress.finance.montecarlo import run_monte_carlo
from ideastress.experiments.kit import generate_kill_test_kit, save_kill_test_kit
from ideastress.finance.ai_unit import AITokenMarginInputs, stress_test_ai_token_margin
from ideastress.finance.solver import solve_reverse_frontier
from ideastress.finance.autofix import generate_autofix_prescriptions
from ideastress.finance.repo_scanner import scan_repo_api_costs
from ideastress.finance.scope_gate import check_scope_creep_finops
from ideastress.providers.geo_arbitrage import scan_geo_arbitrage
from ideastress.providers.price_radar import check_price_drift
from ideastress.reports.proof_card import render_proof_card_svg
from ideastress.ledger.diff import diff_ledgers, load_ledger_yaml
from ideastress.mcp.server import run_stdio_server
from ideastress.providers.cpc import DataForSEOCPCProvider, MockCPCProvider, evaluate_paid_channel_falsification
from ideastress.providers.signals import aggregate_pain_themes, collect_complaint_signals
from ideastress.storage.cache import SQLiteSignalCache
from ideastress.reports.renderer import render_html, render_json, render_markdown
from ideastress.sdk import IdeaStress

console = Console()


@click.group()
@click.version_option(__version__, prog_name="ideastress")
def main() -> None:
    """IdeaStress: Evidence-first business feasibility & reverse unit-economics engine."""


@main.command()
def doctor() -> None:
    """Check environment configuration, provider readiness, and budget caps (secrets redacted)."""
    cfg = IdeaStressConfig.from_env()
    console.print_json(json.dumps(cfg.safe_summary(), indent=2))


@main.command()
@click.option("--idea", type=str, default=None, help="Business idea description.")
@click.option("--input", "input_path", type=click.Path(exists=True), default=None, help="Path to venture.yaml ledger.")
@click.option("--market", type=str, default="United States", help="Target market.")
@click.option("--type", "btype", type=click.Choice([b.value for b in BusinessType]), default="saas")
@click.option("--price", type=str, default="49", help="Unit price.")
@click.option("--budget", type=str, default="10000", help="Starting cash budget.")
@click.option("--currency", type=str, default="USD")
@click.option("--mode", type=click.Choice(["quick", "deep"]), default="quick")
@click.option("--format", "out_format", type=click.Choice(["markdown", "html", "json"]), default="markdown")
@click.option("--out", "out_path", type=click.Path(), default=None, help="Save report to file.")
def analyze(
    idea: str | None,
    input_path: str | None,
    market: str,
    btype: str,
    price: str,
    budget: str,
    currency: str,
    mode: str,
    out_format: str,
    out_path: str | None,
) -> None:
    """Run a full stress-test analysis from CLI flags or a venture.yaml ledger."""
    if input_path:
        req = load_ledger_yaml(input_path)
    elif idea:
        req = AnalysisRequest(
            idea=idea,
            target_market=[market],
            business_type=BusinessType(btype),
            budget=Decimal(budget),
            currency=currency,
            mode=AnalysisMode(mode),
            financials=FinancialInputs(
                business_type=BusinessType(btype),
                currency=currency,
                unit_price=Decimal(price),
                variable_cost_per_unit=Decimal("5"),
                fixed_monthly_costs=Decimal("800"),
                monthly_new_customers=12,
                monthly_acquisition_spend=Decimal("400"),
                starting_cash=Decimal(budget),
            ),
        )
    else:
        raise click.UsageError("Provide either --idea or --input <venture.yaml>.")

    client = IdeaStress.from_env()
    res = client.analyze(req)

    if out_format == "html":
        rendered = render_html(res)
    elif out_format == "json":
        rendered = render_json(res)
    else:
        rendered = render_markdown(res)

    if out_path:
        Path(out_path).write_text(rendered, encoding="utf-8")
        console.print(f"[green]Saved {out_format.upper()} report to {out_path}[/green] (Verdict: [bold]{res.decision.verdict.value}[/bold])")
    else:
        click.echo(rendered)


@main.command()
@click.option("--type", "btype", type=click.Choice([b.value for b in BusinessType]), default="saas")
@click.option("--price", type=str, required=True)
@click.option("--var-cost", type=str, default="5")
@click.option("--fixed-cost", type=str, default="800")
@click.option("--new-customers", type=int, default=12)
@click.option("--acq-spend", type=str, default="400")
@click.option("--churn", type=str, default="0.06")
@click.option("--cash", type=str, default="10000")
@click.option("--currency", type=str, default="USD")
@click.option("--payment-processor", type=click.Choice(["none", "stripe_us", "stripe_saas", "mor_paddle"]), default="none")
@click.option("--tax-rate", type=str, default="0.00", help="Effective tax rate decimal, e.g. 0.21")
def solve(
    btype: str,
    price: str,
    var_cost: str,
    fixed_cost: str,
    new_customers: int,
    acq_spend: str,
    churn: str,
    cash: str,
    currency: str,
    payment_processor: str,
    tax_rate: str,
) -> None:
    """Run the deterministic Reverse Unit-Economics Solver (zero LLM cost)."""
    fin = FinancialInputs(
        business_type=BusinessType(btype),
        currency=currency,
        unit_price=Decimal(price),
        variable_cost_per_unit=Decimal(var_cost),
        fixed_monthly_costs=Decimal(fixed_cost),
        monthly_new_customers=new_customers,
        monthly_acquisition_spend=Decimal(acq_spend),
        monthly_churn_rate=Decimal(churn),
        starting_cash=Decimal(cash),
        payment_processor=payment_processor,
        effective_tax_rate=Decimal(tax_rate),
    )
    fr = solve_reverse_frontier(fin)
    mc = run_monte_carlo(fin, simulations=1000, seed=42)
    out = {"reverse_frontier": json.loads(fr.json()), "monte_carlo": json.loads(mc.json())}
    console.print_json(json.dumps(out, indent=2))


@main.command()
@click.argument("before_yaml", type=click.Path(exists=True))
@click.argument("after_yaml", type=click.Path(exists=True))
def diff(before_yaml: str, after_yaml: str) -> None:
    """Diff two venture.yaml assumption ledgers after real-world experiments."""
    res = diff_ledgers(load_ledger_yaml(before_yaml), load_ledger_yaml(after_yaml))
    console.print_json(res.json() if hasattr(res, "json") else res.model_dump_json())


@main.command()
@click.argument("query")
@click.option("--mode", type=click.Choice(["mock", "live"]), default="mock")
def signals(query: str, mode: str) -> None:
    """Scan Reddit, App Store, and G2 for competitor complaints & pain themes."""
    items = collect_complaint_signals(query, mode=mode)
    payload = {
        "query": query,
        "pain_themes": aggregate_pain_themes(items),
        "signals": [
            {"platform": s.platform, "title": s.title, "rating": s.rating, "pain_tags": s.pain_tags, "url": s.url}
            for s in items
        ],
    }
    console.print_json(json.dumps(payload, indent=2))


@main.command()
@click.option("--type", "btype", type=click.Choice([b.value for b in BusinessType]), default="saas")
def benchmarks(btype: str) -> None:
    """Show source-cited 2025-2026 industry base rates."""
    recs = get_base_rates_for(BusinessType(btype))
    table = Table(title=f"IdeaStress 2025-2026 Base Rates ({btype.upper()})")
    table.add_column("Metric", style="cyan")
    table.add_column("Benchmark", style="bold")
    table.add_column("Source URL", style="dim")
    for r in recs:
        table.add_row(r.metric, r.value_label, r.source_url)
    console.print(table)


@main.command("benchmark-run")
def benchmark_run() -> None:
    """Execute the full 10-case industry Benchmark Suite and print quality metrics."""
    summary = run_benchmark_suite()
    console.print_json(json.dumps(summary, indent=2))


@main.command("cpc-check")
@click.option("--keywords", type=str, required=True, help="Comma-separated search keywords.")
@click.option("--max-cac", type=str, required=True, help="Solved max viable CAC ceiling.")
@click.option("--cvr", type=str, default="0.025", help="Assumed landing-page conversion rate decimal (e.g. 0.025).")
@click.option("--location-code", type=int, default=2840, help="Google Ads location code (2840 = US).")
def cpc_check(keywords: str, max_cac: str, cvr: str, location_code: int) -> None:
    """Cross-check real Google Ads CPC against your max viable CAC ceiling (with 30-day SQLite cache)."""
    cfg = IdeaStressConfig.from_env()
    prov = (
        DataForSEOCPCProvider(cfg.dataforseo_login, cfg.dataforseo_password)
        if cfg.cpc_provider == "dataforseo" and cfg.dataforseo_login and cfg.dataforseo_password
        else MockCPCProvider()
    )
    cache = SQLiteSignalCache(cfg.cache_db_path)
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    res = evaluate_paid_channel_falsification(
        kw_list,
        max_viable_cac=Decimal(max_cac),
        assumed_conversion_rate=Decimal(cvr),
        provider=prov,
        cache=cache,
        location_code=location_code,
    )
    console.print_json(res.json() if hasattr(res, "json") else res.model_dump_json())


@main.command("ai-margin")
@click.option("--price", type=str, required=True, help="Monthly subscription price in USD.")
@click.option("--daily-requests", type=int, default=20)
@click.option("--in-tokens", type=int, default=2500)
@click.option("--out-tokens", type=int, default=800)
@click.option("--model", type=click.Choice(["budget_fast", "mid_balanced", "frontier_reasoning"]), default="mid_balanced")
def ai_margin(price: str, daily_requests: int, in_tokens: int, out_tokens: int, model: str) -> None:
    """Stress-test AI wrapper token COGS, gross margin, and Whale Bankruptcy daily request limit."""
    res = stress_test_ai_token_margin(
        AITokenMarginInputs(
            subscription_price_usd=Decimal(price),
            daily_requests_per_user=daily_requests,
            avg_input_tokens=in_tokens,
            avg_output_tokens=out_tokens,
            model_preset=model,
        )
    )
    console.print_json(res.json() if hasattr(res, "json") else res.model_dump_json())


@main.command("kill-kit")
@click.option("--idea", type=str, required=True)
@click.option("--segment", type=str, default="Solo founders and SMB operators")
@click.option("--price", type=str, default="49")
@click.option("--out-dir", type=click.Path(), default="./kill_test_kit")
def kill_kit(idea: str, segment: str, price: str, out_dir: str) -> None:
    """Generate a ready-to-launch Smoke-Test Landing Page + 3 Ad Copies + 15 Mom-Test Questions."""
    req = AnalysisRequest(
        idea=idea,
        customer_segment=segment,
        financials=FinancialInputs(unit_price=Decimal(price)),
    )
    kit = generate_kill_test_kit(req)
    saved = save_kill_test_kit(kit, out_dir)
    console.print(f"[green]Generated Kill-Test Action Kit in {saved}[/green] (smoke_test_landing.html + kill_test_playbook.md)")


@main.command("radar")
@click.option("--url", type=str, required=True, help="Competitor pricing URL.")
@click.option("--text", type=str, required=True, help="Captured pricing page text excerpt.")
def radar(url: str, text: str) -> None:
    """Check competitor pricing page snapshot for price hikes or free-tier removal."""
    cfg = IdeaStressConfig.from_env()
    cache = SQLiteSignalCache(cfg.cache_db_path)
    report = check_price_drift(url, text, cache)
    console.print_json(report.json() if hasattr(report, "json") else report.model_dump_json())


@main.command("geo-scan")
@click.option("--keywords", type=str, required=True, help="Comma-separated search keywords.")
@click.option("--us-max-cac", type=str, required=True, help="Solved US max viable CAC in USD.")
@click.option("--cvr", type=str, default="0.025")
def geo_scan(keywords: str, us_max_cac: str, cvr: str) -> None:
    """Compare paid search CPC & survival across US, UK, DE, SG, and MY."""
    cfg = IdeaStressConfig.from_env()
    cache = SQLiteSignalCache(cfg.cache_db_path)
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    rep = scan_geo_arbitrage(kw_list, us_max_viable_cac_usd=Decimal(us_max_cac), assumed_conversion_rate=Decimal(cvr), cache=cache)
    console.print_json(rep.json() if hasattr(rep, "json") else rep.model_dump_json())


@main.command("scope-gate")
@click.option("--price", type=str, required=True, help="Current monthly subscription price.")
@click.option("--var-cost", type=str, default="5")
@click.option("--fixed-cost", type=str, default="600")
@click.option("--cash", type=str, default="10000")
@click.option("--feature", type=str, required=True, help="Proposed new feature name.")
@click.option("--extra-cogs", type=str, required=True, help="Estimated extra monthly COGS per user.")
def scope_gate(price: str, var_cost: str, fixed_cost: str, cash: str, feature: str, extra_cogs: str) -> None:
    """Run Coding-Time FinOps Gate before implementing a costly new feature."""
    fin = FinancialInputs(
        business_type=BusinessType.SAAS,
        unit_price=Decimal(price),
        variable_cost_per_unit=Decimal(var_cost),
        fixed_monthly_costs=Decimal(fixed_cost),
        starting_cash=Decimal(cash),
    )
    res = check_scope_creep_finops(fin, feature_name=feature, extra_monthly_cogs_per_user=Decimal(extra_cogs))
    console.print_json(res.json() if hasattr(res, "json") else res.model_dump_json())


@main.command("proof-card")
@click.option("--input", "input_path", type=click.Path(exists=True), required=True, help="Path to venture.yaml.")
@click.option("--out", "out_path", type=click.Path(), default="proof_card.svg")
def proof_card(input_path: str, out_path: str) -> None:
    """Generate a shareable 1200x630 Falsification Proof Card SVG for X / Reddit / Indie Hackers."""
    client = IdeaStress.from_env()
    res = client.analyze(load_ledger_yaml(input_path), save=False)
    svg = render_proof_card_svg(res)
    Path(out_path).write_text(svg, encoding="utf-8")
    console.print(f"[green]Saved 1200x630 Proof Card SVG to {out_path}[/green]")


@main.command("autofix")
@click.option("--type", "btype", type=click.Choice([b.value for b in BusinessType]), default="saas")
@click.option("--price", type=str, required=True)
@click.option("--var-cost", type=str, default="5")
@click.option("--fixed-cost", type=str, default="1000")
@click.option("--new-customers", type=int, default=12)
@click.option("--acq-spend", type=str, default="400")
@click.option("--churn", type=str, default="0.08")
@click.option("--cash", type=str, default="6000")
@click.option("--target-survival", type=str, default="85")
def autofix(btype: str, price: str, var_cost: str, fixed_cost: str, new_customers: int, acq_spend: str, churn: str, cash: str, target_survival: str) -> None:
    """Compute exact Minimum Viable Fix prescriptions (price, churn, spend, annual prepay) to hit target survival."""
    fin = FinancialInputs(
        business_type=BusinessType(btype),
        unit_price=Decimal(price),
        variable_cost_per_unit=Decimal(var_cost),
        fixed_monthly_costs=Decimal(fixed_cost),
        monthly_new_customers=new_customers,
        monthly_acquisition_spend=Decimal(acq_spend),
        monthly_churn_rate=Decimal(churn),
        starting_cash=Decimal(cash),
    )
    rep = generate_autofix_prescriptions(fin, target_survival_pct=Decimal(target_survival))
    console.print_json(rep.json() if hasattr(rep, "json") else rep.model_dump_json())


@main.command("scan-repo")
@click.argument("repo_path", type=click.Path(exists=True))
@click.option("--price", type=str, default="29", help="Monthly subscription price in USD.")
@click.option("--daily-calls", type=int, default=20, help="Assumed daily API calls per active user.")
def scan_repo(repo_path: str, price: str, daily_calls: int) -> None:
    """Statically scan a codebase for AI API costs, unbounded loops, and missing token caps."""
    rep = scan_repo_api_costs(repo_path, subscription_price_usd=Decimal(price), assumed_daily_calls_per_user=daily_calls)
    console.print_json(rep.json() if hasattr(rep, "json") else rep.model_dump_json())


@main.command()
def mcp() -> None:
    """Start the zero-dependency JSON-RPC 2.0 stdio MCP server for Claude Code / Cursor / Codex."""
    run_stdio_server()


if __name__ == "__main__":
    main()
