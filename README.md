# IdeaStress v0.2.0

![IdeaStress v0.8.1 Interactive Demo](assets/ideastress_demo.gif)

**Stress-test your business idea with deterministic math, real competitor complaint signals, 2026 industry base rates, and an independent Red Team — before you write code or spend cash.**

> Open-source, Business-as-Code feasibility & falsification engine for indie hackers, founders, and AI coding agents (Claude Code, Cursor, Codex).

## What's Inside v0.2.0

1. **Reverse Unit-Economics Solver (Goal-Seek Survival Frontier)**: Computes exact `max_viable_cac`, `min_viable_unit_price`, `max_tolerable_monthly_churn_pct`, and `min_monthly_new_customers_to_survive` in Python `Decimal`.
2. **Competitor Complaint Signal Adapters (Reddit / App Store / G2)**: Extracts real 1–3 star App Store reviews, Reddit complaint threads, and G2 cons with automated pain-theme clustering (`pricing_and_billing`, `ux_and_complexity`, `missing_features`, `reliability_and_bugs`, `customer_support`) and SSRF protection.
3. **Git-Friendly Assumption Ledger (`venture.yaml` + `diff`)**: Version-control business assumptions and run `ideastress diff` after live ad/interview experiments to see exact cash and verdict shifts.
4. **10-Case Industry Benchmark Suite**: Automated quality harness covering 10 business archetypes with verified 100% pass rate, 0.0% unsupported `VERIFIED` claim rate, and 100% Kill-Test coverage (`python3 scripts/run_benchmark.py`).
5. **Public SEO Free Calculator Matrix (`web/index.html`)**: Zero-dependency, no-signup interactive web app with 5 calculators (Reverse Frontier Solver, Break-Even, SaaS LTV/CAC, E-Commerce ROAS Floor, Runway Stress-Tester), JSON-LD SEO schema, and one-click `venture.yaml` export.
6. **Zero-Dependency JSON-RPC 2.0 MCP Server**: Exposes `precode_gate_check`, `solve_unit_frontiers`, `scan_competitor_complaints`, `diff_assumption_ledger`, and `get_industry_base_rates` for Claude Code / Cursor / Codex.

## Quickstart

```bash
pip install -e .

ideastress doctor
ideastress solve --type saas --price 49 --var-cost 6 --fixed-cost 900 --new-customers 14 --acq-spend 560 --churn 0.05 --cash 12000
ideastress signals "QuickBooks accounting"
ideastress analyze --input examples/saas_accounting.yaml --format html --out report.html
ideastress diff examples/saas_accounting.yaml examples/saas_accounting_after_test.yaml
ideastress benchmark-run
```

## License

MIT
