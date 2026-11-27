"""Tailored GEO (Generative Engine Optimization) & SEO content for all 10 IdeaStress calculators.

Provides per-tool:
  - 3-step How-To guide (rendered visually + `HowTo` JSON-LD)
  - Exact deterministic formulas
  - Concrete arithmetic-verified Worked Example
  - 4 high-intent FAQs (rendered visually + `FAQPage` JSON-LD)
  - Generators for `/llms.txt` and `/llms-full.txt`
"""

from __future__ import annotations

from typing import Dict, List

TOOL_GEO_CONTENT: Dict[str, dict] = {
    "frontier": {
        "name": "Reverse Unit-Economics Survival Frontier & Monte Carlo Solver",
        "how_to": [
            "Enter your unit price, variable cost per unit, fixed monthly costs, and starting cash (or click one of the 3 one-click presets).",
            "Optionally open Advanced Settings to apply Stripe US (2.9% + $0.30) or MoR (5% + $0.50) fees and your effective US tax reserve.",
            "Review your 1,000-run Monte Carlo survival probability, solved Max Viable CAC ceiling, Google Ads CPC verdict, and Auto-Fix rescue price.",
        ],
        "formula": "Net_Unit_Contrib = Unit_Price × (1 − Refund_Rate) − Variable_Cost − Payment_Fee\nMax_Viable_CAC = GoalSeek(CAC : min_{m=1..12} Ending_Cash(m) ≥ 0)\nImplied_Paid_CAC = Google_Ads_CPC / Landing_Page_CVR",
        "worked_example": "For a $49/mo SaaS with $6 variable cost, Stripe US fee ($1.72), $900 fixed costs, 5% monthly churn, 14 new customers/mo, and $12,000 starting cash, net unit contribution is ~$40.30. Over 12 months, the business can survive up to ~$210 CAC; however, if US Google Ads CPC is $8.90 at 2.5% conversion, implied paid CAC is $356 — triggering CHANNEL_IMPOSSIBLE before spending $1 on ads.",
        "faqs": [
            ("What is a Reverse Unit-Economics Survival Frontier?", "Instead of guessing 3-year revenue, a reverse solver works backward from your cash budget, price, and fixed costs to compute the exact maximum CAC, minimum price floor, and maximum churn your business can survive over 12 months."),
            ("How does the 1,000-run Monte Carlo simulation work?", "It runs 1,000 reproducible seeded paths perturbing monthly acquisition volume, upward-skewed CAC overruns, variable cost drift, and a realistic Month 1–2 SaaS onboarding churn spike to output survival probability and P10/P50/P90 cash percentiles."),
            ("Why did my profitable SaaS get a CHANNEL_IMPOSSIBLE warning?", "Even when unit margins are strong, crowded Google Ads categories (e.g., $8.90 CPC at 2.5% CVR = $356 implied CAC) can exceed your solved Max Viable CAC ceiling. That means you must use SEO, outbound, or lower-CPC geos instead of generic search ads."),
            ("Does IdeaStress include Stripe US fees and taxes?", "Yes. You can toggle Stripe US (2.9% + $0.30), Stripe US + Billing (3.6% + $0.30), or Merchant of Record Paddle/Lemon Squeezy (5% + $0.50), plus an optional effective income tax reserve on positive monthly profit."),
        ],
    },
    "breakeven": {
        "name": "Break-Even Calculator (with US Stripe & MoR Fees)",
        "how_to": [
            "Select your payment processor preset (Stripe US 2.9% + $0.30, MoR 5% + $0.50, or None).",
            "Enter your selling price, variable cost per unit, refund rate, and total monthly fixed overhead.",
            "Compare your expected monthly unit volume against the solved Break-Even Units to see monthly operating profit or shortfall.",
        ],
        "formula": "Net_Unit_Contribution = Selling_Price × (1 − Refund_Rate) − Variable_Cost − Payment_Fee\nBreak_Even_Units = ceil(Fixed_Monthly_Costs / Net_Unit_Contribution)",
        "worked_example": "At a $65 selling price, 2% refund rate ($63.70 net), $22 variable cost, and $2.19 Stripe US fee, net unit contribution is $39.51. Covering $4,200 in fixed monthly overhead requires ceil(4200 / 39.51) = 107 units/month ($6,955 monthly revenue).",
        "faqs": [
            ("How do Stripe fees affect break-even units?", "Stripe's US domestic card fee of 2.9% + $0.30 reduces your contribution margin on every sale, which increases the exact number of units required to cover fixed overhead — especially on low-ticket items under $25."),
            ("What happens when variable cost exceeds net selling price?", "Unit contribution margin becomes negative, meaning every additional unit sold loses money. IdeaStress flags break-even as Unreachable instead of outputting a misleading negative number."),
            ("Should ad spend be included in fixed overhead for break-even?", "If you run a fixed monthly ad budget (e.g., $1,000/mo), include it in fixed overhead to compute true cash break-even; if you scale ad spend per order (CPA), add CPA to variable cost per unit."),
            ("Is break-even revenue the same as profit?", "No. Break-even revenue is simply the point where total revenue equals total fixed plus variable costs ($0 operating profit before taxes)."),
        ],
    },
    "saas": {
        "name": "SaaS LTV / CAC & Payback Calculator (2026 Benchmarks)",
        "how_to": [
            "Select your SaaS billing fee preset (Stripe US + Billing 3.6% + $0.30 or MoR 5% + $0.50).",
            "Enter Monthly ARPA, Gross Margin %, Monthly Customer Churn %, and Customer Acquisition Cost (CAC).",
            "Check your LTV:CAC ratio against the 3.0x baseline (2026 private SaaS median is 4.1x) and CAC Payback against the 16-month median.",
        ],
        "formula": "Monthly_Gross_Profit = (ARPA × Gross_Margin_Pct) − Payment_Fee\nLTV = Monthly_Gross_Profit / Monthly_Churn_Rate\nCAC_Payback_Months = CAC / Monthly_Gross_Profit",
        "worked_example": "For a $49/mo SaaS with 80% gross margin, Stripe Billing fee ($2.06), 5.5% monthly churn, and $180 CAC: net monthly gross profit is $37.14, LTV is $675, LTV:CAC is 3.75x (healthy > 3.0x), and CAC payback is 4.8 months.",
        "faqs": [
            ("What is a healthy SaaS LTV:CAC ratio in 2026?", "3.0x remains the minimum healthy rule of thumb, while 2026 private SaaS medians sit around 4.1x with an 80% software gross margin and 16-month CAC payback period (Benchmarkit / SubscriptionPlaybook 2026)."),
            ("What is average monthly churn for low-priced SaaS?", "According to ChartMogul's November 2026 benchmarks, median monthly customer churn is 6.2% for SaaS with ARPA under $25, compared to 2.6% for SaaS above $1,000 ARPA."),
            ("Why must LTV be gross-margin adjusted?", "Using raw revenue instead of gross profit overstates customer value, especially for AI-heavy SaaS products where LLM token COGS compress gross margin well below 80%."),
            ("Can LTV be calculated if monthly churn is 0%?", "No. Dividing by zero produces infinity; with zero observed churn on a small early cohort, treat LTV as unvalidated until at least 3–6 months of retention data exist."),
        ],
    },
    "ecom": {
        "name": "E-Commerce Profit Margin & Break-Even ROAS Calculator",
        "how_to": [
            "Enter Average Order Value (AOV), product COGS, shipping/fulfillment cost, and your payment fee preset.",
            "Input your blended paid ad CPA / CAC.",
            "Read your exact Break-Even ROAS floor, maximum profitable CPA, and real first-order net profit.",
        ],
        "formula": "Pre_Ad_Margin = AOV − COGS − Shipping − Payment_Fee\nBreak_Even_ROAS = AOV / Pre_Ad_Margin\nFirst_Order_Net_Profit = Pre_Ad_Margin − Ad_CPA",
        "worked_example": "On a $68 AOV order with $19 COGS, $7 shipping, and $2.27 Stripe/Shopify fee, pre-ad margin is $39.73 (58.4%). Break-Even ROAS is 68 / 39.73 = 1.71x. At a $34 paid ad CPA, you keep $5.73 first-order net profit.",
        "faqs": [
            ("What is Break-Even ROAS in e-commerce?", "Break-Even ROAS (Return on Ad Spend) is the minimum ad revenue multiple required so first-order gross profit exactly covers your ad spend. Any ROAS below this floor loses money on every new customer."),
            ("What is the average e-commerce CAC in 2026?", "First Page Sage benchmarks place blended e-commerce CAC between $53 and $91 across 13 verticals, which is why low-AOV stores (<$40) struggle on paid ads without high repeat purchase rates."),
            ("What is a realistic Shopify conversion rate in 2026?", "Littledata's late-2026 Shopify dataset reports a 1.4% median store conversion rate, with the top 20% exceeding 2.7% and top 10% exceeding 3.7%."),
            ("How do e-commerce gross margins vary by category?", "Hycos 2026 benchmarks show 60%–80% for Beauty & Skincare, 55%–70% for Health & Supplements, 45%–65% for Fashion & Apparel, and 15%–30% for Consumer Electronics."),
        ],
    },
    "runway": {
        "name": "Startup Runway & Burn Stress-Tester",
        "how_to": [
            "Enter current bank cash, current monthly revenue, expected monthly revenue growth %, and total monthly expenses.",
            "Compare your Base Runway against the built-in Downside Shock (−30% revenue, 50% slower growth, +20% cost overrun).",
            "Use the Shock Runway to decide when to cut burn, raise prices, or start fundraising (typically 6+ months before zero cash).",
        ],
        "formula": "Monthly_Net_Burn(m) = Monthly_Expenses − Monthly_Revenue(m)\nRunway = First month m where Cash(m) < 0",
        "worked_example": "With $45,000 cash, $3,500 monthly revenue growing 10%/mo, and $8,500 monthly burn, base runway is ~14 months; under a −30% revenue and +20% expense shock, runway compresses sharply to ~6 months.",
        "faqs": [
            ("Why stress-test runway with a −30% revenue and +20% cost shock?", "Early startup revenue is lumpy and infrastructure, ad spend, or contractor costs routinely overrun. Planning solely on base-case runway leaves zero buffer when a channel slows down."),
            ("What is the difference between gross burn and net burn?", "Gross burn is total monthly cash outflow (expenses). Net burn is expenses minus monthly revenue collected. Runway is governed by net burn."),
            ("How many months of runway should a bootstrapped founder keep?", "Keep at least 6–12 months of shock-tested runway before committing to fixed recurring expenses like full-time hires or annual office leases."),
            ("Does revenue growth automatically extend runway?", "Only if unit contribution margin is positive and customer acquisition spend does not scale faster than collected cash."),
        ],
    },
    "ai_margin": {
        "name": "AI Wrapper Token Cost & Whale Bankruptcy Calculator",
        "how_to": [
            "Enter your flat monthly subscription price and select the LLM pricing tier (Fast/Mini, Mid/Balanced, or Frontier Reasoning).",
            "Input average daily requests per user along with typical input and output token counts.",
            "Check your real AI Gross Margin % (vs 80% traditional SaaS median) and your exact Whale Bankruptcy daily request limit.",
        ],
        "formula": "Cost_Per_Request = (Input_Tokens / 1e6) × In_Rate + (Output_Tokens / 1e6) × Out_Rate\nMonthly_AI_COGS = Cost_Per_Request × Daily_Requests × 30\nWhale_Daily_Limit = floor((Price − Stripe_Fee − Infra) / (Cost_Per_Request × 30))",
        "worked_example": "On a $29/mo plan using a Mid/Balanced model ($1.25 in / $5.00 out per 1M tokens) at 3,000 input + 900 output tokens ($0.00825/req) and 25 requests/day, monthly AI COGS is $6.19 plus $1.14 Stripe fee and $1 infra = $8.33 variable cost (71.3% margin). Any whale user exceeding 108 requests/day turns unprofitable.",
        "faqs": [
            ("Why do AI SaaS products have lower gross margins than traditional SaaS?", "Traditional private SaaS averages ~80% gross margin (Benchmarkit 2026), whereas AI apps incur recurring per-token inference COGS on every user prompt, often compressing margins to 40%–65%."),
            ("What is the Whale Bankruptcy Limit?", "It is the exact number of daily requests at which a heavy power user on a flat-rate 'unlimited' subscription costs more in LLM API fees than their entire monthly payment."),
            ("How can I protect margins on an AI wrapper?", "Route routine prompts to budget/mini models, enforce hard max_tokens caps, cache repeated context, and gate frontier reasoning or video generation behind credit packs or add-on tiers."),
            ("Can IdeaStress scan my actual repository for token cost risks?", "Yes. Run `ideastress scan-repo ./my-app --price 29` via CLI or MCP to statically detect OpenAI/Anthropic/Google/Replicate SDK calls inside loops and missing max_tokens caps."),
        ],
    },
    "geo": {
        "name": "5-Country Geo-Arbitrage CPC & CAC Scanner (US / UK / DE / SG / MY)",
        "how_to": [
            "Enter your US baseline Google Ads CPC (e.g., $8.90 for accounting software).",
            "Input your solved US Max Viable CAC ceiling and expected landing-page conversion rate.",
            "Compare localized CPC, implied CAC, and headroom multiples across US, UK, Germany (DACH), Singapore, and Malaysia.",
        ],
        "formula": "Localized_Implied_CAC = Country_CPC / Conversion_Rate\nArbitrage_Headroom = Localized_Max_Viable_CAC / Localized_Implied_CAC",
        "worked_example": "When US Google Ads CPC is $8.90 (implied CAC $356 at 2.5% CVR) and your US ceiling is $200, US paid search fails (0.56x headroom). In Malaysia, localized CPC (~$2.31) yields ~$92 implied CAC against a $110 localized ceiling (1.19x headroom — CHANNEL_VIABLE).",
        "faqs": [
            ("What is Geo-Arbitrage in SaaS and indie hacking?", "It is launching into non-US or non-English markets where Google Ads CPC and competition are 2x–4x lower than the US while local willingness to pay still supports profitable unit economics."),
            ("Why is US Google Ads CPC so high in 2026?", "Publicly tracked indie SaaS products roughly tripled between 2020 and 2026 and CAC rose ~60% over five years, driving US high-intent B2B keywords to $6–$15+ per click."),
            ("Does IdeaStress support live multi-country CPC lookups?", "Yes. With a DataForSEO key in `.env`, `ideastress geo-scan` queries live Google Ads search volume and CPC by country `location_code` and caches results for 30 days in SQLite."),
            ("Should I adjust pricing when entering lower-CPC countries?", "Yes. Our scanner automatically scales your localized max viable CAC by a purchasing-power factor so you do not overestimate revenue in lower-ARPA regions."),
        ],
    },
    "quit_job": {
        "name": "Quit-Your-Job MRR & US Solo Founder Take-Home Calculator",
        "how_to": [
            "Enter the annual net salary you want to replace (e.g., $120,000) and your estimated US tax reserve % (federal + state + self-employment).",
            "Add your monthly software, hosting, and marketing costs, plus your average monthly subscription price.",
            "Toggle between Stripe US (2.9% + $0.30) and MoR Paddle/Lemon Squeezy (5% + $0.50) to see required MRR and exact annual fee savings.",
        ],
        "formula": "Required_PreTax_Profit = (Target_Annual_Salary / 12) / (1 − Effective_Tax_Rate)\nRequired_Customers = ceil((Required_PreTax_Profit + Monthly_Ops) / (Price × (1 − Fee_Pct) − Fee_Flat))",
        "worked_example": "To replace a $120,000/yr net salary ($10,000/mo) with a 30% tax reserve ($14,286 pre-tax profit needed) and $1,500 monthly ops on a $49/mo Stripe US plan ($47.28 net/cust), you need 334 paying customers = $16,366 MRR. Using Stripe US saves ~$4,925/yr in fees vs a 5% + $0.50 MoR.",
        "faqs": [
            ("How much MRR do I need to replace a $100,000 salary in the US?", "After setting aside ~30% for US federal/state/self-employment taxes, payment processing fees, and modest operating costs, replacing $100k net typically requires $13,000–$15,000 in stable MRR."),
            ("Should I use Stripe or a Merchant of Record (Paddle / Lemon Squeezy)?", "Stripe US charges 2.9% + $0.30 (cheaper on fees), while Paddle/Lemon Squeezy charge 5% + $0.50 but act as the legal seller handling global VAT and US sales tax compliance for you."),
            ("Why shouldn't I quit my job the first month I hit target MRR?", "Early SaaS MRR has high churn volatility. Wait until you have held target MRR for 3+ consecutive months and banked 6–12 months of personal emergency runway."),
            ("Is this formal US tax advice?", "No. Tax reserve percentages are planning estimates only; consult a licensed CPA for LLC/S-Corp elections and quarterly estimated tax filings."),
        ],
    },
    "freemium": {
        "name": "Freemium Economics & Free-User Cost Drag Calculator",
        "how_to": [
            "Enter your total Monthly Active Users (MAU) and your realistic free-to-paid conversion rate %.",
            "Input your paid plan price, monthly hosting/AI cost per free user, and monthly COGS per paid user.",
            "Check whether free-tier drag pushes your product into FREEMIUM_BLEEDING and read your exact minimum break-even conversion rate.",
        ],
        "formula": "Free_Tier_Drag = Free_Users × Monthly_Cost_Per_Free_User\nMin_BreakEven_CVR = Free_Cost / (Paid_Unit_Contribution + Free_Cost)",
        "worked_example": "With 10,000 MAU, 2% conversion (200 paid @ $29 = $5,800 rev), $0.35/mo free-user cost ($3,430 drag), and $4 paid COGS + Stripe fees ($1,028), net monthly gross profit is only $1,342 (23.1% blended margin). At $0.60/free user, the business bleeds cash every month.",
        "faqs": [
            ("When does a Freemium model fail for AI SaaS?", "Freemium fails whenever free users consume recurring LLM tokens or GPU compute without driving viral word-of-mouth — even $0.50/mo per free user destroys margins at a typical 1.5%–2% conversion rate."),
            ("What is a realistic free-to-paid conversion rate?", "Self-serve B2B/prosumer freemium products typically convert 1%–5% of free signups; assuming >8% without strong usage gates is usually overly optimistic."),
            ("How do I fix a bleeding freemium tier?", "Replace unlimited free access with a one-time free credit allowance (e.g., 10 lifetime credits), a 7–14 day reverse trial, or strict client-side/zero-cost free tools."),
            ("Why does Stripe fee apply only to paid users?", "Payment processing fees (2.9% + $0.30) are incurred only on paid transactions, while infrastructure and AI token costs apply to both free and paid cohorts."),
        ],
    },
    "social_cpm": {
        "name": "Meta & TikTok Paid Social Funnel Calculator (CPM → CTR → CVR → CPA)",
        "how_to": [
            "Enter your platform CPM (cost per 1,000 ad impressions, typically $12–$30 in the US) and ad Click-Through Rate (CTR %).",
            "Input your landing-page conversion rate (CVR %), Average Order Value (AOV), and pre-ad gross margin %.",
            "See your exact effective CPC, implied Paid Social CPA, Break-Even ROAS, and first-order profit or loss.",
        ],
        "formula": "Effective_CPC = CPM / (1000 × CTR)\nImplied_Social_CPA = Effective_CPC / Landing_Page_CVR\nFirst_Order_Net = (AOV × Pre_Ad_Margin_Pct) − Implied_Social_CPA",
        "worked_example": "At $18 CPM and 1.2% CTR (12 clicks per 1,000 impressions), effective CPC is $1.50. At 2.2% landing-page conversion, implied CPA is $68.18. On a $68 AOV product with 60% margin ($40.80 pre-ad profit), you lose $27.38 on every first order — requiring higher CTR creative, bundles to lift AOV, or strong repeat LTV.",
        "faqs": [
            ("Why calculate paid social from CPM instead of CPC?", "Meta (Facebook/Instagram) and TikTok charge by impressions (CPM). Your real CPC is entirely determined by creative thumb-stop and click-through rate (CTR)."),
            ("What is a realistic Meta Ads CTR and landing-page CVR?", "Cold paid social campaigns commonly see 0.8%–1.8% link CTR and 1.4%–2.7% Shopify store conversion rate (Littledata 2026 median is 1.4%)."),
            ("Which lever improves paid social CPA fastest?", "Doubling creative CTR from 0.9% to 1.8% cuts your effective CPC and CPA in half immediately without changing your product price or website."),
            ("Can a store survive negative first-order profit on Meta Ads?", "Only if you have verified 60-to-90-day repeat purchase LTV and enough working capital cash to float the payback period without running dry."),
        ],
    },
}


def build_llms_txt(base_url: str, routes: list) -> str:
    """Generate concise `/llms.txt` index per the 2026 GEO specification."""
    lines = [
        "# IdeaStress",
        "",
        "> Open-source, deterministic Business-as-Code feasibility, reverse unit-economics solver, 1,000-run Monte Carlo simulator, real Google Ads CPC falsifier, and 10-in-1 free startup calculator suite for founders and AI coding agents (MCP & CLI).",
        "",
        "## Free No-Signup Calculators",
        "",
    ]
    for slug, label, title, desc, _ in routes:
        url = f"{base_url}/" if slug == "" else f"{base_url}/{slug}/"
        lines.append(f"- [{label}]({url}): {desc}")

    lines += [
        "",
        "## Key 2025-2026 Cited Industry Base Rates Used by IdeaStress",
        "- SaaS Monthly Churn: 6.2% median (ARPA < $25), 2.6% median (ARPA > $1,000) — ChartMogul (Nov 2026): https://chartmogul.com/benchmarks/",
        "- Private SaaS Benchmarks: 80% software gross margin median, 16-month CAC payback, 4.1x LTV:CAC — Benchmarkit / SubscriptionPlaybook (2026): https://www.subscriptionplaybook.com/benchmarks/",
        "- Indie SaaS Revenue Base Rate: $145 median MRR across 3,700+ startups (23.6% > $1K MRR, 6.1% > $10K MRR) — TrustMRR / BigIdeasDB (Sep 2026): https://bigideasdb.com/dimeadozen-alternative",
        "- US Payment Fees: Stripe US domestic cards 2.9% + $0.30 (https://stripe.com/pricing); Merchant of Record (Paddle/Lemon Squeezy) 5% + $0.50",
        "- E-Commerce Benchmarks: 1.4% Shopify median CVR (top 20% > 2.7%, Littledata Nov 2026); $53–$91 blended ecommerce CAC (First Page Sage 2026)",
        "",
        "## Open-Source CLI & MCP Server (12 Tools)",
        "- Install: `pip install ideastress`",
        "- Start MCP Server (Claude Code / Cursor / Codex): `ideastress mcp`",
        "- Core MCP tools: `precode_gate_check`, `solve_unit_frontiers`, `auto_fix_unit_economics`, `scan_repo_api_costs`, `falsify_paid_channel`, `scan_geo_arbitrage`, `check_scope_creep_finops`, `stress_test_ai_margin`, `generate_kill_test_kit`, `scan_competitor_complaints`, `diff_assumption_ledger`, `get_industry_base_rates`.",
        "",
        f"## Full Reference",
        f"- [llms-full.txt]({base_url}/llms-full.txt): Complete formulas, worked examples, and FAQs for all 10 calculators.",
    ]
    return "\n".join(lines) + "\n"


def build_llms_full_txt(base_url: str, routes: list) -> str:
    """Generate comprehensive `/llms-full.txt` with all formulas, worked examples, and FAQs."""
    parts = [build_llms_txt(base_url, routes), "\n# Detailed Formulas, Worked Examples & FAQs\n"]
    seen = set()
    for slug, label, title, desc, key in routes:
        if key in seen or key not in TOOL_GEO_CONTENT:
            continue
        seen.add(key)
        c = TOOL_GEO_CONTENT[key]
        url = f"{base_url}/" if slug == "" else f"{base_url}/{slug}/"
        parts.append(f"## {c['name']}\nURL: {url}\n")
        parts.append("### Exact Formula\n```text\n" + c["formula"] + "\n```\n")
        parts.append(f"### Worked Example\n{c['worked_example']}\n")
        parts.append("### Frequently Asked Questions")
        for q, a in c["faqs"]:
            parts.append(f"- **Q: {q}**\n  A: {a}")
        parts.append("")
    return "\n".join(parts) + "\n"
