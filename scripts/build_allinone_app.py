"""Build the 10-in-1 Zero-Dead-Button Flagship Interactive App (`ideastress_v081_flagship_app.html` & `web/app.html`)
featuring:
  - All 10 live deterministic calculators (Reverse Frontier + Monte Carlo + Auto-Fix, Break-Even,
    SaaS LTV/CAC, E-Com ROAS, Runway, AI Token Margin, Geo-Arbitrage CPC, Quit-Your-Job MRR,
    Freemium Drag, Meta/TikTok CPM Funnel)
  - Per-tool v0.8.1 GEO/SEO content embedded inside every tab: 3-Step Quick Guide, Exact Formula,
    Arithmetic-Verified Worked Example, and 4 High-Intent FAQs
  - 1-Click Shareable State URL Hash (`#s=...`)
  - 1-Click 12-Month CSV Cash-Flow Export modal
  - 1-Click Live SVG Proof Card & `venture.yaml` preview/copy/download modal
  - Instant `EN / 中文` UI language toggle
  - Zero relative `.html` links — works 100% standalone offline or in Canvas preview
"""

from pathlib import Path
import html as html_lib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_seo_site as ssg
from geo_seo_content import TOOL_GEO_CONTENT

TABS = [
    ("frontier", "1. Reverse Frontier", "1. 反向红线与蒙特卡洛"),
    ("quit_job", "2. Quit-Job MRR", "2. 辞职替代 MRR"),
    ("freemium", "3. Freemium Drag", "3. 免费版拖累压测"),
    ("social_cpm", "4. Meta/TikTok CPM", "4. Meta/TikTok 信息流"),
    ("ai_margin", "5. AI Token Margin", "5. AI Token 毛利"),
    ("geo", "6. Geo-Arbitrage CPC", "6. 5 国 CPC 套利"),
    ("breakeven", "7. Break-Even", "7. 盈亏平衡"),
    ("saas", "8. SaaS LTV / CAC", "8. SaaS LTV/CAC"),
    ("ecom", "9. E-Com ROAS", "9. 电商 ROAS 底线"),
    ("runway", "10. Startup Runway", "10. 现金跑道压测"),
]

EXTRA_CSS = """
.panel { display: none; }
.panel.active { display: block; }
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(4,6,10,0.78); backdrop-filter: blur(6px);
  display: none; align-items: center; justify-content: center; padding: 20px; z-index: 100;
}
.modal-backdrop.open { display: flex; }
.modal-box {
  background: var(--surface); border: 1px solid var(--border-hi); border-radius: 16px;
  max-width: 860px; width: 100%; max-height: 88vh; overflow-y: auto; padding: 22px;
}
.modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; gap: 12px; }
.modal-head h3 { margin: 0; font-size: 1.05rem; }
.modal-pre {
  background: var(--bg); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px; overflow-x: auto; font-size: 0.83rem; color: #dbeafe; margin: 0 0 14px;
}
.svg-preview { width: 100%; border-radius: 12px; overflow: hidden; border: 1px solid var(--border); margin-bottom: 14px; }
.svg-preview svg { width: 100%; height: auto; display: block; }
.util-bar { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.faq-item h3 { margin: 0 0 6px; font-size: 0.94rem; color: var(--text); }
.faq-item p { margin: 0; font-size: 0.84rem; color: var(--muted); }
"""

pill_btns = "\n        ".join(
    f'<button type="button" class="route-pill{" active" if i == 0 else ""}" data-switch="{k}" data-en="{en}" data-zh="{zh}">{en}</button>'
    for i, (k, en, zh) in enumerate(TABS)
)

def render_panel_geo_html(tool_key: str) -> str:
    geo = TOOL_GEO_CONTENT[tool_key]
    steps_li = "".join(f"<li>{html_lib.escape(s)}</li>" for s in geo["how_to"])
    faqs_html = "".join(
        f'<div class="faq-item"><h3>{html_lib.escape(q)}</h3><p>{html_lib.escape(a)}</p></div>'
        for q, a in geo["faqs"]
    )
    formula_esc = html_lib.escape(geo["formula"])
    example_esc = html_lib.escape(geo["worked_example"])
    return f"""
<section class="section">
  <h2>How to Use &amp; Exact Formula</h2>
  <p class="lead">Transparent deterministic math — inspect every formula and worked example before trusting any projection.</p>
  <div class="row-2" style="gap:18px;align-items:start;">
    <div class="card">
      <h3 style="margin-top:0;font-size:1rem;">3-Step Quick Guide</h3>
      <ol style="padding-left:20px;margin:8px 0 0;color:var(--muted);font-size:0.9rem;">{steps_li}</ol>
    </div>
    <div class="card">
      <h3 style="margin-top:0;font-size:1rem;">Formula &amp; Worked Example</h3>
      <pre class="mono" style="background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:12px;overflow-x:auto;font-size:0.8rem;color:#cbd5e1;margin:0 0 10px;">{formula_esc}</pre>
      <p style="margin:0;font-size:0.86rem;color:var(--muted);">{example_esc}</p>
    </div>
  </div>
</section>
<section class="section">
  <h2>Frequently Asked Questions</h2>
  <div class="faq-grid">{faqs_html}</div>
</section>
"""

panels_html = []
all_faqs = []
for i, (k, _, _) in enumerate(TABS):
    raw = ssg.TOOL_HTML[k].split("<script>")[0]
    if k == "frontier":
        raw = raw.replace(
            '<button id="btn_proof_card" class="btn" style="flex:1;justify-content:center;">Download Proof Card SVG</button>',
            '<button id="btn_proof_card" class="btn" style="flex:1;justify-content:center;">Proof Card SVG</button>\n'
            '      <button id="btn_export_csv" class="btn" style="flex:1;justify-content:center;">Export 12m CSV</button>\n'
            '      <button id="btn_share_url" class="btn" style="flex:1;justify-content:center;">Copy Share Link</button>',
        )
    geo_html = render_panel_geo_html(k)
    active_cls = " active" if i == 0 else ""
    panels_html.append(f'<div class="panel{active_cls}" id="panel-{k}">\n{raw}\n{geo_html}\n</div>')
    all_faqs.extend(TOOL_GEO_CONTENT[k]["faqs"])

ld_json = json.dumps(
    {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebApplication",
                "name": "IdeaStress v0.8.1 — 10-in-1 Startup Financial Stress-Test Suite",
                "url": "https://waterdolphinkiller.github.io/ideastress/app.html",
                "applicationCategory": "BusinessApplication",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                "description": "10 interactive deterministic startup calculators with 1,000-run Monte Carlo, Auto-Fix rescue solver, 3-step guides, exact formulas, worked examples, and 40 FAQs.",
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

APP_JS = """
let currentLang = 'en';
const I18N = {
  en: {
    eyebrow: 'IDEASTRESS v0.8.1 · 10 LIVE CALCULATORS · 1,000-RUN MONTE CARLO · AUTO-FIX · GEO/FAQ',
    h1: 'Stress-test your business idea with hard math before you write code.',
    sub: 'All 10 calculators + step-by-step guides, exact formulas, worked examples & 40 FAQs run 100% live in this single page — zero dead buttons.',
    langBtn: '中文'
  },
  zh: {
    eyebrow: 'IDEASTRESS v0.8.1 · 10 合 1 实时计算器矩阵 · 1,000 次蒙特卡洛 · 自动救命处方 · 内嵌指南与 FAQ',
    h1: '写第一行代码前，先用确定性数学压测你的商业想法。',
    sub: '10 大创业高频计算器及各自的使用说明、核心公式、算例与 40 条 FAQ 全部在本页实时运行，零空按钮：支持一键切换、行业预设、分享链接、导出 CSV 与战绩 SVG 卡片。',
    langBtn: 'EN'
  }
};

function toggleLang() {
  currentLang = currentLang === 'en' ? 'zh' : 'en';
  const t = I18N[currentLang];
  document.getElementById('hero_eyebrow').textContent = t.eyebrow;
  document.getElementById('hero_h1').textContent = t.h1;
  document.getElementById('hero_sub').textContent = t.sub;
  document.getElementById('lang_toggle_btn').textContent = t.langBtn;
  document.querySelectorAll('.route-pill').forEach(btn => {
    btn.textContent = btn.getAttribute('data-' + currentLang);
  });
}
document.getElementById('lang_toggle_btn').onclick = toggleLang;

function switchTab(key) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.route-pill').forEach(b => b.classList.remove('active'));
  const target = document.getElementById('panel-' + key);
  if (target) target.classList.add('active');
  document.querySelectorAll('.route-pill[data-switch="' + key + '"]').forEach(b => b.classList.add('active'));
}
document.querySelectorAll('[data-switch]').forEach(btn => {
  btn.addEventListener('click', () => switchTab(btn.getAttribute('data-switch')));
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
    } catch (e) { showToast('Use Copy button below.'); }
  };
  document.getElementById('modal_copy_btn').onclick = () => {
    navigator.clipboard?.writeText(downloadContent).then(
      () => showToast('Copied to clipboard!'),
      () => showToast('Select & copy from the preview box above.')
    );
  };
  document.getElementById('app_modal').classList.add('open');
}
document.getElementById('modal_close_btn').onclick = () => document.getElementById('app_modal').classList.remove('open');
document.getElementById('app_modal').addEventListener('click', e => { if (e.target.id === 'app_modal') e.target.classList.remove('open'); });

// Restore state from URL hash (#s=...) if present
(function restoreFromHash() {
  try {
    if (!location.hash.startsWith('#s=')) return;
    const obj = JSON.parse(atob(decodeURIComponent(location.hash.slice(3))));
    Object.entries(obj).forEach(([id, val]) => {
      const el = document.getElementById(id);
      if (el) el.value = val;
    });
    showToast('Loaded shared scenario from URL!');
  } catch (e) {}
})();

// Initialize ALL 10 calculators
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

// 1. Export venture.yaml modal
document.getElementById('btn_export_yaml').onclick = () => {
  const c = readFrontierCfg();
  const y = `idea: "My ${c.type} business idea"
target_market:
  - "United States"
business_type: ${c.type}
budget: "${c.cash}"
currency: ${c.cur}
timeline_months: 12
financials:
  business_type: ${c.type}
  currency: ${c.cur}
  unit_price: "${c.price}"
  variable_cost_per_unit: "${c.varCost}"
  fixed_monthly_costs: "${c.fixed}"
  monthly_new_customers: ${c.newC}
  monthly_acquisition_spend: "${c.spend}"
  monthly_churn_rate: "${(c.churnPct / 100).toFixed(4)}"
  refund_rate: "${(c.refundPct / 100).toFixed(4)}"
  payment_processor: "${c.processor}"
  effective_tax_rate: "${(c.taxPct / 100).toFixed(4)}"
  starting_cash: "${c.cash}"
  horizon_months: 12
`;
  openModal('Exported venture.yaml (IdeaStress CLI & MCP)', `<pre class="modal-pre mono">${y.replace(/</g,'&lt;')}</pre>`, 'venture.yaml', y, 'text/yaml');
};

// 2. Live Proof Card SVG modal
document.getElementById('btn_proof_card').onclick = () => {
  const c = readFrontierCfg();
  const mc = runMonteCarlo1000(c);
  const maxCac = solveMaxCac(c);
  const cpc = parseFloat(document.getElementById('f_cpc')?.value) || 0;
  const cvr = Math.max(0.001, (parseFloat(document.getElementById('f_cvr')?.value) || 2.5) / 100);
  const impCac = cpc / cvr;
  const cpcOk = maxCac > 0 && impCac <= maxCac;
  const col = mc.survivalPct >= 85 ? '#10b981' : (mc.survivalPct >= 50 ? '#f59e0b' : '#ef4444');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <rect width="1200" height="630" fill="#080a0f"/><rect x="44" y="44" width="1112" height="542" rx="24" fill="#101521" stroke="#243047" stroke-width="2"/>
  <circle cx="96" cy="98" r="8" fill="#38bdf8"/><text x="116" y="105" fill="#edf2fb" font-family="Inter, sans-serif" font-size="22" font-weight="800" letter-spacing="2">IDEASTRESS // FALSIFICATION PROOF CARD</text>
  <rect x="880" y="72" width="236" height="46" rx="23" fill="${col}" fill-opacity="0.16" stroke="${col}" stroke-width="2"/>
  <text x="998" y="102" text-anchor="middle" fill="${col}" font-family="monospace" font-size="20" font-weight="800">${mc.risk}</text>
  <text x="86" y="185" fill="#ffffff" font-family="Inter, sans-serif" font-size="36" font-weight="800">${c.type.toUpperCase()} · ${c.cur} ${c.price} Price · ${c.cur} ${c.cash.toLocaleString()} Cash</text>
  <rect x="86" y="245" width="320" height="200" rx="16" fill="#161d2e" stroke="#26324a"/>
  <text x="114" y="290" fill="#8a95ad" font-family="monospace" font-size="15">12M SURVIVAL (1,000 RUNS)</text>
  <text x="114" y="365" fill="${col}" font-family="monospace" font-size="52" font-weight="800">${mc.survivalPct.toFixed(1)}%</text>
  <text x="114" y="415" fill="#cbd5e1" font-family="Inter, sans-serif" font-size="17">P10 Cash: ${c.cur} ${Math.round(mc.p10End).toLocaleString()}</text>
  <rect x="440" y="245" width="320" height="200" rx="16" fill="#161d2e" stroke="#26324a"/>
  <text x="468" y="290" fill="#8a95ad" font-family="monospace" font-size="15">MAX VIABLE CAC CEILING</text>
  <text x="468" y="365" fill="#38bdf8" font-family="monospace" font-size="44" font-weight="800">${c.cur} ${maxCac.toFixed(2)}</text>
  <text x="468" y="415" fill="#cbd5e1" font-family="Inter, sans-serif" font-size="17">Monthly Spend: ${c.cur} ${c.spend}</text>
  <rect x="794" y="245" width="320" height="200" rx="16" fill="#161d2e" stroke="#26324a"/>
  <text x="822" y="290" fill="#8a95ad" font-family="monospace" font-size="15">GOOGLE ADS CPC CHECK</text>
  <text x="822" y="355" fill="${cpcOk ? '#10b981' : '#ef4444'}" font-family="monospace" font-size="26" font-weight="800">${cpcOk ? 'CHANNEL_VIABLE' : 'CHANNEL_IMPOSSIBLE'}</text>
  <text x="822" y="415" fill="#cbd5e1" font-family="Inter, sans-serif" font-size="17">Implied CAC: ${c.cur} ${impCac.toFixed(2)}</text>
  <line x1="86" y1="496" x2="1114" y2="496" stroke="#243047" stroke-width="1.5"/>
  <text x="86" y="544" fill="#8a95ad" font-family="monospace" font-size="17">Stress-tested with IdeaStress (MIT Open-Source) · pip install ideastress</text>
  <text x="1114" y="544" text-anchor="end" fill="#38bdf8" font-family="monospace" font-size="17">waterdolphinkiller.github.io/ideastress</text></svg>`;
  openModal('Shareable 1200x630 Proof Card (SVG)', `<div class="svg-preview">${svg}</div>`, 'ideastress_proof_card.svg', svg, 'image/svg+xml');
};

// 3. Export 12-Month CSV Cash-Flow Table modal
document.getElementById('btn_export_csv').onclick = () => {
  const c = readFrontierCfg();
  const base = simPath(c);
  const cons = simPath(c, { p: 0.9, nc: 0.65, v: 1.15, fx: 1.1, sp: 1.25, ch: 1.35 });
  const opt = simPath(c, { p: 1.1, nc: 1.3, v: 0.95, sp: 0.9, ch: 0.8 });
  const lines = ['Month,Currency,Conservative_Cash,Base_Cash,Optimistic_Cash'];
  for (let m = 0; m <= 12; m++) {
    lines.push(`${m},${c.cur},${cons.series[m].toFixed(2)},${base.series[m].toFixed(2)},${opt.series[m].toFixed(2)}`);
  }
  const csv = lines.join('\\n') + '\\n';
  openModal('12-Month Cash Trajectory (CSV for Excel / Google Sheets)', `<pre class="modal-pre mono">${csv}</pre>`, 'ideastress_12m_cashflow.csv', csv, 'text/csv');
};

// 4. Shareable State URL Hash
document.getElementById('btn_share_url').onclick = () => {
  const ids = ['f_type','f_cur','f_proc','f_tax','f_price','f_var','f_fixed','f_cash','f_new','f_spend','f_churn','f_refund','f_cpc','f_cvr'];
  const state = {};
  ids.forEach(id => { const el = document.getElementById(id); if (el) state[id] = el.value; });
  const hash = '#s=' + encodeURIComponent(btoa(JSON.stringify(state)));
  const shareUrl = 'https://waterdolphinkiller.github.io/ideastress/app.html' + hash;
  try { history.replaceState(null, '', hash); } catch (e) {}
  openModal('Shareable Scenario Link (Zero-Backend URL State)', `<pre class="modal-pre mono">${shareUrl}</pre><p class="muted" style="font-size:0.84rem;margin:0 0 12px;">Send this link to your co-founder — opening it automatically restores all 14 parameters and curves.</p>`, 'share_url.txt', shareUrl, 'text/plain');
};
"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>IdeaStress v0.8.1 — 10-in-1 Interactive Startup Stress-Test Suite</title>
  <meta name="description" content="10 live startup financial calculators with 1,000-run Monte Carlo, Auto-Fix rescue solver, 3-step guides, exact formulas, worked examples, and 40 FAQs." />
  <script type="application/ld+json">{ld_json}</script>
  <style>
{ssg.STYLE_CSS}
{EXTRA_CSS}
  </style>
</head>
<body>
  <header>
    <div class="container nav-inner">
      <div class="logo" style="cursor:pointer;" onclick="switchTab('frontier')"><span class="dot"></span>IDEA<span>STRESS</span></div>
      <div style="display:flex;gap:10px;align-items:center;">
        <button type="button" class="btn" onclick="switchTab('quit_job')">Quit-Job MRR</button>
        <button type="button" class="btn" onclick="switchTab('freemium')">Freemium</button>
        <button type="button" class="btn" onclick="switchTab('social_cpm')">Meta/TikTok</button>
        <button type="button" class="btn primary" id="lang_toggle_btn">中文</button>
      </div>
    </div>
  </header>
  <main class="container">
    <section class="hero">
      <div class="eyebrow" id="hero_eyebrow">IDEASTRESS v0.8.1 · 10 LIVE CALCULATORS · 1,000-RUN MONTE CARLO · AUTO-FIX · GEO/FAQ</div>
      <h1 id="hero_h1">Stress-test your business idea with hard math before you write code.</h1>
      <p id="hero_sub">All 10 calculators + step-by-step guides, exact formulas, worked examples &amp; 40 FAQs run 100% live in this single page — zero dead buttons.</p>
      <div class="route-bar">
        {pill_btns}
      </div>
    </section>

    {"".join(panels_html)}
    {ssg.BENCHMARKS_TABLE}

    <footer>
      <div><strong>IdeaStress v0.8.1</strong> · Open-Source MIT · Preliminary feasibility math only (not financial, tax, or legal advice).</div>
      <div class="mono">CLI &amp; MCP: pip install ideastress &amp;&amp; ideastress mcp</div>
    </footer>
  </main>

  <div class="modal-backdrop" id="app_modal">
    <div class="modal-box">
      <div class="modal-head">
        <h3 id="modal_title">Preview</h3>
        <button type="button" class="btn" id="modal_close_btn">Close ✕</button>
      </div>
      <div id="modal_body"></div>
      <div style="display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap;">
        <button type="button" class="btn" id="modal_copy_btn">Copy to Clipboard</button>
        <button type="button" class="btn primary" id="modal_dl_btn">Download File</button>
      </div>
    </div>
  </div>
  <div class="toast" id="toast"></div>

  <script>
{ssg.ENGINE_JS}
{APP_JS}
  </script>
</body>
</html>"""

out_canvas = ROOT.parent / "ideastress_v081_flagship_app.html"
out_web = ROOT / "web" / "app.html"
out_canvas.write_text(html, encoding="utf-8")
out_web.write_text(html, encoding="utf-8")
print("Built v0.8.1 10-in-1 Zero-Dead-Button Flagship App:", out_canvas, len(html), "bytes")
