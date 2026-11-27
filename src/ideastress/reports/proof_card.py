"""Shareable 1200x630 Falsification Proof Card SVG Generator (for X / Reddit / Indie Hackers).

Creates a zero-dependency, high-contrast obsidian social proof card displaying:
  - Verdict badge & idea title
  - 1,000-run Monte Carlo Survival Probability
  - Max Viable CAC vs Real Paid CPC Channel Verdict
  - Embedded `Stress-tested with IdeaStress` viral attribution footer
"""

from __future__ import annotations

from html import escape

from ideastress.domain.models import AnalysisResult


def render_proof_card_svg(result: AnalysisResult) -> str:
    """Render a crisp 1200x630 OpenGraph-ready SVG Proof Card."""
    v = result.decision.verdict.value
    colors = {
        "GO": "#10b981",
        "CONDITIONAL_GO": "#f59e0b",
        "PIVOT": "#fb923c",
        "NO_GO": "#ef4444",
        "INSUFFICIENT_DATA": "#94a3b8",
    }
    vc = colors.get(v, "#38bdf8")
    cur = escape(result.financials.currency)
    fr = result.financials.reverse_frontier
    mc = result.financials.monte_carlo
    cf = result.channel_falsification

    idea_title = escape(result.request.idea[:54] + ("..." if len(result.request.idea) > 54 else ""))
    surv_str = f"{mc.survival_probability_pct}%" if mc else "N/A"
    max_cac_str = f"{cur} {fr.max_viable_cac}" if fr.max_viable_cac is not None else "N/A"
    cpc_verdict = escape(cf.verdict) if cf else "NOT_RUN"
    implied_cac = f"{cur} {cf.implied_paid_cac}" if cf else "N/A"
    cpc_color = "#ef4444" if cpc_verdict == "CHANNEL_IMPOSSIBLE" else ("#f59e0b" if cpc_verdict == "CHANNEL_TIGHT" else "#10b981")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#080a0f"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect x="44" y="44" width="1112" height="542" rx="24" fill="#101521" stroke="#243047" stroke-width="2"/>

  <!-- Top Brand + Verdict -->
  <circle cx="96" cy="98" r="8" fill="#38bdf8"/>
  <text x="116" y="105" fill="#edf2fb" font-family="Inter, -apple-system, sans-serif" font-size="22" font-weight="800" letter-spacing="2">IDEASTRESS // PROOF CARD</text>
  <rect x="860" y="72" width="256" height="48" rx="24" fill="{vc}" fill-opacity="0.16" stroke="{vc}" stroke-width="2"/>
  <text x="988" y="103" text-anchor="middle" fill="{vc}" font-family="ui-monospace, monospace" font-size="22" font-weight="800">{escape(v)}</text>

  <!-- Idea Title -->
  <text x="86" y="185" fill="#ffffff" font-family="Inter, -apple-system, sans-serif" font-size="38" font-weight="800">{idea_title}</text>
  <text x="86" y="224" fill="#8a95ad" font-family="Inter, -apple-system, sans-serif" font-size="20">Deterministic Reverse Unit-Economics · 1,000-Run Monte Carlo · Real CPC Falsification</text>

  <!-- 3 KPI Panels -->
  <rect x="86" y="268" width="320" height="190" rx="16" fill="#161d2e" stroke="#26324a"/>
  <text x="114" y="310" fill="#8a95ad" font-family="ui-monospace, monospace" font-size="15">12M SURVIVAL (1,000 RUNS)</text>
  <text x="114" y="380" fill="#38bdf8" font-family="ui-monospace, monospace" font-size="52" font-weight="800">{surv_str}</text>
  <text x="114" y="425" fill="#cbd5e1" font-family="Inter, sans-serif" font-size="17">Risk: {escape(mc.bankruptcy_risk_label) if mc else 'N/A'}</text>

  <rect x="440" y="268" width="320" height="190" rx="16" fill="#161d2e" stroke="#26324a"/>
  <text x="468" y="310" fill="#8a95ad" font-family="ui-monospace, monospace" font-size="15">MAX VIABLE CAC CEILING</text>
  <text x="468" y="380" fill="#edf2fb" font-family="ui-monospace, monospace" font-size="44" font-weight="800">{max_cac_str}</text>
  <text x="468" y="425" fill="#cbd5e1" font-family="Inter, sans-serif" font-size="17">Min Price: {cur} {fr.min_viable_unit_price if fr.min_viable_unit_price else 'N/A'}</text>

  <rect x="794" y="268" width="320" height="190" rx="16" fill="#161d2e" stroke="#26324a"/>
  <text x="822" y="310" fill="#8a95ad" font-family="ui-monospace, monospace" font-size="15">GOOGLE ADS CPC CHECK</text>
  <text x="822" y="370" fill="{cpc_color}" font-family="ui-monospace, monospace" font-size="26" font-weight="800">{cpc_verdict}</text>
  <text x="822" y="425" fill="#cbd5e1" font-family="Inter, sans-serif" font-size="17">Implied CAC: {implied_cac}</text>

  <!-- Viral Attribution Footer -->
  <line x1="86" y1="504" x2="1114" y2="504" stroke="#243047" stroke-width="1.5"/>
  <text x="86" y="548" fill="#8a95ad" font-family="ui-monospace, monospace" font-size="17">Stress-tested with IdeaStress (MIT Open-Source) · pip install ideastress</text>
  <text x="1114" y="548" text-anchor="end" fill="#38bdf8" font-family="ui-monospace, monospace" font-size="17">waterdolphinkiller.github.io/ideastress</text>
</svg>"""
