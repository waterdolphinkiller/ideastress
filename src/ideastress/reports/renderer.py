"""Markdown, JSON, and Interactive Editorial HTML report renderers for IdeaStress."""

from __future__ import annotations

import json
from html import escape

from ideastress.domain.models import AnalysisResult


def render_json(result: AnalysisResult) -> str:
    if hasattr(result, "json"):
        return result.json(indent=2)
    return result.model_dump_json(indent=2)


def render_markdown(result: AnalysisResult) -> str:
    d = result.decision
    f = result.financials
    base = f.scenarios["base"]
    cons = f.scenarios["conservative"]
    opt = f.scenarios["optimistic"]
    fr = f.reverse_frontier
    cur = f.currency

    lines = [
        f"# IdeaStress Feasibility & Falsification Report",
        "",
        f"- **Analysis ID:** `{result.analysis_id}`",
        f"- **Generated At:** `{result.created_at}`",
        f"- **Verdict:** **`{d.verdict.value}`** — {d.headline}",
        f"- **Run Status:** `{result.status.value}`",
        f"- **Market:** {', '.join(result.request.target_market)} | **Model:** `{result.request.business_type.value}` | **Mode:** `{result.request.mode.value}`",
        f"- **Providers:** LLM=`{result.provider_metadata.get('llm_provider')}`, Search=`{result.provider_metadata.get('search_provider')}`, Fetch=`{result.provider_metadata.get('fetch_provider')}`",
        "",
        "## 1. Executive Decision & Next Action",
        "",
        f"**Next Action:** {d.next_action}",
        "",
        "### Key Reasons",
        *[f"- {r}" for r in d.reasons],
        "",
    ]

    if d.blocking_conditions:
        lines += ["### Blocking Conditions", *[f"- {b}" for b in d.blocking_conditions], ""]

    lines += [
        "## 2. Reverse Unit-Economics Survival Frontier (Mathematical Red Lines)",
        "",
        f"- **Mathematical Verdict:** `{fr.mathematical_verdict}`",
        f"- **Max Viable CAC ({fr.horizon_months}m survival):** `{cur} {fr.max_viable_cac}`" if fr.max_viable_cac is not None else "- **Max Viable CAC:** `N/A`",
        f"- **3:1 LTV:CAC Ceiling:** `{cur} {fr.max_cac_for_3x_ltv}`" if fr.max_cac_for_3x_ltv is not None else "- **3:1 LTV:CAC Ceiling:** `N/A`",
        f"- **Min Viable Unit Price:** `{cur} {fr.min_viable_unit_price}`" if fr.min_viable_unit_price is not None else "- **Min Viable Unit Price:** `N/A`",
        f"- **Max Tolerable Monthly Churn:** `{fr.max_tolerable_monthly_churn_pct}%`" if fr.max_tolerable_monthly_churn_pct is not None else "- **Max Tolerable Monthly Churn:** `N/A`",
        f"- **Min New Customers / Month to Survive:** `{fr.min_monthly_new_customers_to_survive}`",
        "",
        "## 2b. 1,000-Run Monte Carlo Survival & Paid CPC Channel Check",
        "",
        *(
            [
                f"- **Monte Carlo Survival Probability ({f.monte_carlo.simulations} runs):** `{f.monte_carlo.survival_probability_pct}%` (`{f.monte_carlo.bankruptcy_risk_label}`)",
                f"- **Cash Percentiles (M{f.monte_carlo.horizon_months}):** P10=`{cur} {f.monte_carlo.p10_ending_cash:,.2f}` | P50=`{cur} {f.monte_carlo.p50_ending_cash:,.2f}` | P90=`{cur} {f.monte_carlo.p90_ending_cash:,.2f}` (P10 Trough: `{cur} {f.monte_carlo.p10_min_cash:,.2f}`)",
            ]
            if f.monte_carlo
            else []
        ),
        *(
            [
                f"- **Paid Search CPC Falsification:** `{result.channel_falsification.verdict}` — Weighted CPC `{cur} {result.channel_falsification.weighted_avg_cpc}` -> Implied CAC `{cur} {result.channel_falsification.implied_paid_cac}` (Cache Hit: `{result.channel_falsification.cache_hit}`)",
            ]
            if result.channel_falsification
            else []
        ),
        "",
        "## 3. Financial Scenarios (Deterministic Decimal Engine)",
        "",
        "| Metric | Conservative | Base | Optimistic |",
        "|---|---:|---:|---:|",
        f"| Unit Contribution Margin | {cur} {cons.unit_contribution_margin} | {cur} {base.unit_contribution_margin} | {cur} {opt.unit_contribution_margin} |",
        f"| Gross Margin % | {cons.gross_margin_pct}% | {base.gross_margin_pct}% | {opt.gross_margin_pct}% |",
        f"| Break-Even Units/Mo | {cons.break_even_units or cons.break_even_status} | {base.break_even_units or base.break_even_status} | {opt.break_even_units or opt.break_even_status} |",
        f"| Ending Cash (M{f.scenarios['base'].horizon_months}) | {cur} {cons.ending_cash_balance:,.2f} | {cur} {base.ending_cash_balance:,.2f} | {cur} {opt.ending_cash_balance:,.2f} |",
        f"| Min Cash Balance | {cur} {cons.min_cash_balance:,.2f} | {cur} {base.min_cash_balance:,.2f} | {cur} {opt.min_cash_balance:,.2f} |",
        f"| Runway Status | {cons.runway_status} | {base.runway_status} | {opt.runway_status} |",
        "",
        "## 4. 2025-2026 Industry Base Rate Calibration",
        "",
        "| Metric | Your Model | Industry Benchmark | Status | Source |",
        "|---|---|---|---|---|",
    ]
    for br in result.base_rate_checks:
        lines.append(
            f"| {br.metric} | {br.user_value} | {br.benchmark_value} | `{br.status}` | [{br.source_title}]({br.source_url}) |"
        )

    lines += [
        "",
        "## 5. Competitor & Substitute Map",
        "",
        "| Name | Category | Pricing | Overlap |",
        "|---|---|---|---|",
    ]
    for c in result.competitors:
        name_md = f"[{c.name}]({c.url})" if c.url else c.name
        lines.append(f"| {name_md} | `{c.category.value}` | {c.pricing_summary} | {c.overlap_summary} |")

    lines += [
        "",
        "## 6. Independent Red Team: Strongest Counterarguments",
        "",
        *[f"- {arg}" for arg in result.red_team.strongest_counterarguments],
        "",
        "### Decision-Changing Conditions",
        *[f"- {cond}" for cond in result.red_team.decision_changing_conditions],
        "",
        "## 7. Recommended Kill Tests (Lowest-Cost Falsification Experiments)",
        "",
    ]
    for kt in result.kill_tests:
        lines += [
            f"### {kt.method} (`{kt.experiment_id}`)",
            f"- **Hypothesis:** {kt.hypothesis}",
            f"- **Budget / Duration:** {kt.currency} {kt.budget_estimate} / {kt.duration_days} days",
            f"- **Success Threshold:** {kt.success_threshold}",
            f"- **Failure Threshold:** {kt.failure_threshold}",
            f"- **Decision Rule:** {kt.decision_rule}",
            "",
        ]

    lines += [
        "## 8. Evidence Audit & Sources Appendix",
        "",
        f"- **Audit Passed:** `{result.audit.passed}` | **Total Claims:** {result.audit.total_claims} | **Verified:** {result.audit.verified_claims} | **Downgraded:** {result.audit.downgraded_claims} | **Contradictions:** {result.audit.contradictions_found}",
        "",
    ]
    for ev in result.evidences:
        link = f"[{ev.title}]({ev.url})" if ev.url else ev.title
        lines.append(f"- `{ev.evidence_id}` ({ev.source_reliability.value}, retrieved {ev.retrieved_at}): {link}")

    lines += [
        "",
        "## 9. Limitations & Disclaimer",
        "",
        *[f"- {lim}" for lim in f.limitations],
        "- IdeaStress provides structured preliminary feasibility research, not investment, legal, or accounting advice.",
    ]
    return "\n".join(lines)


def render_html(result: AnalysisResult) -> str:
    """Render an obsidian-editorial standalone HTML report with a live interactive Reverse Frontier Calculator."""
    d = result.decision
    f = result.financials
    base = f.scenarios["base"]
    cons = f.scenarios["conservative"]
    opt = f.scenarios["optimistic"]
    fr = f.reverse_frontier
    cur = escape(f.currency)

    verdict_colors = {
        "GO": ("#10b981", "rgba(16,185,129,0.14)"),
        "CONDITIONAL_GO": ("#f59e0b", "rgba(245,158,11,0.14)"),
        "PIVOT": ("#fb923c", "rgba(251,146,60,0.14)"),
        "NO_GO": ("#ef4444", "rgba(239,68,68,0.14)"),
        "INSUFFICIENT_DATA": ("#94a3b8", "rgba(148,163,184,0.14)"),
    }
    vc, vbg = verdict_colors.get(d.verdict.value, ("#e2e8f0", "rgba(226,232,240,0.12)"))

    fin_in = result.request.financials
    init_price = float(fin_in.unit_price) if fin_in else 49.0
    init_var = float(fin_in.variable_cost_per_unit) if fin_in else 5.0
    init_fixed = float(fin_in.fixed_monthly_costs) if fin_in else 800.0
    init_new = int(fin_in.monthly_new_customers) if fin_in else 12
    init_spend = float(fin_in.monthly_acquisition_spend) if fin_in else 400.0
    init_churn = float(fin_in.monthly_churn_rate * 100) if fin_in else 6.0
    init_cash = float(fin_in.starting_cash) if fin_in else float(result.request.budget)
    is_saas = "true" if f.business_type.value == "saas" else "false"

    br_rows = ""
    for br in result.base_rate_checks:
        badge_col = "#ef4444" if br.status == "SEVERE_OUTLIER" else ("#f59e0b" if br.status == "OPTIMISTIC_WARNING" else "#10b981")
        br_rows += f"""
        <tr>
          <td><strong>{escape(br.metric)}</strong></td>
          <td class="mono">{escape(br.user_value)}</td>
          <td>{escape(br.benchmark_value)}</td>
          <td><span class="pill" style="color:{badge_col};border-color:{badge_col}44;background:{badge_col}18">{escape(br.status)}</span></td>
          <td><a href="{escape(br.source_url)}" target="_blank" rel="noopener">{escape(br.source_title)}</a></td>
        </tr>"""

    comp_rows = ""
    for c in result.competitors:
        name_html = f'<a href="{escape(c.url)}" target="_blank" rel="noopener">{escape(c.name)}</a>' if c.url else escape(c.name)
        comp_rows += f"""
        <tr>
          <td><strong>{name_html}</strong></td>
          <td><span class="pill">{escape(c.category.value)}</span></td>
          <td>{escape(c.pricing_summary)}</td>
          <td>{escape(c.overlap_summary)}</td>
        </tr>"""

    rt_items = "".join(f"<li>{escape(x)}</li>" for x in result.red_team.strongest_counterarguments)
    kt_cards = ""
    for kt in result.kill_tests:
        kt_cards += f"""
        <div class="kt-card">
          <div class="kt-head">
            <span class="mono tag">{escape(kt.method)}</span>
            <span class="mono muted">{cur} {kt.budget_estimate} · {kt.duration_days} days</span>
          </div>
          <p class="kt-hyp">{escape(kt.hypothesis)}</p>
          <div class="kt-grid">
            <div><span class="lbl ok">PASS THRESHOLD</span><p>{escape(kt.success_threshold)}</p></div>
            <div><span class="lbl bad">KILL THRESHOLD</span><p>{escape(kt.failure_threshold)}</p></div>
          </div>
        </div>"""

    sens_rows = ""
    for sp in f.sensitivity:
        sc = "#10b981" if sp.survives_horizon else "#ef4444"
        sens_rows += f"""
        <tr>
          <td>{escape(sp.variable)}</td>
          <td class="mono">{escape(sp.change_label)}</td>
          <td class="mono">{cur} {sp.ending_cash:,.2f}</td>
          <td class="mono">{cur} {sp.delta_ending_cash:+,.2f}</td>
          <td><span class="pill" style="color:{sc};border-color:{sc}44">{'SURVIVES' if sp.survives_horizon else 'RUNS OUT OF CASH'}</span></td>
        </tr>"""

    ev_items = "".join(
        f'<li><span class="mono muted">[{escape(e.evidence_id)}]</span> ({escape(e.source_reliability.value)}, {escape(e.retrieved_at)}) — '
        + (f'<a href="{escape(e.url)}" target="_blank" rel="noopener">{escape(e.title)}</a>' if e.url else escape(e.title))
        + "</li>"
        for e in result.evidences
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>IdeaStress Report — {escape(result.request.idea[:60])}</title>
<style>
  :root {{
    --bg: #0b0d12;
    --surface: #121620;
    --surface-2: #181d2a;
    --border: #252c3d;
    --text: #e6ebf5;
    --muted: #8b95ad;
    --accent: #38bdf8;
    --gold: #f59e0b;
    --ok: #10b981;
    --bad: #ef4444;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; padding: 0;
    background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
    line-height: 1.55;
    scrollbar-width: thin;
    scrollbar-color: #2b3449 var(--bg);
  }}
  ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: #2b3449; border-radius: 4px; }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .wrap {{ max-width: 1120px; margin: 0 auto; padding: 36px 24px 72px; }}
  .topbar {{
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid var(--border); padding-bottom: 18px; margin-bottom: 28px;
    flex-wrap: wrap; gap: 12px;
  }}
  .brand {{ font-weight: 800; letter-spacing: 0.04em; font-size: 1.1rem; }}
  .brand span {{ color: var(--accent); }}
  .meta {{ color: var(--muted); font-size: 0.85rem; }}
  .hero {{
    background: linear-gradient(145deg, var(--surface), #151a27);
    border: 1px solid var(--border); border-radius: 16px; padding: 28px; margin-bottom: 24px;
  }}
  .verdict-badge {{
    display: inline-block; padding: 6px 14px; border-radius: 999px;
    font-weight: 800; letter-spacing: 0.06em; font-size: 0.85rem;
    color: {vc}; background: {vbg}; border: 1px solid {vc}55; margin-bottom: 12px;
  }}
  h1 {{ margin: 0 0 8px; font-size: 1.75rem; letter-spacing: -0.02em; }}
  h2 {{ margin: 32px 0 14px; font-size: 1.15rem; letter-spacing: 0.01em; color: #f8fafc; }}
  .kpi-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 14px; margin-top: 20px;
  }}
  .kpi {{
    background: var(--surface-2); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px;
  }}
  .kpi .k-lbl {{ font-size: 0.76rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }}
  .kpi .k-val {{ font-size: 1.45rem; font-weight: 700; margin-top: 4px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 22px; margin-bottom: 20px;
  }}
  .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .muted {{ color: var(--muted); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th, td {{ text-align: left; padding: 11px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }}
  th {{ color: var(--muted); font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  .pill {{
    display: inline-block; padding: 2px 9px; border-radius: 999px;
    font-size: 0.75rem; font-weight: 600; border: 1px solid var(--border);
  }}
  .calc-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 18px; }}
  .field label {{ display: block; font-size: 0.78rem; color: var(--muted); margin-bottom: 4px; }}
  .field input {{
    width: 100%; background: var(--bg); color: var(--text);
    border: 1px solid var(--border); border-radius: 8px; padding: 9px 10px;
    font-family: ui-monospace, monospace; font-size: 0.95rem;
  }}
  .kt-card {{
    background: var(--surface-2); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px; margin-bottom: 12px;
  }}
  .kt-head {{ display: flex; justify-content: space-between; margin-bottom: 8px; gap: 10px; flex-wrap: wrap; }}
  .kt-hyp {{ margin: 0 0 12px; font-weight: 600; }}
  .kt-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  .lbl {{ font-size: 0.7rem; font-weight: 700; letter-spacing: 0.06em; }}
  .lbl.ok {{ color: var(--ok); }}
  .lbl.bad {{ color: var(--bad); }}
  .kt-grid p {{ margin: 4px 0 0; font-size: 0.86rem; color: var(--muted); }}
  ul {{ padding-left: 20px; margin: 8px 0; }}
  li {{ margin-bottom: 6px; }}
  @media (max-width: 700px) {{ .kt-grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="wrap">
  <div class="topbar">
    <div class="brand">IDEA<span>STRESS</span> <span class="muted" style="font-weight:400;font-size:0.85rem;">// Business-as-Code Falsification Engine</span></div>
    <div class="meta mono">ID: {escape(result.analysis_id)} · {escape(result.created_at)} · {escape(result.request.business_type.value.upper())}</div>
  </div>

  <div class="hero">
    <div class="verdict-badge">{escape(d.verdict.value)}</div>
    <h1>{escape(result.request.idea)}</h1>
    <p class="muted" style="margin:6px 0 14px;">{escape(d.headline)} — <strong style="color:var(--text)">Next Action:</strong> {escape(d.next_action)}</p>
    <div class="kpi-grid">
      <div class="kpi">
        <div class="k-lbl">Max Viable CAC ({fr.horizon_months}m)</div>
        <div class="k-val" style="color:var(--accent)">{cur} {fr.max_viable_cac if fr.max_viable_cac is not None else 'N/A'}</div>
      </div>
      <div class="kpi">
        <div class="k-lbl">Min Viable Unit Price</div>
        <div class="k-val">{cur} {fr.min_viable_unit_price if fr.min_viable_unit_price is not None else 'N/A'}</div>
      </div>
      <div class="kpi">
        <div class="k-lbl">Base Ending Cash (M{base.horizon_months})</div>
        <div class="k-val" style="color:{'#10b981' if base.ending_cash_balance >= 0 else '#ef4444'}">{cur} {base.ending_cash_balance:,.2f}</div>
      </div>
      <div class="kpi">
        <div class="k-lbl">Survival Frontier</div>
        <div class="k-val" style="font-size:1.05rem;padding-top:6px;">{escape(fr.mathematical_verdict)}</div>
      </div>
    </div>
  </div>

  <h2>1,000-Run Monte Carlo Survival &amp; Real CPC Channel Falsification</h2>
  <div class="card">
    <div class="kpi-grid" style="margin-top:0;">
      <div class="kpi"><div class="k-lbl">Monte Carlo Survival (1,000 runs)</div><div class="k-val" style="color:var(--accent)">{f'{f.monte_carlo.survival_probability_pct}%' if f.monte_carlo else 'N/A'}</div></div>
      <div class="kpi"><div class="k-lbl">P10 Downside Cash</div><div class="k-val">{f'{cur} {f.monte_carlo.p10_ending_cash:,.0f}' if f.monte_carlo else 'N/A'}</div></div>
      <div class="kpi"><div class="k-lbl">Paid Search CPC Check</div><div class="k-val" style="font-size:1rem;padding-top:6px;">{escape(result.channel_falsification.verdict) if result.channel_falsification else 'N/A'}</div></div>
      <div class="kpi"><div class="k-lbl">Implied Paid CAC</div><div class="k-val">{f'{cur} {result.channel_falsification.implied_paid_cac:,.2f}' if result.channel_falsification else 'N/A'}</div></div>
    </div>
    <p class="muted" style="margin:12px 0 0;font-size:0.86rem;">{escape(result.channel_falsification.explanation) if result.channel_falsification else ''}</p>
  </div>

  <h2>Interactive Live Reverse Unit-Economics Stress Tester</h2>
  <div class="card">
    <p class="muted" style="margin-top:0;font-size:0.88rem;">Adjust your assumptions in real time to compute your exact 12-month cash balance, break-even units, and maximum survivable CAC ceiling.</p>
    <div class="calc-grid">
      <div class="field"><label>Unit Price ({cur})</label><input id="c_price" type="number" step="1" value="{init_price}" /></div>
      <div class="field"><label>Variable Cost / Unit ({cur})</label><input id="c_var" type="number" step="1" value="{init_var}" /></div>
      <div class="field"><label>Fixed Monthly Cost ({cur})</label><input id="c_fixed" type="number" step="50" value="{init_fixed}" /></div>
      <div class="field"><label>New Customers / Mo</label><input id="c_new" type="number" step="1" value="{init_new}" /></div>
      <div class="field"><label>Monthly Ad/Acq Spend ({cur})</label><input id="c_spend" type="number" step="50" value="{init_spend}" /></div>
      <div class="field"><label>Monthly Churn (%)</label><input id="c_churn" type="number" step="0.5" value="{init_churn}" /></div>
      <div class="field"><label>Starting Cash ({cur})</label><input id="c_cash" type="number" step="500" value="{init_cash}" /></div>
    </div>
    <div class="kpi-grid" id="live_out"></div>
  </div>

  <h2>2025–2026 Industry Base Rate Calibration (Cited)</h2>
  <div class="card" style="overflow-x:auto;">
    <table>
      <thead><tr><th>Metric</th><th>Your Model</th><th>2026 Industry Benchmark</th><th>Status</th><th>Source</th></tr></thead>
      <tbody>{br_rows}</tbody>
    </table>
  </div>

  <h2>Single-Variable Sensitivity Stress Tests</h2>
  <div class="card" style="overflow-x:auto;">
    <table>
      <thead><tr><th>Variable</th><th>Shock</th><th>Ending Cash</th><th>Delta vs Base</th><th>Survival</th></tr></thead>
      <tbody>{sens_rows}</tbody>
    </table>
  </div>

  <h2>Competitors & Substitutes</h2>
  <div class="card" style="overflow-x:auto;">
    <table>
      <thead><tr><th>Competitor</th><th>Tier</th><th>Pricing</th><th>Overlap</th></tr></thead>
      <tbody>{comp_rows}</tbody>
    </table>
  </div>

  <h2>Independent Red Team Counterarguments</h2>
  <div class="card">
    <ul>{rt_items}</ul>
  </div>

  <h2>Lowest-Cost Kill Tests (Run Before Writing Production Code)</h2>
  {kt_cards}

  <h2>Evidence Appendix & Audit</h2>
  <div class="card">
    <p class="mono muted" style="margin-top:0;font-size:0.84rem;">Audit Passed: {result.audit.passed} · Total Claims: {result.audit.total_claims} · Verified: {result.audit.verified_claims} · Downgraded: {result.audit.downgraded_claims} · Contradictions: {result.audit.contradictions_found}</p>
    <ul>{ev_items}</ul>
  </div>
</div>

<script>
const IS_SAAS = {is_saas};
const CUR = {json.dumps(f.currency)};
function sim(price, varCost, fixed, newC, spend, churnPct, cash) {{
  let active = 0, c = cash, minC = cash;
  const contrib = price - varCost;
  const churn = Math.min(0.95, Math.max(0, churnPct / 100));
  for (let m = 1; m <= 12; m++) {{
    if (IS_SAAS) {{
      active = Math.max(0, Math.round(active * (1 - churn))) + newC;
    }} else {{
      active = newC;
    }}
    const net = active * contrib - fixed - spend;
    c += net;
    if (c < minC) minC = c;
  }}
  return {{ ending: c, minC, contrib }};
}}
function solveMaxCac(price, varCost, fixed, newC, churnPct, cash) {{
  if (newC <= 0) return 0;
  if (sim(price, varCost, fixed, newC, 0, churnPct, cash).minC < 0) return 0;
  let lo = 0, hi = Math.max(5000, price * 24);
  for (let i = 0; i < 32; i++) {{
    const mid = (lo + hi) / 2;
    if (sim(price, varCost, fixed, newC, mid * newC, churnPct, cash).minC >= 0) lo = mid;
    else hi = mid;
  }}
  return lo;
}}
function recalc() {{
  const price = parseFloat(document.getElementById('c_price').value) || 0;
  const varCost = parseFloat(document.getElementById('c_var').value) || 0;
  const fixed = parseFloat(document.getElementById('c_fixed').value) || 0;
  const newC = parseInt(document.getElementById('c_new').value, 10) || 0;
  const spend = parseFloat(document.getElementById('c_spend').value) || 0;
  const churnPct = parseFloat(document.getElementById('c_churn').value) || 0;
  const cash = parseFloat(document.getElementById('c_cash').value) || 0;
  const res = sim(price, varCost, fixed, newC, spend, churnPct, cash);
  const maxCac = solveMaxCac(price, varCost, fixed, newC, churnPct, cash);
  const be = res.contrib > 0 ? Math.ceil((fixed + spend) / res.contrib) : 'IMPOSSIBLE';
  const curCac = newC > 0 ? (spend / newC) : 0;
  const ok = res.minC >= 0;
  document.getElementById('live_out').innerHTML = `
    <div class="kpi"><div class="k-lbl">Live Ending Cash (M12)</div><div class="k-val" style="color:${{ok ? '#10b981':'#ef4444'}}">${{CUR}} ${{res.ending.toLocaleString(undefined, {{maximumFractionDigits:2}})}}</div></div>
    <div class="kpi"><div class="k-lbl">Solved Max Viable CAC</div><div class="k-val" style="color:#38bdf8">${{CUR}} ${{maxCac.toFixed(2)}}</div></div>
    <div class="kpi"><div class="k-lbl">Implied Current CAC</div><div class="k-val" style="color:${{curCac <= maxCac ? '#10b981':'#ef4444'}}">${{CUR}} ${{curCac.toFixed(2)}}</div></div>
    <div class="kpi"><div class="k-lbl">Break-Even Units / Mo</div><div class="k-val">${{be}}</div></div>
  `;
}}
document.querySelectorAll('.calc-grid input').forEach(el => el.addEventListener('input', recalc));
recalc();
</script>
</body>
</html>"""
