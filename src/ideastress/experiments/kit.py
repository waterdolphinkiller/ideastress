"""One-Click Kill-Test Action Kit Generator.

Turns abstract validation advice into an immediately executable smoke-test bundle:
  1. Deploy-ready 1-page Smoke-Test Landing Page HTML (obsidian editorial design)
  2. 3 High-Intent Google / Reddit Ad Copies anchored to competitor pain themes
  3. 15 Mom-Test Customer Discovery Interview Questions (past behavior & real spend only)
"""

from __future__ import annotations

from decimal import Decimal
from html import escape
from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel

from ideastress.domain.models import AnalysisRequest


class KillTestKit(BaseModel):
    idea: str
    target_segment: str
    target_price_label: str
    ad_copies: List[Dict[str, str]]
    mom_test_questions: List[str]
    landing_page_html: str


def generate_kill_test_kit(
    request: AnalysisRequest,
    *,
    pain_themes: Dict[str, int] | None = None,
    max_viable_cac: Decimal | None = None,
) -> KillTestKit:
    """Generate a ready-to-launch smoke-test bundle (landing page + 3 ads + 15 interview questions)."""
    seg = request.customer_segment or "independent operators and small teams"
    price = request.financials.unit_price if request.financials else Decimal("49")
    cur = request.currency.upper()
    price_label = f"{cur} {price}/mo" if request.business_type.value == "saas" else f"{cur} {price}"
    top_pain = next(iter((pain_themes or {}).keys()), "pricing_and_billing").replace("_", " ")

    ad_copies = [
        {
            "channel": "Google Search (High Intent)",
            "headline": f"Simpler {request.idea[:38]} — {price_label}",
            "body": f"Built for {seg}. Skip bloated enterprise suites and {top_pain}. Join the founding pilot with transparent pricing.",
        },
        {
            "channel": "Reddit / Niche Community",
            "headline": f"Tired of {top_pain} with existing tools?",
            "body": f"We are testing a focused solution for {seg}: {request.idea}. Looking for 10 founding testers to stress-test our concierge pilot.",
        },
        {
            "channel": "Direct Cold Outreach / LinkedIn",
            "headline": f"Quick question about how you handle {request.idea[:35]}",
            "body": f"Not selling anything yet — researching why {seg} struggle with {top_pain}. Open to a 10-min chat about your current workflow?",
        },
    ]

    mom_test_questions = [
        f"Walk me through the last time you dealt with the workflow around '{request.idea}'. What triggered it?",
        "What tool, spreadsheet, or manual process did you use to solve it in the last 30 days?",
        "How many hours per week did you or your team spend on that workaround?",
        "Have you already paid money for any software, contractor, or agency to fix this? How much?",
        "What was the single most frustrating moment in your current solution last month?",
        "Have you actively searched for alternatives recently? Which ones did you try and why did you stop?",
        f"Does '{top_pain}' actually cost you money or customers, or is it just a mild annoyance?",
        "If your current workaround disappeared tomorrow, what would you immediately replace it with?",
        "Who else in your business has to approve spending money on a new tool like this?",
        "What budget category would a tool like this come out of?",
        "When you tried switching tools in the past, what stopped you from completing onboarding?",
        "What specific metric or outcome would prove to you in 14 days that a new tool paid for itself?",
        "Would you rather pay a flat monthly fee, per-usage fee, or a one-time setup fee?",
        f"If we delivered this manually as a concierge pilot next week at {price_label} (full refund guarantee), what would stop you from signing up today?",
        "Who are two other peers with this exact same problem that I should talk to next?",
    ]

    cac_note = f"Target CAC Ceiling: {cur} {max_viable_cac:,.2f}" if max_viable_cac else "Track click-to-intent conversion before building."

    landing_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(request.idea[:60])} — Founding Pilot</title>
  <style>
    :root {{ --bg:#080a0f; --card:#111622; --border:#252e42; --text:#eef2fb; --muted:#8c98b0; --accent:#38bdf8; --ok:#10b981; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Inter",sans-serif; line-height:1.6; }}
    .wrap {{ max-width:760px; margin:0 auto; padding:72px 24px; }}
    .pill {{ display:inline-block; padding:4px 12px; border-radius:999px; font-size:12px; font-weight:700; color:var(--accent); background:rgba(56,189,248,0.14); border:1px solid rgba(56,189,248,0.35); }}
    h1 {{ font-size:clamp(2rem,4vw,2.8rem); line-height:1.14; margin:16px 0 14px; letter-spacing:-0.025em; }}
    p.lead {{ color:var(--muted); font-size:1.08rem; margin:0 0 28px; }}
    .box {{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:28px; margin-bottom:24px; }}
    .price {{ font-size:2rem; font-weight:800; font-family:ui-monospace,monospace; color:var(--accent); }}
    ul {{ padding-left:20px; color:var(--muted); }}
    li {{ margin-bottom:8px; }}
    .form-row {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:18px; }}
    input[type=email] {{ flex:1; min-width:220px; padding:12px 14px; border-radius:10px; border:1px solid var(--border); background:var(--bg); color:var(--text); font-size:0.95rem; }}
    button {{ padding:12px 22px; border-radius:10px; border:none; background:var(--accent); color:#04111c; font-weight:700; font-size:0.95rem; cursor:pointer; }}
    .fine {{ font-size:12px; color:var(--muted); margin-top:12px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <span class="pill">FOUNDING PILOT · TRANSPARENT SMOKE TEST</span>
    <h1>{escape(request.idea)}</h1>
    <p class="lead">Built specifically for {escape(seg)} tired of {escape(top_pain)}.</p>
    <div class="box">
      <div class="price">{escape(price_label)}</div>
      <p style="margin:6px 0 16px;color:var(--muted);">Founding pilot pricing · Full refund guarantee if we don't save you measurable time in 14 days.</p>
      <ul>
        <li>Zero bloat: solves your core workflow without enterprise setup fees</li>
        <li>Direct founder onboarding &amp; concierge setup during the pilot</li>
        <li>Transparent cancellation anytime — no hidden lock-in</li>
      </ul>
      <form class="form-row" onsubmit="event.preventDefault(); document.getElementById('msg').textContent='Intent recorded! Replace this form action with Formspree, Tally, or Stripe Checkout link.';">
        <input type="email" required placeholder="Enter your work email for pilot access..." />
        <button type="submit">Reserve Pilot Spot</button>
      </form>
      <div id="msg" class="fine" style="color:var(--ok);"></div>
      <div class="fine">Smoke-Test Note ({escape(cac_note)}): Connect this form to Tally/Formspree or a Stripe Payment Link to measure real paid intent.</div>
    </div>
  </div>
</body>
</html>"""

    return KillTestKit(
        idea=request.idea,
        target_segment=seg,
        target_price_label=price_label,
        ad_copies=ad_copies,
        mom_test_questions=mom_test_questions,
        landing_page_html=landing_html,
    )


def save_kill_test_kit(kit: KillTestKit, out_dir: str | Path) -> Path:
    """Write the complete smoke-test bundle (landing page + ads + interview guide) to disk."""
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / "smoke_test_landing.html").write_text(kit.landing_page_html, encoding="utf-8")

    md_lines = [
        f"# Kill-Test Action Kit: {kit.idea}",
        f"- **Target Segment:** {kit.target_segment}",
        f"- **Target Price:** {kit.target_price_label}",
        "",
        "## 1. High-Intent Ad Copies (3 Channels)",
        "",
    ]
    for ad in kit.ad_copies:
        md_lines += [f"### {ad['channel']}", f"- **Headline:** {ad['headline']}", f"- **Body:** {ad['body']}", ""]

    md_lines += ["## 2. 15 Mom-Test Discovery Questions (Past Behavior & Spend Only)", ""]
    for idx, q in enumerate(kit.mom_test_questions, 1):
        md_lines.append(f"{idx}. {q}")

    (p / "kill_test_playbook.md").write_text("\n".join(md_lines), encoding="utf-8")
    return p
