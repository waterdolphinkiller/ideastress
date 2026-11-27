"""Build the Bespoke Luxury Editorial Flagship `index.html` for IdeaStress v0.8.1.

Design Direction: Swiss Private Wealth × Architectural Financial Monograph
  - Warm Obsidian (#0A0A0B), Elevated Charcoal (#121215), Brushed Champagne Gold (#C9A96E), Warm Ivory (#F4F1EA)
  - Cormorant Garamond Display Serif + Plus Jakarta Sans + JetBrains Mono (tabular-nums)
  - GPU-composited ambient Monte Carlo silk canvas in Hero
  - Live Interactive Hero Falsification Instrument (3 presets + live sliders + animated fan chart + Sync-to-Workbench)
  - Sliding champagne-gold underline tab bar for all 10 live deterministic calculators
  - Per-tool 3-Step Quick Guide, Exact Formula, Worked Example, and 40 FAQs in clean editorial drawers
  - Zero dead links, zero generic AI neon styling, custom ultra-thin dark scrollbar, EN / 中文 bilingual toggle
"""

from __future__ import annotations

import html as html_lib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_seo_site as ssg
from geo_seo_content import TOOL_GEO_CONTENT

TABS = [
    ("frontier",   "01", "Reverse Frontier",   "反向红线与蒙特卡洛", "1,000× Monte Carlo & CAC",  "1,000 次仿真与 CAC 上限"),
    ("quit_job",   "02", "Quit-Job MRR",       "辞职替代 MRR",       "Stripe vs MoR & Tax",       "税后薪资替代与通道费"),
    ("freemium",   "03", "Freemium Drag",      "免费版拖累压测",     "Free-tier subsidy stress",  "免费用户算力补贴压测"),
    ("social_cpm", "04", "Meta/TikTok CPM",    "Meta/TikTok 信息流", "CPM → CTR → ROAS funnel",   "曝光点击到转化全漏斗"),
    ("ai_margin",  "05", "AI Token Margin",    "AI Token 毛利",      "LLM COGS & Whale limit",    "大模型成本与巨鲸阈值"),
    ("geo",        "06", "Geo-Arbitrage CPC",  "5 国 CPC 套利",      "US / UK / DE / SG / MY",    "五国买量套利空间对比"),
    ("breakeven",  "07", "Break-Even",         "盈亏平衡",           "Unit floor & overhead",     "保本销量与固定成本线"),
    ("saas",       "08", "SaaS LTV / CAC",     "SaaS LTV/CAC",       "Payback & 2026 medians",    "回本周期与行业中位数"),
    ("ecom",       "09", "E-Com ROAS",         "电商 ROAS 底线",     "First-order margin floor",  "首单毛利与投流盈亏线"),
    ("runway",     "10", "Startup Runway",     "现金跑道压测",       "Shock-tested burn months",  "营收骤降与烧钱抗压月数"),
]


def remap_luxury_palette(text: str) -> str:
    """Harmonize internal engine colors to Warm Obsidian & Brushed Champagne Gold."""
    replacements = {
        "#080a0f": "#0A0A0B",
        "#101521": "#121215",
        "#243047": "#27241F",
        "#38bdf8": "#C9A96E",
        "#8a95ad": "#9A948A",
        "#edf2fb": "#F4F1EA",
        "#10b981": "#4E9F7C",
        "#f59e0b": "#C89248",
        "#ef4444": "#C45C5C",
        "#fca5a5": "#D46B6B",
        "#fcd34d": "#E3C996",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def render_panel_geo_drawer(tool_key: str) -> str:
    geo = TOOL_GEO_CONTENT[tool_key]
    steps_li = "".join(f"<li>{html_lib.escape(s)}</li>" for s in geo["how_to"])
    faqs_html = "".join(
        f'<div class="faq-card"><h4>{html_lib.escape(q)}</h4><p>{html_lib.escape(a)}</p></div>'
        for q, a in geo["faqs"]
    )
    formula_esc = html_lib.escape(geo["formula"])
    example_esc = html_lib.escape(geo["worked_example"])
    return f"""
<details class="ref-drawer">
  <summary class="ref-summary">
    <span class="ref-summary-left">
      <span class="ref-kicker">METHODOLOGY &amp; FAQ</span>
      <span class="ref-title">3-Step Guide, Exact Formula, Worked Example &amp; 4 FAQs</span>
    </span>
    <span class="ref-chevron" aria-hidden="true">+</span>
  </summary>
  <div class="ref-body">
    <div class="ref-grid">
      <div class="ref-block">
        <div class="ref-label">01 · 3-STEP QUICK GUIDE</div>
        <ol class="ref-steps">{steps_li}</ol>
      </div>
      <div class="ref-block">
        <div class="ref-label">02 · DETERMINISTIC FORMULA &amp; WORKED EXAMPLE</div>
        <pre class="ref-formula mono">{formula_esc}</pre>
        <p class="ref-example">{example_esc}</p>
      </div>
    </div>
    <div class="ref-label" style="margin-top:24px;">03 · FREQUENTLY ASKED QUESTIONS</div>
    <div class="faq-grid">{faqs_html}</div>
  </div>
</details>
"""


panels_html = []
all_faqs = []
for i, (k, num, en, zh, sub_en, sub_zh) in enumerate(TABS):
    raw = ssg.TOOL_HTML[k].split("<script>")[0]
    raw = remap_luxury_palette(raw)
    if k == "frontier":
        raw = raw.replace('<button id="btn_export_yaml"', '<button type="button" id="btn_export_yaml"')
        raw = raw.replace(
            '<button id="btn_proof_card" class="btn" style="flex:1;justify-content:center;">Download Proof Card SVG</button>',
            '<button type="button" id="btn_proof_card" class="btn" style="flex:1;justify-content:center;">Proof Card SVG</button>\n'
            '      <button type="button" id="btn_export_csv" class="btn" style="flex:1;justify-content:center;">Export 12m CSV</button>\n'
            '      <button type="button" id="btn_share_url" class="btn" style="flex:1;justify-content:center;">Copy Share Link</button>',
        )
    geo_drawer = render_panel_geo_drawer(k)
    active_cls = " active" if i == 0 else ""
    panels_html.append(f'<div class="panel{active_cls}" id="panel-{k}">\n{raw}\n{geo_drawer}\n</div>')
    all_faqs.extend(TOOL_GEO_CONTENT[k]["faqs"])

tab_buttons = "\n        ".join(
    f'<button type="button" class="inst-tile{" active" if i == 0 else ""}" data-switch="{k}" data-num="{num}" data-en="{en}" data-zh="{zh}" data-sub-en="{sub_en}" data-sub-zh="{sub_zh}">'
    f'<span class="it-top"><span class="it-num">{num}</span><span class="it-dot" aria-hidden="true"></span></span>'
    f'<span class="it-name">{en}</span>'
    f'<span class="it-sub">{sub_en}</span>'
    f'</button>'
    for i, (k, num, en, zh, sub_en, sub_zh) in enumerate(TABS)
)

ld_json = json.dumps(
    {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebApplication",
                "name": "IdeaStress — Deterministic Business Falsification & 10-Calculator Suite",
                "url": "https://waterdolphinkiller.github.io/ideastress/",
                "applicationCategory": "BusinessApplication",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                "description": "Stress-test your startup idea with 1,000-run Monte Carlo survival math, Auto-Fix rescue pricing, 10 deterministic calculators, and a 12-tool MCP engine.",
            },
            {
                "@type": "HowTo",
                "name": "How to Stress-Test a Startup Idea with IdeaStress",
                "description": "Three-step deterministic workflow to falsify startup unit economics before writing code.",
                "step": [
                    {"@type": "HowToStep", "position": 1, "text": "Enter unit price, variable cost, fixed monthly overhead, and starting cash (or pick a 1-click SaaS, AI Wrapper, or DTC E-Com preset)."},
                    {"@type": "HowToStep", "position": 2, "text": "Inspect the 1,000-run Monte Carlo survival probability, solved Max Viable CAC ceiling, and Google Ads CPC channel verdict."},
                    {"@type": "HowToStep", "position": 3, "text": "Apply the Auto-Fix pricing or annual-prepay rescue plan, export venture.yaml or a 1200x630 Proof Card SVG, or run ideastress mcp inside your IDE."}
                ]
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a},
                    }
                    for q, a in all_faqs
                ],
            },
        ],
    },
    indent=2,
)

ENGINE_JS_LUXURY = remap_luxury_palette(ssg.ENGINE_JS).replace("document.getElementById('f_payroll')?.value", "0")

LUXURY_CSS = r"""
:root {
  color-scheme: dark;
  --bg: #0A0A0B;
  --bg-elev: #111114;
  --surface: #141418;
  --surface-2: #1A1A1F;
  --border: rgba(214, 198, 168, 0.14);
  --border-hi: rgba(214, 198, 168, 0.34);
  --text: #F4F1EA;
  --muted: #9A948A;
  --dim: #635F58;
  --accent: #C9A96E;
  --accent-hi: #E3C996;
  --accent-soft: rgba(201, 169, 110, 0.11);
  --ok: #4E9F7C;
  --warn: #C89248;
  --bad: #C45C5C;
  --radius: 14px;
  --serif: "Cormorant Garamond", Georgia, "Times New Roman", serif;
  --sans: "Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}

*, *::before, *::after { box-sizing: border-box; }

html {
  scroll-behavior: smooth;
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  scrollbar-width: thin;
  scrollbar-color: rgba(201,169,110,0.3) var(--bg);
}

body {
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--text);
  overflow-x: hidden;
  font-feature-settings: "ss01", "cv01";
}

/* Custom Luxury Dark Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(201, 169, 110, 0.25); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(201, 169, 110, 0.52); }

::selection { background: rgba(201, 169, 110, 0.26); color: #fff; }

a { color: var(--accent-hi); text-decoration: none; transition: color 0.25s var(--ease-out); }
a:hover { color: #fff; }

.mono { font-family: var(--mono); font-variant-numeric: tabular-nums; }
.serif { font-family: var(--serif); }
.container { max-width: 1240px; margin: 0 auto; padding: 0 28px; }

/* Subtle architectural grid texture */
.arch-grid-bg {
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    linear-gradient(to right, rgba(214, 198, 168, 0.028) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(214, 198, 168, 0.028) 1px, transparent 1px);
  background-size: 88px 88px;
  mask-image: radial-gradient(ellipse 80% 60% at 50% 15%, #000 30%, transparent 100%);
  -webkit-mask-image: radial-gradient(ellipse 80% 60% at 50% 15%, #000 30%, transparent 100%);
}

/* Header Navigation */
.site-header {
  position: sticky; top: 0; z-index: 60;
  background: rgba(10, 10, 11, 0.78);
  backdrop-filter: blur(18px) saturate(140%);
  -webkit-backdrop-filter: blur(18px) saturate(140%);
  border-bottom: 1px solid var(--border);
  transition: background 0.35s var(--ease-out), border-color 0.35s var(--ease-out);
}
.site-header.scrolled {
  background: rgba(10, 10, 11, 0.92);
  border-bottom-color: rgba(214, 198, 168, 0.22);
}
.nav-inner {
  display: flex; align-items: center; justify-content: space-between;
  height: 70px; gap: 20px;
}
.brand {
  display: inline-flex; align-items: center; gap: 12px;
  color: var(--text); cursor: pointer; background: none; border: 0; padding: 0;
  font-family: var(--serif); font-size: 1.38rem; font-weight: 600; letter-spacing: 0.14em;
}
.brand-mark { width: 26px; height: 26px; flex-shrink: 0; }
.brand-ver {
  font-family: var(--mono); font-size: 0.66rem; letter-spacing: 0.08em;
  color: var(--accent); border: 1px solid var(--border-hi);
  padding: 2px 7px; border-radius: 999px; margin-left: 2px;
}
.nav-links {
  display: flex; align-items: center; gap: 30px;
  font-size: 0.83rem; letter-spacing: 0.06em; text-transform: uppercase;
}
.nav-links a {
  color: var(--muted); position: relative; padding: 4px 0;
}
.nav-links a::after {
  content: ""; position: absolute; left: 0; right: 0; bottom: -2px; height: 1px;
  background: var(--accent); transform: scaleX(0); transform-origin: right;
  transition: transform 0.35s var(--ease-out);
}
.nav-links a:hover { color: var(--text); }
.nav-links a:hover::after { transform: scaleX(1); transform-origin: left; }

.nav-actions { display: flex; align-items: center; gap: 10px; }

/* Buttons — Tactile Luxury */
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  background: rgba(26, 26, 31, 0.9); color: var(--text);
  border: 1px solid var(--border-hi); border-radius: 8px;
  padding: 9px 16px; font-size: 0.82rem; font-weight: 500; letter-spacing: 0.02em;
  font-family: var(--sans); cursor: pointer;
  transition: transform 0.25s var(--ease-out), border-color 0.25s var(--ease-out), background 0.25s var(--ease-out), color 0.25s var(--ease-out), box-shadow 0.35s var(--ease-out);
  position: relative; overflow: hidden;
}
.btn:hover {
  border-color: var(--accent); color: #fff;
  background: rgba(34, 32, 29, 0.95);
  transform: translateY(-1px);
}
.btn:active { transform: translateY(0); }

.btn.primary, .btn-gold {
  background: linear-gradient(135deg, #D5B880 0%, #B79252 100%);
  color: #0B0A08; border-color: rgba(235, 211, 163, 0.7); font-weight: 600;
  box-shadow: 0 8px 26px rgba(201, 169, 110, 0.16);
}
.btn.primary::before, .btn-gold::before {
  content: ""; position: absolute; top: 0; left: -120%; width: 80%; height: 100%;
  background: linear-gradient(110deg, transparent, rgba(255,255,255,0.42), transparent);
  transition: left 0.65s var(--ease-out);
}
.btn.primary:hover::before, .btn-gold:hover::before { left: 135%; }
.btn.primary:hover, .btn-gold:hover {
  color: #050504; border-color: #F0DAA9;
  box-shadow: 0 12px 32px rgba(201, 169, 110, 0.28);
}

.btn-ghost {
  background: transparent; border: 1px solid var(--border); color: var(--muted);
}
.btn-ghost:hover { color: var(--text); border-color: var(--border-hi); background: rgba(255,255,255,0.03); }

/* HERO SECTION */
.hero-wrap {
  position: relative; z-index: 1;
  padding: 64px 0 84px;
  border-bottom: 1px solid var(--border);
  overflow: hidden;
}
#hero_canvas {
  position: absolute; inset: 0; width: 100%; height: 100%;
  pointer-events: none; opacity: 0.72;
}
.hero-grid {
  position: relative; z-index: 2;
  display: grid; grid-template-columns: 1.06fr 0.94fr;
  gap: 52px; align-items: center;
}
.edition-kicker {
  display: inline-flex; align-items: center; gap: 10px;
  font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.18em;
  color: var(--accent); text-transform: uppercase;
  margin-bottom: 22px;
}
.edition-kicker .hairline {
  width: 28px; height: 1px; background: var(--accent); display: inline-block;
}
.hero-title {
  font-family: var(--serif);
  font-size: clamp(2.85rem, 5.1vw, 4.75rem);
  font-weight: 400; line-height: 1.03; letter-spacing: -0.02em;
  margin: 0 0 22px; color: var(--text);
}
.hero-title em {
  font-style: italic; color: var(--accent-hi); font-weight: 400;
}
.hero-lead {
  font-size: 1.02rem; color: var(--muted); max-width: 540px;
  margin: 0 0 32px; font-weight: 400; line-height: 1.72;
}
.hero-ctas { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 44px; }
.hero-ctas .btn { padding: 13px 24px; font-size: 0.88rem; }

.hero-metrics {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px; padding-top: 26px;
  border-top: 1px solid var(--border);
}
.hm-item .hm-val {
  font-family: var(--serif); font-size: 1.9rem; font-weight: 500;
  color: var(--text); line-height: 1.1;
}
.hm-item .hm-lbl {
  font-size: 0.72rem; color: var(--muted); letter-spacing: 0.05em;
  margin-top: 4px; text-transform: uppercase;
}

/* HERO INTERACTIVE INSTRUMENT (RIGHT COLUMN) */
.instrument-frame {
  background: linear-gradient(180deg, rgba(22, 22, 26, 0.92) 0%, rgba(15, 15, 18, 0.96) 100%);
  border: 1px solid var(--border-hi);
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 36px 90px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 245, 225, 0.08);
  position: relative;
}
.instrument-head {
  display: flex; align-items: center; justify-content: space-between;
  padding-bottom: 16px; margin-bottom: 18px;
  border-bottom: 1px solid var(--border);
  gap: 10px; flex-wrap: wrap;
}
.inst-tag {
  font-family: var(--mono); font-size: 0.68rem; letter-spacing: 0.14em;
  color: var(--accent); text-transform: uppercase;
  display: inline-flex; align-items: center; gap: 8px;
}
.inst-dot {
  width: 6px; height: 6px; border-radius: 50%; background: var(--ok);
  box-shadow: 0 0 10px rgba(78, 159, 124, 0.8);
}
.inst-presets { display: flex; gap: 6px; flex-wrap: wrap; }
.inst-preset-btn {
  background: transparent; color: var(--muted);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 5px 10px; font-size: 0.72rem; font-family: var(--mono);
  cursor: pointer; transition: all 0.25s var(--ease-out);
}
.inst-preset-btn:hover { color: var(--text); border-color: var(--border-hi); }
.inst-preset-btn.active {
  background: var(--accent-soft); color: var(--accent-hi);
  border-color: rgba(201, 169, 110, 0.55);
}

.inst-kpis {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
  margin-bottom: 16px;
}
.inst-kpi {
  background: rgba(10, 10, 11, 0.65); border: 1px solid var(--border);
  border-radius: 10px; padding: 12px 14px;
}
.inst-kpi .ik-l {
  font-family: var(--mono); font-size: 0.63rem; letter-spacing: 0.1em;
  color: var(--muted); text-transform: uppercase;
}
.inst-kpi .ik-v {
  font-family: var(--mono); font-size: 1.32rem; font-weight: 600;
  margin-top: 4px; color: var(--text);
}
.inst-kpi .ik-s { font-size: 0.7rem; color: var(--dim); margin-top: 2px; }

.inst-chart-box {
  background: rgba(9, 9, 11, 0.82); border: 1px solid var(--border);
  border-radius: 12px; padding: 12px 14px 8px; margin-bottom: 16px;
}
.inst-chart-head {
  display: flex; justify-content: space-between; align-items: center; gap: 12px;
  font-family: var(--mono); font-size: 0.66rem; letter-spacing: 0.08em;
  color: var(--muted); margin-bottom: 6px;
}
.inst-sliders { display: grid; grid-template-columns: 1fr; gap: 12px; margin-bottom: 16px; }
.slider-row label {
  display: flex; justify-content: space-between; font-size: 0.76rem;
  color: var(--muted); margin-bottom: 5px;
}
.slider-row label strong { color: var(--text); font-family: var(--mono); font-weight: 500; }

/* Bespoke Hairline Gold Range Input */
input[type="range"].gold-range {
  -webkit-appearance: none; appearance: none; width: 100%; height: 2px;
  background: rgba(214, 198, 168, 0.22); border-radius: 999px; outline: none;
  cursor: pointer;
}
input[type="range"].gold-range::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none; width: 14px; height: 14px;
  border-radius: 50%; background: var(--accent-hi);
  border: 2px solid #0A0A0B;
  box-shadow: 0 0 0 1px rgba(201,169,110,0.6), 0 4px 12px rgba(0,0,0,0.5);
  transition: transform 0.2s var(--ease-out);
}
input[type="range"].gold-range::-webkit-slider-thumb:hover { transform: scale(1.18); }
input[type="range"].gold-range::-moz-range-thumb {
  width: 14px; height: 14px; border-radius: 50%; background: var(--accent-hi);
  border: 2px solid #0A0A0B;
}

.inst-verdict {
  border-radius: 10px; padding: 11px 14px; font-size: 0.8rem;
  border: 1px solid var(--border); background: rgba(201,169,110,0.06);
  margin-bottom: 14px; line-height: 1.5; color: var(--text);
}
.inst-verdict.ok { border-color: rgba(78,159,124,0.45); background: rgba(78,159,124,0.08); }
.inst-verdict.warn { border-color: rgba(200,146,72,0.45); background: rgba(200,146,72,0.08); }
.inst-verdict.bad { border-color: rgba(196,92,92,0.45); background: rgba(196,92,92,0.08); }

/* SECTIONS */
.editorial-section {
  position: relative; z-index: 1;
  padding: 88px 0;
  border-bottom: 1px solid var(--border);
}
.sec-head {
  display: flex; justify-content: space-between; align-items: flex-end;
  gap: 24px; margin-bottom: 42px; flex-wrap: wrap;
}
.sec-kicker {
  font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.16em;
  color: var(--accent); text-transform: uppercase; margin-bottom: 10px;
}
.sec-title {
  font-family: var(--serif); font-size: clamp(2rem, 3.3vw, 3rem);
  font-weight: 400; line-height: 1.1; margin: 0; letter-spacing: -0.015em;
}
.sec-lead {
  color: var(--muted); max-width: 480px; margin: 0; font-size: 0.92rem; line-height: 1.65;
}

/* 4-PILLAR EDITORIAL PLATES */
.plates-grid {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}
.plate {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 26px 22px;
  display: flex; flex-direction: column; justify-content: space-between;
  transition: transform 0.4s var(--ease-out), border-color 0.35s var(--ease-out), background 0.35s var(--ease-out);
  cursor: pointer; text-align: left; color: inherit;
}
.plate:hover {
  transform: translateY(-4px);
  border-color: var(--border-hi);
  background: var(--surface-2);
}
.plate-num {
  font-family: var(--serif); font-size: 1.65rem; font-style: italic;
  color: var(--accent); line-height: 1; margin-bottom: 18px;
}
.plate h3 {
  font-family: var(--serif); font-size: 1.38rem; font-weight: 500;
  margin: 0 0 10px; line-height: 1.22; color: var(--text);
}
.plate p {
  font-size: 0.84rem; color: var(--muted); margin: 0 0 20px; line-height: 1.65;
}
.plate-link {
  font-family: var(--mono); font-size: 0.72rem; letter-spacing: 0.08em;
  color: var(--accent-hi); text-transform: uppercase;
  display: inline-flex; align-items: center; gap: 6px;
}

/* 10-CALCULATOR ARCHITECTURAL 5x2 SELECTOR MATRIX (ALL 10 VISIBLE AT ONCE) */
.matrix-bar-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px; gap: 12px; flex-wrap: wrap;
}
.matrix-counter {
  font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.12em;
  color: var(--accent-hi); text-transform: uppercase;
  display: inline-flex; align-items: center; gap: 8px;
}
.matrix-counter .mc-pill {
  background: var(--accent-soft); border: 1px solid rgba(201,169,110,0.4);
  padding: 2px 9px; border-radius: 999px; color: var(--accent-hi);
}
.inst-matrix {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 28px;
}
.inst-tile {
  position: relative;
  display: flex; flex-direction: column; align-items: flex-start; text-align: left;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 11px;
  padding: 13px 14px 12px;
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.28s var(--ease-out), border-color 0.28s var(--ease-out), background 0.28s var(--ease-out), box-shadow 0.3s var(--ease-out);
}
.inst-tile::before {
  content: "";
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--accent), var(--accent-hi));
  transform: scaleX(0); transform-origin: left;
  transition: transform 0.32s var(--ease-out);
}
.inst-tile:hover {
  transform: translateY(-2px);
  border-color: var(--border-hi);
  background: var(--surface-2);
}
.inst-tile.active {
  background: linear-gradient(180deg, rgba(201,169,110,0.12) 0%, rgba(22,22,26,0.96) 100%);
  border-color: rgba(201,169,110,0.55);
  box-shadow: 0 12px 28px rgba(0,0,0,0.42);
}
.inst-tile.active::before { transform: scaleX(1); }
.it-top {
  width: 100%; display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 6px;
}
.it-num {
  font-family: var(--mono); font-size: 0.68rem; letter-spacing: 0.1em;
  color: var(--muted); transition: color 0.25s;
}
.inst-tile.active .it-num { color: var(--accent-hi); font-weight: 600; }
.it-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: transparent; border: 1px solid rgba(214,198,168,0.25);
  transition: all 0.25s var(--ease-out);
}
.inst-tile.active .it-dot {
  background: var(--accent-hi); border-color: var(--accent-hi);
  box-shadow: 0 0 8px rgba(227,201,150,0.85);
}
.it-name {
  font-family: var(--sans); font-size: 0.84rem; font-weight: 600;
  color: var(--text); line-height: 1.25; margin-bottom: 3px;
}
.inst-tile.active .it-name { color: #fff; }
.it-sub {
  font-size: 0.7rem; color: var(--dim); line-height: 1.35;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%;
}
.inst-tile.active .it-sub { color: var(--muted); }

/* WORKBENCH INTERNAL CALCULATOR STYLING (HARMONIZED WITH ssg.TOOL_HTML) */
.panel { display: none; opacity: 0; transform: translateY(8px); }
.panel.active { display: block; animation: panelIn 0.42s var(--ease-out) forwards; }
@keyframes panelIn {
  to { opacity: 1; transform: translateY(0); }
}

.workspace { display: grid; grid-template-columns: 385px 1fr; gap: 24px; align-items: start; }
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 24px;
}
.card h2 {
  font-family: var(--serif); font-size: 1.5rem; font-weight: 500;
  margin: 0 0 6px; letter-spacing: -0.01em; color: var(--text);
}
.card .sub { margin: 0 0 18px; color: var(--muted); font-size: 0.84rem; }
.field { margin-bottom: 13px; }
.field label {
  display: flex; justify-content: space-between;
  font-size: 0.76rem; color: var(--muted); margin-bottom: 5px;
}
.field input, .field select {
  width: 100%; background: var(--bg); color: var(--text);
  border: 1px solid var(--border); border-radius: 8px;
  padding: 9px 11px; font-size: 0.88rem; font-family: var(--mono);
  transition: border-color 0.25s var(--ease-out), box-shadow 0.25s var(--ease-out);
}
.field input:focus, .field select:focus {
  outline: none; border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(201, 169, 110, 0.14);
}
.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 11px; }
.kpi-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(168px, 1fr));
  gap: 12px; margin-bottom: 16px;
}
.kpi {
  background: var(--bg-elev); border: 1px solid var(--border);
  border-radius: 12px; padding: 14px 16px;
}
.kpi .kl {
  font-family: var(--mono); font-size: 0.66rem; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.08em;
}
.kpi .kv {
  font-size: 1.3rem; font-weight: 600; margin-top: 5px;
  font-family: var(--mono); color: var(--text);
}
.kpi .ks { font-size: 0.73rem; color: var(--dim); margin-top: 3px; }

.alert-box {
  border-radius: 10px; padding: 13px 15px; font-size: 0.85rem;
  border: 1px solid var(--border); background: var(--bg-elev); margin-bottom: 16px;
}
.alert-box.ok { border-color: rgba(78,159,124,0.45); background: rgba(78,159,124,0.08); }
.alert-box.warn { border-color: rgba(200,146,72,0.45); background: rgba(200,146,72,0.08); }
.alert-box.bad { border-color: rgba(196,92,92,0.45); background: rgba(196,92,92,0.08); }

.chart-box {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px; margin-bottom: 16px;
}
.chart-title {
  font-family: var(--mono); font-size: 0.7rem; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.09em; margin-bottom: 10px;
}
.pill {
  display: inline-block; padding: 2px 9px; border-radius: 999px;
  font-size: 0.72rem; font-weight: 600; border: 1px solid var(--border);
  font-family: var(--mono);
}

/* EDITORIAL REFERENCE DRAWER (GUIDE + FORMULA + FAQS) */
.ref-drawer {
  margin-top: 22px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 14px;
  overflow: hidden; transition: border-color 0.3s var(--ease-out);
}
.ref-drawer[open] { border-color: var(--border-hi); }
.ref-summary {
  list-style: none; cursor: pointer; padding: 18px 24px;
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  user-select: none;
}
.ref-summary::-webkit-details-marker { display: none; }
.ref-summary-left { display: flex; flex-direction: column; gap: 3px; }
.ref-kicker {
  font-family: var(--mono); font-size: 0.66rem; letter-spacing: 0.14em;
  color: var(--accent); text-transform: uppercase;
}
.ref-title { font-family: var(--serif); font-size: 1.24rem; color: var(--text); }
.ref-chevron {
  font-family: var(--mono); font-size: 1.2rem; color: var(--accent);
  transition: transform 0.3s var(--ease-out);
}
.ref-drawer[open] .ref-chevron { transform: rotate(45deg); }
.ref-body {
  padding: 0 24px 24px; border-top: 1px solid var(--border);
}
.ref-grid {
  display: grid; grid-template-columns: 1fr 1.15fr; gap: 22px; margin-top: 20px;
}
.ref-label {
  font-family: var(--mono); font-size: 0.67rem; letter-spacing: 0.14em;
  color: var(--accent); margin-bottom: 10px; text-transform: uppercase;
}
.ref-steps {
  margin: 0; padding-left: 18px; color: var(--muted); font-size: 0.87rem;
  display: flex; flex-direction: column; gap: 8px;
}
.ref-formula {
  background: var(--bg); border: 1px solid var(--border); border-radius: 10px;
  padding: 13px 15px; overflow-x: auto; font-size: 0.78rem;
  color: var(--accent-hi); margin: 0 0 12px; line-height: 1.65;
}
.ref-example { margin: 0; font-size: 0.85rem; color: var(--muted); line-height: 1.65; }
.faq-grid {
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px;
}
.faq-card {
  background: var(--bg-elev); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px 18px;
}
.faq-card h4 {
  margin: 0 0 6px; font-size: 0.9rem; font-weight: 600; color: var(--text);
}
.faq-card p { margin: 0; font-size: 0.82rem; color: var(--muted); line-height: 1.6; }

/* BENCHMARKS TABLE */
.table-wrap {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; overflow-x: auto;
}
table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
th, td {
  text-align: left; padding: 14px 18px;
  border-bottom: 1px solid var(--border); vertical-align: top;
}
th {
  font-family: var(--mono); font-size: 0.68rem; color: var(--accent);
  text-transform: uppercase; letter-spacing: 0.12em;
  background: rgba(255,255,255,0.015);
}
tr:last-child td { border-bottom: 0; }
tbody tr { transition: background 0.2s var(--ease-out); }
tbody tr:hover { background: rgba(201, 169, 110, 0.04); }

/* CLI & MCP MONOGRAPH SECTION */
.mcp-grid { display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 28px; align-items: start; }
.terminal-card {
  background: #0D0D10; border: 1px solid var(--border-hi);
  border-radius: 14px; overflow: hidden;
  box-shadow: 0 24px 60px rgba(0,0,0,0.5);
}
.term-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 18px; border-bottom: 1px solid var(--border);
  background: rgba(255,255,255,0.02);
}
.term-dots { display: flex; gap: 7px; }
.term-dots span { width: 9px; height: 9px; border-radius: 50%; background: rgba(214,198,168,0.22); }
.term-body {
  padding: 20px; font-family: var(--mono); font-size: 0.81rem;
  color: #E7E1D5; line-height: 1.75; overflow-x: auto;
}
.term-cmd { color: var(--accent-hi); }
.term-cmt { color: var(--dim); }
.mcp-tools-list {
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px;
}
.mcp-pill {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 11px 14px;
  font-family: var(--mono); font-size: 0.74rem; color: var(--text);
  display: flex; flex-direction: column; gap: 3px;
}
.mcp-pill span { font-family: var(--sans); font-size: 0.73rem; color: var(--muted); }

/* FOOTER */
.site-footer {
  position: relative; z-index: 1;
  padding: 44px 0 56px; color: var(--muted); font-size: 0.82rem;
}
.footer-inner {
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 18px;
}

/* MODAL & TOAST */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(5, 5, 7, 0.82);
  backdrop-filter: blur(10px);
  display: none; align-items: center; justify-content: center;
  padding: 20px; z-index: 100;
}
.modal-backdrop.open { display: flex; }
.modal-box {
  background: var(--surface); border: 1px solid var(--border-hi);
  border-radius: 16px; max-width: 860px; width: 100%;
  max-height: 88vh; overflow-y: auto; padding: 26px;
  box-shadow: 0 36px 90px rgba(0,0,0,0.75);
}
.modal-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px; gap: 12px;
}
.modal-head h3 { margin: 0; font-family: var(--serif); font-size: 1.45rem; font-weight: 500; }
.modal-pre {
  background: var(--bg); border: 1px solid var(--border); border-radius: 10px;
  padding: 15px; overflow-x: auto; font-size: 0.82rem; color: var(--accent-hi); margin: 0 0 16px;
}
.svg-preview {
  width: 100%; border-radius: 12px; overflow: hidden;
  border: 1px solid var(--border); margin-bottom: 16px;
}
.svg-preview svg { width: 100%; height: auto; display: block; }
.toast {
  position: fixed; right: 24px; bottom: 24px; z-index: 120;
  background: #171614; border: 1px solid var(--accent);
  color: var(--text); padding: 11px 18px; border-radius: 10px;
  font-size: 0.83rem; opacity: 0; transform: translateY(10px);
  pointer-events: none; transition: opacity 0.3s var(--ease-out), transform 0.3s var(--ease-out);
  box-shadow: 0 16px 40px rgba(0,0,0,0.55);
}
.toast.show { opacity: 1; transform: translateY(0); }

/* SCROLL REVEAL */
.reveal {
  opacity: 0; transform: translateY(20px);
  transition: opacity 0.75s var(--ease-out), transform 0.75s var(--ease-out);
}
.reveal.visible { opacity: 1; transform: translateY(0); }



/* LUXURY FORM CONTROLS: ZERO NATIVE WHITE SPINNERS, ZERO OS BLUE DROPDOWNS */
:focus-visible {
  outline: 1.5px solid var(--accent);
  outline-offset: 2px;
}
input[type="number"]::-webkit-outer-spin-button,
input[type="number"]::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type="number"] {
  -moz-appearance: textfield;
  appearance: textfield;
}
.field input:hover, .lux-select-trigger:hover {
  border-color: var(--border-hi);
}
.card { overflow: visible; }
.card details summary {
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.card details summary::-webkit-details-marker { display: none; }
.card details summary::after {
  content: "+";
  font-family: var(--mono);
  color: var(--accent);
  font-size: 1rem;
  transition: transform 0.25s var(--ease-out);
}
.card details[open] summary::after { transform: rotate(45deg); }

/* BESPOKE OBSIDIAN & CHAMPAGNE CUSTOM SELECT */
.lux-select-wrap {
  position: relative;
  width: 100%;
}
.lux-select-native {
  position: absolute !important;
  opacity: 0 !important;
  pointer-events: none !important;
  width: 1px !important;
  height: 1px !important;
  margin: 0 !important;
  padding: 0 !important;
}
.lux-select-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  background: var(--bg);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 9px 12px;
  font-size: 0.87rem;
  font-family: var(--mono);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.25s var(--ease-out), box-shadow 0.25s var(--ease-out), background 0.25s var(--ease-out);
}
.lux-select-wrap.open .lux-select-trigger {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(201, 169, 110, 0.14);
  background: #101013;
}
.lux-select-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.lux-select-arrow {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  color: var(--accent);
  transition: transform 0.28s var(--ease-out);
}
.lux-select-wrap.open .lux-select-arrow {
  transform: rotate(180deg);
}
.lux-select-menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 80;
  background: rgba(18, 18, 22, 0.98);
  backdrop-filter: blur(18px) saturate(140%);
  -webkit-backdrop-filter: blur(18px) saturate(140%);
  border: 1px solid var(--border-hi);
  border-radius: 10px;
  padding: 5px;
  box-shadow: 0 22px 54px rgba(0, 0, 0, 0.78), inset 0 1px 0 rgba(255, 245, 225, 0.06);
  opacity: 0;
  transform: translateY(-6px) scale(0.985);
  pointer-events: none;
  transition: opacity 0.2s var(--ease-out), transform 0.22s var(--ease-out);
  max-height: 240px;
  overflow-y: auto;
}
.lux-select-wrap.open .lux-select-menu {
  opacity: 1;
  transform: translateY(0) scale(1);
  pointer-events: auto;
}
.lux-select-opt {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  background: transparent;
  border: 0;
  border-radius: 7px;
  padding: 9px 11px;
  font-family: var(--mono);
  font-size: 0.83rem;
  color: var(--muted);
  text-align: left;
  cursor: pointer;
  transition: background 0.18s var(--ease-out), color 0.18s var(--ease-out);
}
.lux-select-opt:hover {
  background: rgba(201, 169, 110, 0.1);
  color: var(--text);
}
.lux-select-opt.selected {
  background: rgba(201, 169, 110, 0.16);
  color: var(--accent-hi);
  font-weight: 600;
}
.lux-select-check {
  font-size: 0.78rem;
  color: var(--accent-hi);
  opacity: 0;
}
.lux-select-opt.selected .lux-select-check {
  opacity: 1;
}

/* LUXURY INTERACTIVE FINANCIAL CHART ENGINE */
.lux-chart-root {
  position: relative;
  width: 100%;
  user-select: none;
  -webkit-user-select: none;
}
.lux-chart-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.lux-legend {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.lux-leg-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 4px 10px;
  font-family: var(--mono);
  font-size: 0.67rem;
  letter-spacing: 0.04em;
  color: var(--text);
  cursor: pointer;
  transition: opacity 0.25s var(--ease-out), border-color 0.25s var(--ease-out), background 0.25s var(--ease-out);
}
.lux-leg-btn:hover {
  border-color: var(--border-hi);
  background: rgba(201, 169, 110, 0.08);
}
.lux-leg-btn.dimmed {
  opacity: 0.35;
  text-decoration: line-through;
}
.lux-leg-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}
.lux-chart-hint {
  font-family: var(--mono);
  font-size: 0.65rem;
  letter-spacing: 0.08em;
  color: var(--dim);
  text-transform: uppercase;
}
.lux-svg-stage {
  position: relative;
  width: 100%;
  cursor: crosshair;
}
.lux-svg-stage svg {
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
}
.lux-series-group {
  transition: opacity 0.28s var(--ease-out);
}
.lux-series-group.hidden {
  opacity: 0.06;
}
.lux-hud {
  position: absolute;
  top: 10px;
  left: 12px;
  min-width: 196px;
  background: rgba(13, 13, 16, 0.92);
  backdrop-filter: blur(14px) saturate(150%);
  -webkit-backdrop-filter: blur(14px) saturate(150%);
  border: 1px solid rgba(214, 198, 168, 0.32);
  border-radius: 10px;
  padding: 10px 13px;
  pointer-events: none;
  opacity: 0;
  transform: translateY(4px) scale(0.98);
  transition: opacity 0.18s var(--ease-out), transform 0.18s var(--ease-out), left 0.12s ease-out;
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.72), inset 0 1px 0 rgba(255, 245, 225, 0.08);
  z-index: 15;
}
.lux-hud.show {
  opacity: 1;
  transform: translateY(0) scale(1);
}
.lux-hud-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 6px;
  margin-bottom: 6px;
  border-bottom: 1px solid rgba(214, 198, 168, 0.14);
  font-family: var(--mono);
  font-size: 0.67rem;
  letter-spacing: 0.08em;
  color: var(--accent-hi);
}
.lux-hud-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  font-size: 0.74rem;
  margin: 3px 0;
}
.lux-hud-row span:first-child {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--muted);
}
.lux-hud-row strong {
  font-family: var(--mono);
  font-weight: 600;
  color: var(--text);
}
@keyframes luxPulse {
  0%, 100% { r: 4.5; opacity: 0.55; }
  50% { r: 9; opacity: 0; }
}
.lux-beacon-ring {
  animation: luxPulse 2.4s cubic-bezier(0.16, 1, 0.3, 1) infinite;
}

@media (max-width: 1040px) {
  .hero-grid, .mcp-grid { grid-template-columns: 1fr; }
  .plates-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .inst-matrix { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .workspace { grid-template-columns: 1fr; }
  .ref-grid { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .container { padding: 0 18px; }
  .nav-links { display: none; }
  .hero-metrics { grid-template-columns: repeat(2, 1fr); }
  .plates-grid, .faq-grid, .mcp-tools-list { grid-template-columns: 1fr; }
  .inst-kpis { grid-template-columns: 1fr; }
}
@media (max-width: 480px) {
  .brand-ver { display: none; }
  .brand { font-size: 1.15rem; gap: 8px; }
}
"""

APP_JS = r"""

// =========================================================================
// 0. LUXURY INTERACTIVE FINANCIAL CHART ENGINE (BEZIER + CROSSHAIR + HUD)
// =========================================================================
const LUX_CHART_STATE = {};

function fmtCompactMoney(val, cur) {
  const sym = cur === 'USD' ? '$' : (cur === 'EUR' ? '€' : (cur === 'GBP' ? '£' : cur + ' '));
  const abs = Math.abs(val);
  const sign = val < 0 ? '-' : '';
  if (abs >= 1000000) return sign + sym + (abs / 1000000).toFixed(1) + 'M';
  if (abs >= 10000) return sign + sym + (abs / 1000).toFixed(1) + 'k';
  if (abs >= 1000) return sign + sym + (abs / 1000).toFixed(2).replace(/\.00$/, '') + 'k';
  return sign + sym + Math.round(abs).toLocaleString();
}

function fmtExactMoney(val, cur) {
  const sym = cur === 'USD' ? '$' : (cur === 'EUR' ? '€' : (cur === 'GBP' ? '£' : cur + ' '));
  const sign = val < 0 ? '-' : '';
  return sign + sym + Math.round(Math.abs(val)).toLocaleString();
}

function smoothPath(pts) {
  if (!pts.length) return '';
  if (pts.length === 1) return `M ${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
  let d = `M ${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(pts.length - 1, i + 2)];
    const cp1x = p1[0] + (p2[0] - p0[0]) / 6;
    const cp1y = p1[1] + (p2[1] - p0[1]) / 6;
    const cp2x = p2[0] - (p3[0] - p1[0]) / 6;
    const cp2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C ${cp1x.toFixed(1)},${cp1y.toFixed(1)} ${cp2x.toFixed(1)},${cp2y.toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
  }
  return d;
}

function areaBetween(topPts, botPts) {
  const topD = smoothPath(topPts);
  const revBot = [...botPts].reverse();
  const botD = smoothPath(revBot).replace(/^M/, 'L');
  return `${topD} ${botD} Z`;
}

function renderCashChart(containerId, consSeries, baseSeries, optSeries, currency, opts) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const compact = Boolean(opts && opts.compact);
  const cur = currency || 'USD';

  if (!LUX_CHART_STATE[containerId]) {
    LUX_CHART_STATE[containerId] = { opt: true, base: true, cons: true };
  }
  const vis = LUX_CHART_STATE[containerId];

  const n = Math.min(consSeries.length, baseSeries.length, optSeries.length);
  const allVals = [...consSeries, ...baseSeries, ...optSeries, 0];
  let mn = Math.min(...allVals);
  let mx = Math.max(...allVals);
  const rawSpan = Math.max(100, mx - mn);
  mn -= rawSpan * 0.08;
  mx += rawSpan * 0.12;
  const span = Math.max(1, mx - mn);

  const W = compact ? 520 : 680;
  const H = compact ? 182 : 244;
  const padL = compact ? 50 : 58;
  const padR = compact ? 56 : 68;
  const padT = 16;
  const padB = 28;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const xAt = i => padL + (i / Math.max(1, n - 1)) * plotW;
  const yAt = v => padT + plotH - ((v - mn) / span) * plotH;

  const optPts = optSeries.map((v, i) => [xAt(i), yAt(v)]);
  const basePts = baseSeries.map((v, i) => [xAt(i), yAt(v)]);
  const consPts = consSeries.map((v, i) => [xAt(i), yAt(v)]);

  const uid = containerId.replace(/[^a-zA-Z0-9]/g, '');

  // Clean Y-axis ticks (4 evenly spaced, skip if too close to zero line to prevent overlap)
  const zeroY = yAt(0);
  const showZero = zeroY >= padT - 2 && zeroY <= padT + plotH + 2;
  const tickCount = 4;
  let gridHtml = '';
  for (let t = 0; t < tickCount; t++) {
    const frac = t / (tickCount - 1);
    const val = mn + frac * span;
    const y = yAt(val);
    gridHtml += `<line x1="${padL}" y1="${y.toFixed(1)}" x2="${W - padR}" y2="${y.toFixed(1)}" stroke="rgba(214,198,168,0.075)" stroke-width="1"/>`;
    if (!showZero || Math.abs(y - zeroY) > 13) {
      gridHtml += `<text x="${padL - 8}" y="${(y + 3.5).toFixed(1)}" text-anchor="end" fill="#7D786F" font-family="JetBrains Mono, monospace" font-size="9.5">${fmtCompactMoney(val, cur)}</text>`;
    }
  }

  // Zero cash threshold & crimson insolvency hazard zone
  let zeroHtml = '';
  if (showZero) {
    const hazH = Math.max(0, (padT + plotH) - zeroY);
    if (hazH > 2) {
      zeroHtml += `<rect x="${padL}" y="${zeroY.toFixed(1)}" width="${plotW}" height="${hazH.toFixed(1)}" fill="url(#haz_${uid})"/>`;
    }
    zeroHtml += `<line x1="${padL}" y1="${zeroY.toFixed(1)}" x2="${W - padR}" y2="${zeroY.toFixed(1)}" stroke="rgba(196,92,92,0.68)" stroke-dasharray="3 4" stroke-width="1.15"/>`;
    zeroHtml += `<text x="${padL - 8}" y="${(zeroY + 3.5).toFixed(1)}" text-anchor="end" fill="#C45C5C" font-family="JetBrains Mono, monospace" font-size="9.5" font-weight="600">${fmtCompactMoney(0, cur)}</text>`;
    if (hazH > 16) {
      zeroHtml += `<text x="${W - padR - 6}" y="${(zeroY + 13).toFixed(1)}" text-anchor="end" fill="rgba(196,92,92,0.72)" font-family="JetBrains Mono, monospace" font-size="8" letter-spacing="1.2">INSOLVENCY ZONE</text>`;
    }
  }

  // X-axis month ticks
  let xTicksHtml = '';
  const monthMarks = [0, 3, 6, 9, 12].filter(m => m < n);
  monthMarks.forEach(m => {
    const x = xAt(m);
    xTicksHtml += `<line x1="${x.toFixed(1)}" y1="${padT + plotH}" x2="${x.toFixed(1)}" y2="${padT + plotH + 4}" stroke="rgba(214,198,168,0.22)" stroke-width="1"/>`;
    xTicksHtml += `<text x="${x.toFixed(1)}" y="${(H - 8).toFixed(1)}" text-anchor="middle" fill="#8D877D" font-family="JetBrains Mono, monospace" font-size="9.5">M${m}</text>`;
  });

  // Collision-avoided right-side M12 endpoint labels
  const lastIdx = n - 1;
  const endLabels = [
    { key: 'opt',  y: optPts[lastIdx][1],  val: optSeries[lastIdx],  col: '#58B58D', show: vis.opt },
    { key: 'base', y: basePts[lastIdx][1], val: baseSeries[lastIdx], col: '#E8CE9B', show: vis.base },
    { key: 'cons', y: consPts[lastIdx][1], val: consSeries[lastIdx], col: '#D46B6B', show: vis.cons }
  ].filter(item => item.show).sort((a, b) => a.y - b.y);
  for (let i = 1; i < endLabels.length; i++) {
    if (endLabels[i].y - endLabels[i - 1].y < 14) {
      endLabels[i].y = endLabels[i - 1].y + 14;
    }
  }
  const endLabelsHtml = endLabels.map(it =>
    `<text x="${(W - padR + 8).toFixed(1)}" y="${(it.y + 3.5).toFixed(1)}" fill="${it.col}" font-family="JetBrains Mono, monospace" font-size="9.5" font-weight="600">${fmtCompactMoney(it.val, cur)}</text>`
  ).join('');

  const svgHtml = `
  <div class="lux-chart-root" data-chart-id="${containerId}">
    <div class="lux-chart-toolbar">
      <div class="lux-legend">
        <button type="button" class="lux-leg-btn${vis.opt ? '' : ' dimmed'}" data-leg="opt"><span class="lux-leg-dot" style="background:#58B58D;"></span>P90 Opt</button>
        <button type="button" class="lux-leg-btn${vis.base ? '' : ' dimmed'}" data-leg="base"><span class="lux-leg-dot" style="background:#E8CE9B;"></span>Base</button>
        <button type="button" class="lux-leg-btn${vis.cons ? '' : ' dimmed'}" data-leg="cons"><span class="lux-leg-dot" style="background:#D46B6B;"></span>P10 Cons</button>
      </div>
      <div class="lux-chart-hint">HOVER TO INSPECT M0–M12</div>
    </div>
    <div class="lux-svg-stage">
      <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Interactive 12-month cash trajectory">
        <defs>
          <linearGradient id="fanTop_${uid}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#58B58D" stop-opacity="0.22"/>
            <stop offset="100%" stop-color="#C9A96E" stop-opacity="0.03"/>
          </linearGradient>
          <linearGradient id="fanBot_${uid}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#C9A96E" stop-opacity="0.14"/>
            <stop offset="100%" stop-color="#C45C5C" stop-opacity="0.04"/>
          </linearGradient>
          <pattern id="haz_${uid}" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="8" height="8" fill="rgba(196,92,92,0.055)"/>
            <line x1="0" y1="0" x2="0" y2="8" stroke="rgba(196,92,92,0.16)" stroke-width="1"/>
          </pattern>
          <filter id="glow_${uid}" x="-15%" y="-30%" width="130%" height="160%">
            <feGaussianBlur stdDeviation="2.6" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>

        ${gridHtml}
        ${zeroHtml}
        ${xTicksHtml}

        <!-- Confidence Fan Ribbons -->
        <path class="lux-series-group${(vis.opt && vis.base) ? '' : ' hidden'}" d="${areaBetween(optPts, basePts)}" fill="url(#fanTop_${uid})"/>
        <path class="lux-series-group${(vis.base && vis.cons) ? '' : ' hidden'}" d="${areaBetween(basePts, consPts)}" fill="url(#fanBot_${uid})"/>

        <!-- Smooth Cubic Bezier Curves -->
        <g class="lux-series-group${vis.opt ? '' : ' hidden'}">
          <path d="${smoothPath(optPts)}" fill="none" stroke="#58B58D" stroke-width="1.65" stroke-linecap="round"/>
          <circle cx="${optPts[lastIdx][0].toFixed(1)}" cy="${optPts[lastIdx][1].toFixed(1)}" r="3.2" fill="#58B58D" stroke="#0A0A0B" stroke-width="1.4"/>
        </g>
        <g class="lux-series-group${vis.cons ? '' : ' hidden'}">
          <path d="${smoothPath(consPts)}" fill="none" stroke="#D46B6B" stroke-width="1.55" stroke-dasharray="4 3.5" stroke-linecap="round"/>
          <circle cx="${consPts[lastIdx][0].toFixed(1)}" cy="${consPts[lastIdx][1].toFixed(1)}" r="3.2" fill="#D46B6B" stroke="#0A0A0B" stroke-width="1.4"/>
        </g>
        <g class="lux-series-group${vis.base ? '' : ' hidden'}">
          <path d="${smoothPath(basePts)}" fill="none" stroke="#E8CE9B" stroke-width="2.5" stroke-linecap="round" filter="url(#glow_${uid})"/>
          <circle class="lux-beacon-ring" cx="${basePts[lastIdx][0].toFixed(1)}" cy="${basePts[lastIdx][1].toFixed(1)}" r="5" fill="none" stroke="#E8CE9B" stroke-width="1.4"/>
          <circle cx="${basePts[lastIdx][0].toFixed(1)}" cy="${basePts[lastIdx][1].toFixed(1)}" r="3.8" fill="#E8CE9B" stroke="#0A0A0B" stroke-width="1.5"/>
        </g>

        ${endLabelsHtml}

        <!-- Interactive Crosshair & Magnetic Nodes -->
        <g class="lux-crosshair" style="opacity:0;transition:opacity 0.16s ease-out;">
          <line class="lux-ch-line" x1="${padL}" y1="${padT}" x2="${padL}" y2="${padT + plotH}" stroke="rgba(227,201,150,0.48)" stroke-dasharray="2.5 3" stroke-width="1"/>
          <circle class="lux-ch-opt"  cx="0" cy="0" r="4.5" fill="#58B58D" stroke="#0A0A0B" stroke-width="1.8"/>
          <circle class="lux-ch-base" cx="0" cy="0" r="5.2" fill="#E8CE9B" stroke="#0A0A0B" stroke-width="2"/>
          <circle class="lux-ch-cons" cx="0" cy="0" r="4.5" fill="#D46B6B" stroke="#0A0A0B" stroke-width="1.8"/>
        </g>
      </svg>
      <div class="lux-hud"></div>
    </div>
  </div>`;

  el.innerHTML = svgHtml;

  // Bind Legend Toggles
  el.querySelectorAll('.lux-leg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const k = btn.getAttribute('data-leg');
      vis[k] = !vis[k];
      if (!vis.opt && !vis.base && !vis.cons) vis[k] = true; // keep at least one visible
      renderCashChart(containerId, consSeries, baseSeries, optSeries, cur, opts);
    });
  });

  // Bind Interactive Hover / Touch Scrubbing
  const stage = el.querySelector('.lux-svg-stage');
  const svgEl = stage.querySelector('svg');
  const chGroup = svgEl.querySelector('.lux-crosshair');
  const chLine = svgEl.querySelector('.lux-ch-line');
  const chOpt = svgEl.querySelector('.lux-ch-opt');
  const chBase = svgEl.querySelector('.lux-ch-base');
  const chCons = svgEl.querySelector('.lux-ch-cons');
  const hud = stage.querySelector('.lux-hud');

  function scrubAtClientX(clientX) {
    const rect = svgEl.getBoundingClientRect();
    if (!rect.width) return;
    const svgX = ((clientX - rect.left) / rect.width) * W;
    const rawIdx = Math.round(((svgX - padL) / plotW) * (n - 1));
    const idx = Math.max(0, Math.min(n - 1, rawIdx));
    const x = xAt(idx);

    chGroup.style.opacity = '1';
    chLine.setAttribute('x1', x.toFixed(1));
    chLine.setAttribute('x2', x.toFixed(1));
    chOpt.setAttribute('cx', x.toFixed(1));  chOpt.setAttribute('cy', optPts[idx][1].toFixed(1));  chOpt.style.display = vis.opt ? '' : 'none';
    chBase.setAttribute('cx', x.toFixed(1)); chBase.setAttribute('cy', basePts[idx][1].toFixed(1)); chBase.style.display = vis.base ? '' : 'none';
    chCons.setAttribute('cx', x.toFixed(1)); chCons.setAttribute('cy', consPts[idx][1].toFixed(1)); chCons.style.display = vis.cons ? '' : 'none';

    const delta = idx > 0 ? (baseSeries[idx] - baseSeries[idx - 1]) : 0;
    const deltaStr = idx === 0 ? 'START' : ((delta >= 0 ? '+' : '') + fmtCompactMoney(delta, cur) + '/mo');
    const deltaCol = idx === 0 ? 'var(--muted)' : (delta >= 0 ? '#58B58D' : '#D46B6B');
    const solvent = consSeries[idx] >= 0;

    hud.innerHTML = `
      <div class="lux-hud-head">
        <span>MONTH ${String(idx).padStart(2, '0')}</span>
        <span style="color:${deltaCol};">${deltaStr}</span>
      </div>
      <div class="lux-hud-row"><span><i class="lux-leg-dot" style="background:#58B58D;"></i>P90 Opt</span><strong>${fmtExactMoney(optSeries[idx], cur)}</strong></div>
      <div class="lux-hud-row"><span><i class="lux-leg-dot" style="background:#E8CE9B;"></i>Base</span><strong style="color:var(--accent-hi);">${fmtExactMoney(baseSeries[idx], cur)}</strong></div>
      <div class="lux-hud-row"><span><i class="lux-leg-dot" style="background:#D46B6B;"></i>P10 Cons</span><strong style="color:${solvent ? 'var(--text)' : '#D46B6B'};">${fmtExactMoney(consSeries[idx], cur)}</strong></div>
    `;

    // Position HUD cleanly left or right of crosshair without clipping
    const pxX = ((x / W) * rect.width);
    const hudW = 204;
    const leftPos = (pxX + hudW + 20 > rect.width) ? Math.max(6, pxX - hudW - 14) : (pxX + 14);
    hud.style.left = leftPos.toFixed(0) + 'px';
    hud.classList.add('show');
  }

  stage.addEventListener('mousemove', e => scrubAtClientX(e.clientX));
  stage.addEventListener('touchmove', e => {
    if (e.touches && e.touches[0]) scrubAtClientX(e.touches[0].clientX);
  }, { passive: true });
  stage.addEventListener('mouseleave', () => {
    chGroup.style.opacity = '0';
    hud.classList.remove('show');
  });
}
window.renderCashChart = renderCashChart;

// =========================================================================
// 1. AMBIENT SILK MONTE CARLO CANVAS (HERO BACKGROUND, 60FPS GPU-LIGHT)
// =========================================================================
(function initHeroCanvas() {
  const canvas = document.getElementById('hero_canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let w = 0, h = 0, t = 0, mx = 0.5, my = 0.5;
  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const rect = canvas.parentElement.getBoundingClientRect();
    w = rect.width; h = rect.height;
    canvas.width = w * dpr; canvas.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  window.addEventListener('resize', resize);
  window.addEventListener('mousemove', e => {
    mx = e.clientX / Math.max(1, window.innerWidth);
    my = e.clientY / Math.max(1, window.innerHeight);
  }, { passive: true });

  const curves = [
    { amp: 26, freq: 0.0024, speed: 0.0045, yOff: 0.72, alpha: 0.16, col: '201,169,110', lw: 1.2 },
    { amp: 18, freq: 0.0031, speed: 0.0032, yOff: 0.62, alpha: 0.10, col: '227,201,150', lw: 0.9 },
    { amp: 32, freq: 0.0019, speed: 0.0025, yOff: 0.80, alpha: 0.09, col: '244,241,234', lw: 0.8 },
    { amp: 14, freq: 0.0038, speed: 0.0052, yOff: 0.52, alpha: 0.07, col: '201,169,110', lw: 0.7 }
  ];

  function draw() {
    ctx.clearRect(0, 0, w, h);
    t += 1;
    const parallaxY = (my - 0.5) * 18;
    for (const c of curves) {
      ctx.beginPath();
      for (let x = 0; x <= w; x += 14) {
        const trend = -0.14 * (x / Math.max(1, w)) * h;
        const y = h * c.yOff + trend + parallaxY +
          Math.sin(x * c.freq + t * c.speed + mx * 1.5) * c.amp +
          Math.cos(x * c.freq * 0.6 - t * c.speed * 0.7) * (c.amp * 0.45);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = `rgba(${c.col}, ${c.alpha})`;
      ctx.lineWidth = c.lw;
      ctx.stroke();
    }
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();

// =========================================================================
// 2. HEADER SCROLL ELEVATION & INTERSECTION REVEALS
// =========================================================================
window.addEventListener('scroll', () => {
  const hdr = document.getElementById('site_header');
  if (hdr) hdr.classList.toggle('scrolled', window.scrollY > 24);
}, { passive: true });

(function initReveals() {
  const els = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    els.forEach(el => el.classList.add('visible'));
    return;
  }
  const io = new IntersectionObserver(entries => {
    entries.forEach(en => {
      if (en.isIntersecting) {
        en.target.classList.add('visible');
        io.unobserve(en.target);
      }
    });
  }, { threshold: 0.08 });
  els.forEach(el => io.observe(el));
})();

// =========================================================================
// 3. LIVE HERO FALSIFICATION INSTRUMENT (INSTANT INTERACTIVE SHOWCASE)
// =========================================================================
const HERO_SCENARIOS = {
  saas: { type: 'saas', price: 49, varCost: 6, fixed: 900, cash: 12000, newC: 14, spend: 1800, churnPct: 5.5, refundPct: 2.0, cpc: 6.5, cvr: 2.5, processor: 'stripe_us_billing', taxPct: 21 },
  ai:   { type: 'saas', price: 29, varCost: 11, fixed: 1200, cash: 10000, newC: 22, spend: 2200, churnPct: 8.5, refundPct: 3.0, cpc: 5.2, cvr: 2.2, processor: 'stripe_us_billing', taxPct: 21 },
  ecom: { type: 'ecommerce', price: 68, varCost: 26, fixed: 2200, cash: 18000, newC: 95, spend: 2800, churnPct: 0, refundPct: 4.0, cpc: 2.4, cvr: 2.8, processor: 'stripe_us', taxPct: 21 }
};
let activeHeroKey = 'saas';

function renderHeroInstrument() {
  const base = HERO_SCENARIOS[activeHeroKey];
  const price = parseFloat(document.getElementById('h_price').value) || base.price;
  const cpc = parseFloat(document.getElementById('h_cpc').value) || base.cpc;
  const cash = parseFloat(document.getElementById('h_cash').value) || base.cash;

  document.getElementById('h_price_val').textContent = '$' + price.toFixed(0);
  document.getElementById('h_cpc_val').textContent = '$' + cpc.toFixed(2);
  document.getElementById('h_cash_val').textContent = '$' + Math.round(cash).toLocaleString();

  const cfg = {
    type: base.type, cur: 'USD', processor: base.processor, taxPct: base.taxPct, payrollPct: 0,
    price, varCost: base.varCost, fixed: base.fixed, cash,
    newC: base.newC, spend: base.spend, churnPct: base.churnPct, refundPct: base.refundPct
  };
  const mc = runMonteCarlo1000(cfg);
  const maxCac = solveMaxCac(cfg);
  const impCac = cpc / (base.cvr / 100);
  const cpcOk = maxCac > 0 && impCac <= maxCac;

  const survEl = document.getElementById('hi_surv');
  survEl.textContent = mc.survivalPct.toFixed(1) + '%';
  survEl.style.color = mc.survivalPct >= 85 ? 'var(--ok)' : (mc.survivalPct >= 50 ? 'var(--warn)' : 'var(--bad)');
  document.getElementById('hi_surv_sub').textContent = 'P10 Cash: $' + Math.round(mc.p10End).toLocaleString();

  document.getElementById('hi_cac').textContent = '$' + maxCac.toFixed(0);
  document.getElementById('hi_cac_sub').textContent = 'Implied Ads CAC: $' + impCac.toFixed(0);

  const vEl = document.getElementById('hi_channel');
  vEl.textContent = cpcOk ? 'VIABLE' : 'BLOCKED';
  vEl.style.color = cpcOk ? 'var(--ok)' : 'var(--bad)';
  document.getElementById('hi_channel_sub').textContent = base.cvr.toFixed(1) + '% CVR · $' + cpc.toFixed(2) + ' CPC';

  // Auto-Fix Prescription
  let rescuePrice = price;
  if (mc.survivalPct < 85) {
    for (let p = price + 2; p <= price * 4; p += 2) {
      if (runMonteCarlo1000({ ...cfg, price: p }).survivalPct >= 85) { rescuePrice = p; break; }
    }
  }
  const box = document.getElementById('hi_verdict');
  if (mc.survivalPct >= 85 && cpcOk) {
    box.className = 'inst-verdict ok';
    box.innerHTML = '<strong>Falsification Passed.</strong> 12-month survival exceeds 85% and paid search CPC clears your Max Viable CAC ceiling.';
  } else if (mc.survivalPct < 85) {
    box.className = 'inst-verdict bad';
    box.innerHTML = `<strong>Auto-Fix Prescription:</strong> Survival is ${mc.survivalPct.toFixed(1)}%. Raise price to <strong>$${rescuePrice.toFixed(0)}</strong> or shift 35% of customers to 20%-off annual prepay to restore ≥85% survival.`;
  } else {
    box.className = 'inst-verdict warn';
    box.innerHTML = `<strong>Channel Ceiling Breached:</strong> Unit math survives, but $${cpc.toFixed(2)} CPC ($${impCac.toFixed(0)} CAC) exceeds your $${maxCac.toFixed(0)} ceiling. Pivot to SEO, outbound, or Geo-Arbitrage.`;
  }

  // Render Luxury Interactive SVG Cash Telemetry Chart inside Hero Instrument
  const basePath = simPath(cfg).series;
  const consPath = simPath(cfg, { p: 0.9, nc: 0.65, v: 1.15, fx: 1.1, sp: 1.25, ch: 1.35 }).series;
  const optPath = simPath(cfg, { p: 1.1, nc: 1.3, v: 0.95, sp: 0.9, ch: 0.8 }).series;
  renderCashChart('hi_chart', consPath, basePath, optPath, 'USD', { compact: true });
}

document.querySelectorAll('.inst-preset-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.inst-preset-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeHeroKey = btn.getAttribute('data-hero-preset');
    const s = HERO_SCENARIOS[activeHeroKey];
    document.getElementById('h_price').value = s.price;
    document.getElementById('h_cpc').value = s.cpc;
    document.getElementById('h_cash').value = s.cash;
    renderHeroInstrument();

// =========================================================================
// 8. BESPOKE LUXURY CUSTOM SELECT ENHANCER (ZERO OS BLUE DROPDOWNS)
// =========================================================================
const LUX_SELECT_SYNCERS = [];

function upgradeLuxurySelects() {
  document.querySelectorAll('select').forEach(sel => {
    if (sel.dataset.luxUpgraded) return;
    sel.dataset.luxUpgraded = '1';

    const wrap = document.createElement('div');
    wrap.className = 'lux-select-wrap';
    sel.parentNode.insertBefore(wrap, sel);
    wrap.appendChild(sel);
    sel.classList.add('lux-select-native');
    sel.tabIndex = -1;

    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'lux-select-trigger';
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.innerHTML = `<span class="lux-select-label"></span><svg class="lux-select-arrow" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

    const menu = document.createElement('div');
    menu.className = 'lux-select-menu';
    menu.setAttribute('role', 'listbox');

    function syncVisual() {
      const activeOpt = sel.options[sel.selectedIndex] || sel.options[0];
      trigger.querySelector('.lux-select-label').textContent = activeOpt ? activeOpt.textContent : '';
      menu.querySelectorAll('.lux-select-opt').forEach(btn => {
        btn.classList.toggle('selected', btn.dataset.val === sel.value);
      });
    }

    Array.from(sel.options).forEach(opt => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'lux-select-opt';
      item.dataset.val = opt.value;
      item.setAttribute('role', 'option');
      item.innerHTML = `<span>${opt.textContent}</span><span class="lux-select-check">✓</span>`;
      item.addEventListener('click', () => {
        sel.value = opt.value;
        sel.dispatchEvent(new Event('change', { bubbles: true }));
        sel.dispatchEvent(new Event('input', { bubbles: true }));
        syncVisual();
        wrap.classList.remove('open');
        trigger.setAttribute('aria-expanded', 'false');
      });
      menu.appendChild(item);
    });

    trigger.addEventListener('click', e => {
      e.stopPropagation();
      const willOpen = !wrap.classList.contains('open');
      document.querySelectorAll('.lux-select-wrap.open').forEach(w => {
        w.classList.remove('open');
        w.querySelector('.lux-select-trigger')?.setAttribute('aria-expanded', 'false');
      });
      if (willOpen) {
        wrap.classList.add('open');
        trigger.setAttribute('aria-expanded', 'true');
      }
    });

    sel.addEventListener('change', syncVisual);
    LUX_SELECT_SYNCERS.push(syncVisual);

    wrap.appendChild(trigger);
    wrap.appendChild(menu);
    syncVisual();
  });

  document.addEventListener('click', () => {
    document.querySelectorAll('.lux-select-wrap.open').forEach(w => {
      w.classList.remove('open');
      w.querySelector('.lux-select-trigger')?.setAttribute('aria-expanded', 'false');
    });
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.lux-select-wrap.open').forEach(w => {
        w.classList.remove('open');
        w.querySelector('.lux-select-trigger')?.setAttribute('aria-expanded', 'false');
      });
    }
  });
}

function syncAllLuxurySelects() {
  LUX_SELECT_SYNCERS.forEach(fn => fn());
}
upgradeLuxurySelects();
// Keep custom selects synced whenever preset buttons or Hero Sync update native select values
document.querySelectorAll('[data-preset], #btn_sync_workbench').forEach(btn => {
  btn.addEventListener('click', () => setTimeout(syncAllLuxurySelects, 20));
});

  });
});
['h_price', 'h_cpc', 'h_cash'].forEach(id => {
  document.getElementById(id).addEventListener('input', renderHeroInstrument);
});
document.getElementById('btn_sync_workbench').addEventListener('click', () => {
  const s = HERO_SCENARIOS[activeHeroKey];
  document.getElementById('f_type').value = s.type;
  document.getElementById('f_cur').value = 'USD';
  document.getElementById('f_proc').value = s.processor;
  document.getElementById('f_tax').value = s.taxPct;
  document.getElementById('f_price').value = document.getElementById('h_price').value;
  document.getElementById('f_var').value = s.varCost;
  document.getElementById('f_fixed').value = s.fixed;
  document.getElementById('f_cash').value = document.getElementById('h_cash').value;
  document.getElementById('f_new').value = s.newC;
  document.getElementById('f_spend').value = s.spend;
  document.getElementById('f_churn').value = s.churnPct;
  document.getElementById('f_refund').value = s.refundPct;
  document.getElementById('f_cpc').value = document.getElementById('h_cpc').value;
  document.getElementById('f_cvr').value = s.cvr;
  document.getElementById('f_price').dispatchEvent(new Event('input', { bubbles: true }));
  switchTab('frontier');
  document.getElementById('workbench').scrollIntoView({ behavior: 'smooth' });
  showToast('Scenario synced to full workbench');
});

// =========================================================================
// 4. WORKBENCH 5x2 INSTRUMENT MATRIX SWITCHER
// =========================================================================
function switchTab(key) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.inst-tile').forEach(b => b.classList.remove('active'));
  const target = document.getElementById('panel-' + key);
  if (target) target.classList.add('active');
  const btn = document.querySelector(`.inst-tile[data-switch="${key}"]`);
  if (btn) {
    btn.classList.add('active');
    const num = btn.getAttribute('data-num') || '01';
    const label = btn.getAttribute('data-' + currentLang) || btn.getAttribute('data-en');
    const pill = document.getElementById('wb_active_pill');
    const nameEl = document.getElementById('wb_active_name');
    if (pill) pill.textContent = (currentLang === 'zh' ? '当前仪器 ' : 'ACTIVE ') + num + ' / 10';
    if (nameEl) nameEl.textContent = label;
  }
}

document.querySelectorAll('[data-switch]').forEach(el => {
  el.addEventListener('click', () => {
    const key = el.getAttribute('data-switch');
    switchTab(key);
    if (el.classList.contains('plate')) {
      document.getElementById('workbench').scrollIntoView({ behavior: 'smooth' });
    }
  });
});

// =========================================================================
// 5. BILINGUAL EN / 中文 TOGGLE
// =========================================================================
let currentLang = 'en';
const I18N = {
  en: {
    kicker: 'EDITION 08.1 · DETERMINISTIC FINANCE · MIT OPEN-SOURCE',
    h1: 'Falsify the math <em>before</em> you write the code.',
    lead: 'An architectural stress-testing instrument for founders. Run 1,000-path Monte Carlo survival simulations, reverse-solve your Max Viable CAC, inspect Auto-Fix pricing prescriptions, or connect 12 deterministic MCP tools directly to your coding agent.',
    cta1: 'Open 10-Tool Workbench',
    cta2: 'CLI & MCP Engine',
    langBtn: '中文',
    wbKicker: 'INTERACTIVE INSTRUMENT SUITE',
    wbTitle: 'Ten deterministic calculators. Zero black boxes.',
    wbLead: 'Every input recalculates instantaneously in your browser. Expand Methodology & FAQ beneath any instrument to inspect exact formulas and worked examples.'
  },
  zh: {
    kicker: 'EDITION 08.1 · 确定性商业财务数学 · MIT 开源协议',
    h1: '写第一行代码<em>之前</em>，先用硬数学证伪商业假设。',
    lead: '专为独立开发者与创始人打造的精密商业压测仪。内置 1,000 次蒙特卡洛生存仿真、反向求解最高可承受获客成本（Max Viable CAC）、Auto-Fix 自动救命处方，以及 12 个可直接接入 AI 编程助手的 MCP 确定性工具。',
    cta1: '进入 10 合 1 压测工作台',
    cta2: '查看 CLI 与 MCP 引擎',
    langBtn: 'EN',
    wbKicker: '交互式商业压测工作台',
    wbTitle: '十大确定性计算器，拒绝黑盒估算。',
    wbLead: '所有参数均在浏览器端实时演算；展开任意工具下方的「方法论与 FAQ」即可核对精确公式、完整算例与高频问答。'
  }
};

document.getElementById('lang_toggle_btn').addEventListener('click', () => {
  currentLang = currentLang === 'en' ? 'zh' : 'en';
  const t = I18N[currentLang];
  document.getElementById('hero_kicker_text').textContent = t.kicker;
  document.getElementById('hero_h1').innerHTML = t.h1;
  document.getElementById('hero_lead').textContent = t.lead;
  document.getElementById('hero_cta_1').textContent = t.cta1;
  document.getElementById('hero_cta_2').textContent = t.cta2;
  document.getElementById('lang_toggle_btn').textContent = t.langBtn;
  document.getElementById('wb_kicker').textContent = t.wbKicker;
  document.getElementById('wb_title').textContent = t.wbTitle;
  document.getElementById('wb_lead').textContent = t.wbLead;
  document.querySelectorAll('.inst-tile').forEach(btn => {
    const nameEl = btn.querySelector('.it-name');
    const subEl = btn.querySelector('.it-sub');
    if (nameEl) nameEl.textContent = btn.getAttribute('data-' + currentLang);
    if (subEl) subEl.textContent = btn.getAttribute('data-sub-' + currentLang);
  });
  const activeTile = document.querySelector('.inst-tile.active');
  if (activeTile) switchTab(activeTile.getAttribute('data-switch'));
});

// =========================================================================
// 6. COPY HELPER (WITH SANDBOX-SAFE FALLBACK) & MODALS
// =========================================================================
function copyTextSafe(text, okMsg) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(
      () => showToast(okMsg || 'Copied to clipboard'),
      () => fallbackCopy(text, okMsg)
    );
  } else {
    fallbackCopy(text, okMsg);
  }
}
function fallbackCopy(text, okMsg) {
  try {
    const ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    document.execCommand('copy');
    ta.remove();
    showToast(okMsg || 'Copied to clipboard');
  } catch (e) {
    showToast('Select and copy from the box above.');
  }
}

document.getElementById('btn_copy_cli').addEventListener('click', () => {
  copyTextSafe('pip install ideastress && ideastress mcp', 'CLI command copied');
});

function openModal(title, bodyHtml, downloadName, downloadContent, downloadMime) {
  document.getElementById('modal_title').textContent = title;
  document.getElementById('modal_body').innerHTML = bodyHtml;
  document.getElementById('modal_dl_btn').onclick = () => {
    try {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([downloadContent], { type: downloadMime }));
      a.download = downloadName; document.body.appendChild(a); a.click(); a.remove();
      showToast('Downloaded ' + downloadName);
    } catch (e) { showToast('Use Copy button instead.'); }
  };
  document.getElementById('modal_copy_btn').onclick = () => copyTextSafe(downloadContent, 'Copied to clipboard');
  document.getElementById('app_modal').classList.add('open');
}
document.getElementById('modal_close_btn').addEventListener('click', () => document.getElementById('app_modal').classList.remove('open'));
document.getElementById('app_modal').addEventListener('click', e => {
  if (e.target.id === 'app_modal') e.target.classList.remove('open');
});

// =========================================================================
// 7. RESTORE URL HASH & INITIALIZE ALL 10 DETERMINISTIC CALCULATORS
// =========================================================================
(function restoreFromHash() {
  try {
    if (!location.hash.startsWith('#s=')) return;
    const obj = JSON.parse(atob(decodeURIComponent(location.hash.slice(3))));
    Object.entries(obj).forEach(([id, val]) => {
      const el = document.getElementById(id);
      if (el) el.value = val;
    });
    showToast('Loaded shared scenario from URL');
  } catch (e) {}
})();

window.initFrontierTool();
window.initQuitJobTool();
window.initFreemiumTool();
window.initSocialCpmTool();
window.initAiMarginTool();
window.initGeoTool();
window.initBreakEvenTool();
window.initSaasTool();
window.initEcomTool();
window.initRunwayTool();

renderHeroInstrument();


function readFrontierCfg() {
  return {
    type: document.getElementById('f_type').value,
    cur: document.getElementById('f_cur').value,
    processor: document.getElementById('f_proc').value,
    taxPct: parseFloat(document.getElementById('f_tax').value) || 0,
    payrollPct: 0,
    price: parseFloat(document.getElementById('f_price').value) || 0,
    varCost: parseFloat(document.getElementById('f_var').value) || 0,
    fixed: parseFloat(document.getElementById('f_fixed').value) || 0,
    cash: parseFloat(document.getElementById('f_cash').value) || 0,
    newC: parseInt(document.getElementById('f_new').value, 10) || 0,
    spend: parseFloat(document.getElementById('f_spend').value) || 0,
    churnPct: parseFloat(document.getElementById('f_churn').value) || 0,
    refundPct: parseFloat(document.getElementById('f_refund').value) || 0
  };
}

document.getElementById('btn_export_yaml').onclick = () => {
  const c = readFrontierCfg();
  const y = `idea: "My ${c.type} business idea"\ntarget_market:\n  - "United States"\nbusiness_type: ${c.type}\nbudget: "${c.cash}"\ncurrency: ${c.cur}\ntimeline_months: 12\nfinancials:\n  business_type: ${c.type}\n  currency: ${c.cur}\n  unit_price: "${c.price}"\n  variable_cost_per_unit: "${c.varCost}"\n  fixed_monthly_costs: "${c.fixed}"\n  monthly_new_customers: ${c.newC}\n  monthly_acquisition_spend: "${c.spend}"\n  monthly_churn_rate: "${(c.churnPct / 100).toFixed(4)}"\n  refund_rate: "${(c.refundPct / 100).toFixed(4)}"\n  payment_processor: "${c.processor}"\n  effective_tax_rate: "${(c.taxPct / 100).toFixed(4)}"\n  starting_cash: "${c.cash}"\n  horizon_months: 12\n`;
  openModal('Exported venture.yaml (IdeaStress CLI & MCP)', `<pre class="modal-pre mono">${y.replace(/</g,'&lt;')}</pre>`, 'venture.yaml', y, 'text/yaml');
};

document.getElementById('btn_proof_card').onclick = () => {
  const c = readFrontierCfg();
  const mc = runMonteCarlo1000(c);
  const maxCac = solveMaxCac(c);
  const cpc = parseFloat(document.getElementById('f_cpc')?.value) || 0;
  const cvr = Math.max(0.001, (parseFloat(document.getElementById('f_cvr')?.value) || 2.5) / 100);
  const impCac = cpc / cvr;
  const cpcOk = maxCac > 0 && impCac <= maxCac;
  const col = mc.survivalPct >= 85 ? '#4E9F7C' : (mc.survivalPct >= 50 ? '#C89248' : '#C45C5C');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <rect width="1200" height="630" fill="#0A0A0B"/><rect x="44" y="44" width="1112" height="542" rx="20" fill="#121215" stroke="#3B3429" stroke-width="1.5"/>
  <text x="86" y="106" fill="#C9A96E" font-family="Georgia, serif" font-size="24" letter-spacing="4">IDEASTRESS  //  FALSIFICATION PROOF CARD</text>
  <rect x="880" y="72" width="236" height="46" rx="23" fill="${col}" fill-opacity="0.14" stroke="${col}" stroke-width="1.5"/>
  <text x="998" y="102" text-anchor="middle" fill="${col}" font-family="monospace" font-size="19" font-weight="700">${mc.risk}</text>
  <text x="86" y="188" fill="#F4F1EA" font-family="Georgia, serif" font-size="38">${c.type.toUpperCase()} · ${c.cur} ${c.price} Price · ${c.cur} ${c.cash.toLocaleString()} Cash</text>
  <rect x="86" y="245" width="320" height="200" rx="14" fill="#18181C" stroke="#2D2922"/>
  <text x="114" y="290" fill="#9A948A" font-family="monospace" font-size="14">12M SURVIVAL (1,000 RUNS)</text>
  <text x="114" y="365" fill="${col}" font-family="monospace" font-size="52" font-weight="700">${mc.survivalPct.toFixed(1)}%</text>
  <text x="114" y="415" fill="#D5CFC3" font-family="sans-serif" font-size="16">P10 Cash: ${c.cur} ${Math.round(mc.p10End).toLocaleString()}</text>
  <rect x="440" y="245" width="320" height="200" rx="14" fill="#18181C" stroke="#2D2922"/>
  <text x="468" y="290" fill="#9A948A" font-family="monospace" font-size="14">MAX VIABLE CAC CEILING</text>
  <text x="468" y="365" fill="#E3C996" font-family="monospace" font-size="44" font-weight="700">${c.cur} ${maxCac.toFixed(2)}</text>
  <text x="468" y="415" fill="#D5CFC3" font-family="sans-serif" font-size="16">Monthly Spend: ${c.cur} ${c.spend}</text>
  <rect x="794" y="245" width="320" height="200" rx="14" fill="#18181C" stroke="#2D2922"/>
  <text x="822" y="290" fill="#9A948A" font-family="monospace" font-size="14">GOOGLE ADS CPC CHECK</text>
  <text x="822" y="355" fill="${cpcOk ? '#4E9F7C' : '#C45C5C'}" font-family="monospace" font-size="25" font-weight="700">${cpcOk ? 'CHANNEL_VIABLE' : 'CHANNEL_IMPOSSIBLE'}</text>
  <text x="822" y="415" fill="#D5CFC3" font-family="sans-serif" font-size="16">Implied CAC: ${c.cur} ${impCac.toFixed(2)}</text>
  <line x1="86" y1="496" x2="1114" y2="496" stroke="#2D2922" stroke-width="1"/>
  <text x="86" y="544" fill="#9A948A" font-family="monospace" font-size="16">Stress-tested with IdeaStress (MIT Open-Source) · pip install ideastress</text>
  <text x="1114" y="544" text-anchor="end" fill="#C9A96E" font-family="monospace" font-size="16">waterdolphinkiller.github.io/ideastress</text></svg>`;
  openModal('Shareable 1200×630 Proof Card (SVG)', `<div class="svg-preview">${svg}</div>`, 'ideastress_proof_card.svg', svg, 'image/svg+xml');
};

document.getElementById('btn_export_csv').addEventListener('click', () => {
  const c = readFrontierCfg();
  const base = simPath(c);
  const cons = simPath(c, { p: 0.9, nc: 0.65, v: 1.15, fx: 1.1, sp: 1.25, ch: 1.35 });
  const opt = simPath(c, { p: 1.1, nc: 1.3, v: 0.95, sp: 0.9, ch: 0.8 });
  const lines = ['Month,Currency,Conservative_Cash,Base_Cash,Optimistic_Cash'];
  for (let m = 0; m <= 12; m++) {
    lines.push(`${m},${c.cur},${cons.series[m].toFixed(2)},${base.series[m].toFixed(2)},${opt.series[m].toFixed(2)}`);
  }
  const csv = lines.join('\n') + '\n';
  openModal('12-Month Cash Trajectory (CSV)', `<pre class="modal-pre mono">${csv}</pre>`, 'ideastress_12m_cashflow.csv', csv, 'text/csv');
});

document.getElementById('btn_share_url').addEventListener('click', () => {
  const ids = ['f_type','f_cur','f_proc','f_tax','f_price','f_var','f_fixed','f_cash','f_new','f_spend','f_churn','f_refund','f_cpc','f_cvr'];
  const state = {};
  ids.forEach(id => { const el = document.getElementById(id); if (el) state[id] = el.value; });
  const hash = '#s=' + encodeURIComponent(btoa(JSON.stringify(state)));
  const shareUrl = 'https://waterdolphinkiller.github.io/ideastress/' + hash;
  try { history.replaceState(null, '', hash); } catch (e) {}
  openModal('Shareable Scenario Link', `<pre class="modal-pre mono">${shareUrl}</pre><p style="font-size:0.84rem;color:var(--muted);margin:0 0 14px;">Share this URL with your co-founder — opening it restores all 14 parameters instantaneously.</p>`, 'share_url.txt', shareUrl, 'text/plain');
});
"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>IdeaStress — Deterministic Business Falsification &amp; Financial Stress-Test Suite</title>
  <meta name="description" content="Stress-test your startup idea with 1,000-run Monte Carlo survival math, Auto-Fix pricing prescriptions, 10 deterministic calculators, and a 12-tool MCP engine." />
  <link rel="canonical" href="https://waterdolphinkiller.github.io/ideastress/" />
  <link rel="alternate" type="text/plain" href="https://waterdolphinkiller.github.io/ideastress/llms.txt" title="IdeaStress LLMs.txt AI Index" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="IdeaStress" />
  <meta property="og:title" content="IdeaStress — Deterministic Business Falsification & Financial Stress-Test Suite" />
  <meta property="og:description" content="Run 1,000-path Monte Carlo survival simulations, reverse-solve Max Viable CAC, inspect Auto-Fix prescriptions, and connect 12 MCP tools." />
  <meta property="og:url" content="https://waterdolphinkiller.github.io/ideastress/" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="IdeaStress — Falsify the math before you write the code." />
  <meta name="twitter:description" content="10 live startup financial calculators, 1,000-run Monte Carlo, Auto-Fix rescue solver, and 12-tool MIT open-source MCP engine." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <script type="application/ld+json">{ld_json}</script>
  <style>{LUXURY_CSS}</style>
</head>
<body>
  <div class="arch-grid-bg" aria-hidden="true"></div>

  <header class="site-header" id="site_header">
    <div class="container nav-inner">
      <button type="button" class="brand" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">
        <svg class="brand-mark" viewBox="0 0 28 28" fill="none" aria-hidden="true">
          <rect x="2" y="2" width="24" height="24" rx="4" stroke="#C9A96E" stroke-width="1.2"/>
          <path d="M7 20 C11 19, 13 11, 21 8" stroke="#E3C996" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="7" y1="15" x2="21" y2="15" stroke="rgba(201,169,110,0.45)" stroke-dasharray="2 2.5" stroke-width="1"/>
          <circle cx="21" cy="8" r="2" fill="#E3C996"/>
        </svg>
        <span>IDEASTRESS</span>
        <span class="brand-ver">v0.8.1</span>
      </button>

      <nav class="nav-links" aria-label="Primary Navigation">
        <a href="#capabilities">Capabilities</a>
        <a href="#workbench">Workbench</a>
        <a href="#benchmarks">Benchmarks</a>
        <a href="#mcp">CLI &amp; MCP</a>
      </nav>

      <div class="nav-actions">
        <button type="button" class="btn btn-ghost" id="lang_toggle_btn" style="padding:7px 12px;">中文</button>
        <a href="#workbench" class="btn primary">Stress-Test →</a>
      </div>
    </div>
  </header>

  <main id="main_content">
  <section class="hero-wrap" id="hero">
    <canvas id="hero_canvas" aria-hidden="true"></canvas>
    <div class="container hero-grid">
      <div>
        <div class="edition-kicker">
          <span class="hairline"></span>
          <span id="hero_kicker_text">EDITION 08.1 · DETERMINISTIC FINANCE · MIT OPEN-SOURCE</span>
        </div>
        <h1 class="hero-title" id="hero_h1">Falsify the math <em>before</em> you write the code.</h1>
        <p class="hero-lead" id="hero_lead">
          An architectural stress-testing instrument for founders. Run 1,000-path Monte Carlo survival simulations, reverse-solve your Max Viable CAC, inspect Auto-Fix pricing prescriptions, or connect 12 deterministic MCP tools directly to your coding agent.
        </p>
        <div class="hero-ctas">
          <a href="#workbench" class="btn primary" id="hero_cta_1">Open 10-Tool Workbench</a>
          <a href="#mcp" class="btn" id="hero_cta_2">CLI &amp; MCP Engine</a>
        </div>
        <div class="hero-metrics">
          <div class="hm-item"><div class="hm-val">10</div><div class="hm-lbl">Live Calculators</div></div>
          <div class="hm-item"><div class="hm-val">1,000×</div><div class="hm-lbl">Monte Carlo Paths</div></div>
          <div class="hm-item"><div class="hm-val">12</div><div class="hm-lbl">MCP Agent Tools</div></div>
          <div class="hm-item"><div class="hm-val">0</div><div class="hm-lbl">LLM Math Guesses</div></div>
        </div>
      </div>

      <!-- LIVE EXECUTIVE FALSIFICATION INSTRUMENT -->
      <div class="instrument-frame">
        <div class="instrument-head">
          <div class="inst-tag"><span class="inst-dot"></span>LIVE FALSIFICATION DESK</div>
          <div class="inst-presets">
            <button type="button" class="inst-preset-btn active" data-hero-preset="saas">B2B SaaS</button>
            <button type="button" class="inst-preset-btn" data-hero-preset="ai">AI Wrapper</button>
            <button type="button" class="inst-preset-btn" data-hero-preset="ecom">DTC E-Com</button>
          </div>
        </div>

        <div class="inst-kpis">
          <div class="inst-kpi">
            <div class="ik-l">12M Survival</div>
            <div class="ik-v" id="hi_surv">—</div>
            <div class="ik-s" id="hi_surv_sub">P10 Cash: —</div>
          </div>
          <div class="inst-kpi">
            <div class="ik-l">Max Viable CAC</div>
            <div class="ik-v" id="hi_cac" style="color:var(--accent-hi);">—</div>
            <div class="ik-s" id="hi_cac_sub">Implied Ads CAC: —</div>
          </div>
          <div class="inst-kpi">
            <div class="ik-l">Paid Channel</div>
            <div class="ik-v" id="hi_channel">—</div>
            <div class="ik-s" id="hi_channel_sub">—</div>
          </div>
        </div>

        <div class="inst-chart-box">
          <div class="inst-chart-head">
            <span>12M CASH TRAJECTORY (P10 · BASE · P90)</span>
            <span style="color:var(--accent-hi);">SEEDED DETERMINISTIC</span>
          </div>
          <div id="hi_chart"></div>
        </div>

        <div class="inst-sliders">
          <div class="slider-row">
            <label><span>Unit Price / Monthly ARPA</span><strong id="h_price_val">$49</strong></label>
            <input type="range" class="gold-range" id="h_price" min="15" max="240" step="1" value="49" />
          </div>
          <div class="slider-row">
            <label><span>Google Ads CPC (Paid Search Reality)</span><strong id="h_cpc_val">$6.50</strong></label>
            <input type="range" class="gold-range" id="h_cpc" min="0.8" max="15" step="0.1" value="6.5" />
          </div>
          <div class="slider-row">
            <label><span>Starting Cash Runway</span><strong id="h_cash_val">$12,000</strong></label>
            <input type="range" class="gold-range" id="h_cash" min="3000" max="60000" step="1000" value="12000" />
          </div>
        </div>

        <div class="inst-verdict" id="hi_verdict">Evaluating survival frontier…</div>

        <button type="button" class="btn" id="btn_sync_workbench" style="width:100%;">
          Sync Parameters to Full 10-Tool Workbench ↓
        </button>
      </div>
    </div>
  </section>

  <!-- 01 · CAPABILITIES ARCHITECTURE -->
  <section class="editorial-section" id="capabilities">
    <div class="container">
      <div class="sec-head reveal">
        <div>
          <div class="sec-kicker">ARCHITECTURAL PILLARS</div>
          <h2 class="sec-title">Four engines built to kill bad assumptions early.</h2>
        </div>
        <p class="sec-lead">Click any discipline below to open its live interactive instrument directly inside the workbench.</p>
      </div>

      <div class="plates-grid reveal">
        <button type="button" class="plate" data-switch="frontier">
          <div>
            <div class="plate-num">01</div>
            <h3>Reverse Frontier &amp; Monte Carlo</h3>
            <p>Work backward from your real bank balance to solve exact Max Viable CAC, with 1,000 seeded volatility paths and early SaaS churn spikes.</p>
          </div>
          <span class="plate-link">Open Frontier Solver →</span>
        </button>

        <button type="button" class="plate" data-switch="ai_margin">
          <div>
            <div class="plate-num">02</div>
            <h3>AI Token &amp; Whale Bankruptcy</h3>
            <p>Model real LLM inference COGS across fast, balanced, and frontier reasoning tiers—and pinpoint the exact daily prompt limit where power users bankrupt flat plans.</p>
          </div>
          <span class="plate-link">Open AI Margin Tool →</span>
        </button>

        <button type="button" class="plate" data-switch="geo">
          <div>
            <div class="plate-num">03</div>
            <h3>5-Country Geo-Arbitrage CPC</h3>
            <p>When US paid search is mathematically impossible, compare localized CPC and CAC headroom across the US, UK, Germany, Singapore, and Malaysia.</p>
          </div>
          <span class="plate-link">Open Geo Scanner →</span>
        </button>

        <button type="button" class="plate" data-switch="quit_job">
          <div>
            <div class="plate-num">04</div>
            <h3>Founder Reality Matrix</h3>
            <p>Calculate exact Quit-Your-Job MRR (Stripe vs MoR + taxes), Freemium free-tier drag, Meta/TikTok CPM funnels, and shock-tested cash runway.</p>
          </div>
          <span class="plate-link">Open Quit-Job MRR →</span>
        </button>
      </div>
    </div>
  </section>

  <!-- 02 · INTERACTIVE 10-CALCULATOR WORKBENCH -->
  <section class="editorial-section" id="workbench">
    <div class="container">
      <div class="sec-head reveal">
        <div>
          <div class="sec-kicker" id="wb_kicker">INTERACTIVE INSTRUMENT SUITE</div>
          <h2 class="sec-title" id="wb_title">Ten deterministic calculators. Zero black boxes.</h2>
        </div>
        <p class="sec-lead" id="wb_lead">Every input recalculates instantaneously in your browser. Expand Methodology &amp; FAQ beneath any instrument to inspect exact formulas and worked examples.</p>
      </div>

      <div class="matrix-bar-head">
        <div class="matrix-counter">
          <span class="mc-pill" id="wb_active_pill">ACTIVE 01 / 10</span>
          <span id="wb_active_name">Reverse Frontier</span>
        </div>
        <div style="font-family:var(--mono);font-size:0.68rem;letter-spacing:0.08em;color:var(--dim);text-transform:uppercase;">ALL 10 INSTRUMENTS VISIBLE · SELECT TO SWITCH</div>
      </div>
      <div class="inst-matrix" role="tablist" aria-label="10 Deterministic Calculators">
        {tab_buttons}
      </div>

      {"".join(panels_html)}
    </div>
  </section>

  <!-- 03 · 2025–2026 VERIFIED BENCHMARKS -->
  <section class="editorial-section" id="benchmarks">
    <div class="container">
      <div class="sec-head reveal">
        <div>
          <div class="sec-kicker">EMPIRICAL BASE RATES</div>
          <h2 class="sec-title">2025–2026 Industry Benchmarks</h2>
        </div>
        <p class="sec-lead">Every default assumption and red-flag threshold in IdeaStress is anchored to published empirical datasets rather than optimistic pitch-deck lore.</p>
      </div>

      <div class="table-wrap reveal">
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Published Benchmark</th>
              <th>Falsification Implication</th>
              <th>Primary Source</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>SaaS Monthly Churn</strong></td>
              <td class="mono">6.2% (ARPA &lt;$25) · 2.6% (&gt;$1K)</td>
              <td>Low-ticket SaaS loses half its cohort in ~11 months unless retention is engineered first.</td>
              <td><a href="https://chartmogul.com/benchmarks/" target="_blank" rel="noopener">ChartMogul (Nov 2026)</a></td>
            </tr>
            <tr>
              <td><strong>Private SaaS Economics</strong></td>
              <td class="mono">80% GM · 16m Payback · 4.1× LTV:CAC</td>
              <td>AI wrappers with 45%–65% gross margin need sharply lower CAC than traditional SaaS.</td>
              <td><a href="https://www.subscriptionplaybook.com/benchmarks/" target="_blank" rel="noopener">SubscriptionPlaybook (2026)</a></td>
            </tr>
            <tr>
              <td><strong>Indie SaaS Median MRR</strong></td>
              <td class="mono">$145 median · 23.6% &gt;$1K MRR</td>
              <td>Only 6.1% surpass $10K MRR—validate paid demand before quitting full-time income.</td>
              <td><a href="https://bigideasdb.com/dimeadozen-alternative" target="_blank" rel="noopener">TrustMRR / BigIdeasDB (2026)</a></td>
            </tr>
            <tr>
              <td><strong>US Payment Processing</strong></td>
              <td class="mono">Stripe 2.9%+$0.30 · MoR 5%+$0.50</td>
              <td>Fees compound on low-ticket items; Stripe Billing adds 0.7% on recurring invoices.</td>
              <td><a href="https://stripe.com/pricing" target="_blank" rel="noopener">Stripe US Pricing (2026)</a></td>
            </tr>
            <tr>
              <td><strong>Shopify Store CVR</strong></td>
              <td class="mono">1.4% median · 2.7% top 20%</td>
              <td>Assuming 4%–5% cold-traffic conversion masks fatal paid-ad economics.</td>
              <td><a href="https://eulav.io/insights/average-ecommerce-conversion-rate/" target="_blank" rel="noopener">Littledata / Eulav (Nov 2026)</a></td>
            </tr>
            <tr>
              <td><strong>Blended E-Com CAC</strong></td>
              <td class="mono">$53 – $91 across 13 verticals</td>
              <td>Stores under $40 AOV cannot profitably acquire cold paid traffic on order #1.</td>
              <td><a href="https://agencyai.app/blog/shopify-ad-benchmarks-2026" target="_blank" rel="noopener">First Page Sage (2026)</a></td>
            </tr>
            <tr>
              <td><strong>US Sector Net Margin</strong></td>
              <td class="mono">9.74% avg · 3%–9% restaurants</td>
              <td>High-overhead local businesses leave minimal buffer for rent or labor shocks.</td>
              <td><a href="https://christopholivierconsulting.com/profit-margin-by-industry/" target="_blank" rel="noopener">NYU Stern / VantaInsights</a></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- 04 · BUSINESS-AS-CODE CLI & MCP ENGINE -->
  <section class="editorial-section" id="mcp">
    <div class="container">
      <div class="sec-head reveal">
        <div>
          <div class="sec-kicker">BUSINESS-AS-CODE ENGINE</div>
          <h2 class="sec-title">Run the exact same math inside your IDE &amp; AI agents.</h2>
        </div>
        <p class="sec-lead">Version-control your assumptions in <code class="mono">venture.yaml</code>, scan repositories for uncapped LLM token loops, and expose 12 deterministic tools over stdio JSON-RPC 2.0 MCP.</p>
      </div>

      <div class="mcp-grid reveal">
        <div class="terminal-card">
          <div class="term-bar">
            <div class="term-dots"><span></span><span></span><span></span></div>
            <button type="button" class="btn btn-ghost" id="btn_copy_cli" style="padding:4px 10px;font-size:0.72rem;">Copy Quickstart</button>
          </div>
          <div class="term-body">
            <div><span class="term-cmt"># 1. Install MIT open-source engine</span></div>
            <div><span class="term-cmd">$ pip install ideastress</span></div>
            <div style="height:10px;"></div>
            <div><span class="term-cmt"># 2. Audit real codebase for uncapped AI API loops</span></div>
            <div><span class="term-cmd">$ ideastress scan-repo ./my-saas --price 29</span></div>
            <div style="height:10px;"></div>
            <div><span class="term-cmt"># 3. Launch 12-tool zero-dependency MCP server</span></div>
            <div><span class="term-cmd">$ ideastress mcp</span></div>
            <div style="height:10px;"></div>
            <div><span class="term-cmt"># 4. Run full 10-case falsification benchmark</span></div>
            <div><span class="term-cmd">$ python3 scripts/run_benchmark.py</span></div>
            <div style="color:var(--ok);margin-top:6px;">✓ 10/10 cases passed · 0.0% unsupported VERIFIED claims</div>
          </div>
        </div>

        <div class="mcp-tools-list">
          <div class="mcp-pill">solve_reverse_frontier<span>Max Viable CAC &amp; Min Price Floor</span></div>
          <div class="mcp-pill">run_monte_carlo<span>1,000-run seeded survival percentiles</span></div>
          <div class="mcp-pill">compute_autofix_plan<span>4-lever + annual prepay cash rescue</span></div>
          <div class="mcp-pill">scan_repo_ai_costs<span>Static Python/JS/TS LLM cost audit</span></div>
          <div class="mcp-pill">scan_geo_arbitrage<span>5-country CPC &amp; CAC headroom</span></div>
          <div class="mcp-pill">check_scope_creep<span>Coding-time FinOps margin gate</span></div>
          <div class="mcp-pill">quit_job_mrr_calc<span>Stripe vs MoR &amp; tax replacement</span></div>
          <div class="mcp-pill">freemium_drag_calc<span>Free-user subsidy &amp; margin stress</span></div>
          <div class="mcp-pill">social_cpm_funnel<span>Meta/TikTok CPM → CPA → ROAS</span></div>
          <div class="mcp-pill">generate_proof_card<span>1200×630 shareable SVG verdict</span></div>
          <div class="mcp-pill">diff_venture_ledger<span>Git-native assumption drift diff</span></div>
          <div class="mcp-pill">generate_kill_test_kit<span>72-hour falsification experiment</span></div>
        </div>
      </div>
    </div>
  </section>

  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <div>
        <strong style="color:var(--text);font-family:var(--serif);font-size:1.05rem;letter-spacing:0.1em;">IDEASTRESS</strong>
        <span style="margin-left:10px;">Edition 08.1 · Open-Source MIT · Preliminary feasibility modeling only (not financial, tax, or legal advice).</span>
      </div>
      <div class="mono" style="font-size:0.75rem;color:var(--accent);">Zero-Backend Deterministic Math · waterdolphinkiller.github.io/ideastress</div>
    </div>
  </footer>

  <!-- MODAL -->
  <div class="modal-backdrop" id="app_modal" role="dialog" aria-modal="true" aria-labelledby="modal_title">
    <div class="modal-box">
      <div class="modal-head">
        <h3 id="modal_title">Preview</h3>
        <button type="button" class="btn btn-ghost" id="modal_close_btn">Close ✕</button>
      </div>
      <div id="modal_body"></div>
      <div style="display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap;">
        <button type="button" class="btn" id="modal_copy_btn">Copy to Clipboard</button>
        <button type="button" class="btn primary" id="modal_dl_btn">Download File</button>
      </div>
    </div>
  </div>
  <div class="toast" id="toast" role="status" aria-live="polite"></div>

  <script>
{ENGINE_JS_LUXURY}
{APP_JS}
  </script>
</body>
</html>"""

out_canvas = ROOT.parent / "index.html"
out_web_index = ROOT / "web" / "index.html"
out_canvas.write_text(html, encoding="utf-8")
out_web_index.write_text(html, encoding="utf-8")
print(f"Built Luxury Editorial index.html: {out_canvas} ({len(html):,} bytes)")
