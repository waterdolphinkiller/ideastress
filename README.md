# IdeaStress v0.8.1

**Falsify the math _before_ you write the code.**

**[Live 10-in-1 Workbench](https://waterdolphinkiller.github.io/ideastress/)** · **[12-Tool MCP Server](#12-tool-mcp-server-claude-code--cursor--codex)** · **[GitHub Action CI Gate](#github-action-ai-cost--finops-ci-gate)** · **[MIT License](LICENSE)** · `47/47 Tests Passing`

![IdeaStress v0.8.1 Interactive Demo](assets/ideastress_demo.gif)

> Open-source **Business-as-Code** financial falsification engine for indie hackers, founders, and AI coding agents. Run 1,000-path deterministic Monte Carlo survival simulations, reverse-solve your Max Viable CAC, audit repositories for uncapped LLM token loops, or use all 10 interactive calculators free in the browser.

## Live 10-Calculator Matrix (Free · Zero-Backend · No Signup)

Open the **[Flagship 10-in-1 Interactive Workbench](https://waterdolphinkiller.github.io/ideastress/)** or jump straight to any standalone calculator (each includes a 3-Step Quick Guide, Exact Formula, Worked Example, and 4 FAQs):

| # | Calculator | What It Falsifies | Live URL |
| :-: | :--- | :--- | :--- |
| 01 | **Reverse Survival Frontier & Monte Carlo** | 1,000-run survival %, Max Viable CAC, Auto-Fix rescue price & Google Ads CPC check | [Open Reverse CAC](https://waterdolphinkiller.github.io/ideastress/reverse-cac-calculator/) |
| 02 | **Quit-Your-Job MRR Calculator** | Exact MRR & customers needed to replace take-home salary (Stripe US vs MoR + taxes) | [Open Quit-Job MRR](https://waterdolphinkiller.github.io/ideastress/quit-job-mrr-calculator/) |
| 03 | **Freemium vs. Free-Trial Drag** | Whether free-tier hosting & AI token costs wipe out paid subscription margin | [Open Freemium Drag](https://waterdolphinkiller.github.io/ideastress/freemium-economics-calculator/) |
| 04 | **Meta / TikTok CPM Funnel** | Full paid-social math from CPM → CTR → CPC → CVR → CPA & first-order ROAS | [Open Social CPM](https://waterdolphinkiller.github.io/ideastress/meta-tiktok-cpm-calculator/) |
| 05 | **AI Wrapper Token Margin & Whale Limit** | Real LLM inference COGS & exact daily prompt threshold where power users lose money | [Open AI Margin](https://waterdolphinkiller.github.io/ideastress/ai-token-margin-calculator/) |
| 06 | **5-Country Geo-Arbitrage CPC Scanner** | Localized paid-search CPC & CAC headroom across US, UK, Germany, Singapore & Malaysia | [Open Geo-Arbitrage](https://waterdolphinkiller.github.io/ideastress/geo-arbitrage-cpc-scanner/) |
| 07 | **Break-Even Calculator (Stripe / MoR)** | Exact break-even units & monthly revenue after payment processing and refund rates | [Open Break-Even](https://waterdolphinkiller.github.io/ideastress/break-even-calculator/) |
| 08 | **SaaS LTV / CAC & Payback** | Gross-margin-adjusted LTV, LTV:CAC ratio, and payback months vs. 2026 benchmarks | [Open SaaS LTV/CAC](https://waterdolphinkiller.github.io/ideastress/saas-ltv-cac-calculator/) |
| 09 | **E-Commerce Profit & Break-Even ROAS** | Pre-ad contribution margin, Break-Even ROAS floor, and first-order net profit | [Open E-Com ROAS](https://waterdolphinkiller.github.io/ideastress/ecommerce-roas-calculator/) |
| 10 | **Startup Runway & Burn Stress-Tester** | Base runway vs. downside shock (−30% revenue, 50% slower growth, +20% cost overrun) | [Open Runway Tester](https://waterdolphinkiller.github.io/ideastress/startup-runway-calculator/) |

*AI Search & GEO Index:* [`llms.txt`](https://waterdolphinkiller.github.io/ideastress/llms.txt) · [`llms-full.txt`](https://waterdolphinkiller.github.io/ideastress/llms-full.txt)

## GitHub Action (AI Cost & FinOps CI Gate)

Automatically audit every Pull Request for uncapped LLM SDK calls inside loops, missing `max_tokens` limits, and negative AI wrapper unit margins:

```yaml
name: IdeaStress FinOps Gate
on: [pull_request]

jobs:
  ai-cost-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: waterdolphinkiller/ideastress@v0.8.1
        with:
          path: "."
          price: "29"
          fail-on-high-risk: "false"
```

## Quickstart (CLI & MCP)

```bash
pip install -e .

# 1. Verify environment
ideastress doctor

# 2. Reverse-solve Max Viable CAC & 1,000-run Monte Carlo survival
ideastress solve --type saas --price 49 --var-cost 6 --fixed-cost 900 \
  --new-customers 14 --acq-spend 560 --churn 0.05 --cash 12000

# 3. Scan a real codebase for uncapped OpenAI/Anthropic/Google SDK token loops
ideastress scan-repo ./my-saas --price 29

# 4. Run 10-case falsification benchmark suite (10/10 pass, 0% unsupported VERIFIED claims)
python3 scripts/run_benchmark.py
```

## 12-Tool MCP Server (Claude Code / Cursor / Codex)

Launch the zero-dependency stdio JSON-RPC 2.0 MCP server:

```bash
ideastress mcp
```

Exposed deterministic tools include `solve_reverse_frontier`, `run_monte_carlo`, `compute_autofix_plan`, `scan_repo_ai_costs`, `scan_geo_arbitrage`, `check_scope_creep`, `quit_job_mrr_calc`, `freemium_drag_calc`, `social_cpm_funnel`, `generate_proof_card`, `diff_venture_ledger`, and `generate_kill_test_kit`.

## License

MIT — preliminary feasibility modeling only (not financial, tax, or legal advice).
