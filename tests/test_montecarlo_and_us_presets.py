"""Unit tests for v0.3.0 Monte Carlo Survival Simulator and US Stripe/Tax presets."""

import unittest
from decimal import Decimal

from ideastress.domain.models import BusinessType, FinancialInputs
from ideastress.finance.engine import compute_payment_fee_per_unit, run_full_financial_analysis, run_scenario
from ideastress.finance.montecarlo import run_monte_carlo


class TestMonteCarloAndUSPresets(unittest.TestCase):
    def test_stripe_us_and_mor_fee_presets_exact_math(self):
        # On $100 US domestic card, Stripe 2.9% + $0.30 = $3.20
        f_stripe = FinancialInputs(unit_price=Decimal("100"), payment_processor="stripe_us")
        self.assertEqual(compute_payment_fee_per_unit(f_stripe), Decimal("3.20"))

        # On $100 MoR (Paddle / Lemon Squeezy), 5.0% + $0.50 = $5.50
        f_mor = FinancialInputs(unit_price=Decimal("100"), payment_processor="mor_paddle")
        self.assertEqual(compute_payment_fee_per_unit(f_mor), Decimal("5.50"))

        # Verify unit contribution margin decreases by exact Stripe fee
        base_no_fee = run_scenario(FinancialInputs(unit_price=Decimal("100"), variable_cost_per_unit=Decimal("10"), refund_rate=Decimal("0")))
        base_stripe = run_scenario(FinancialInputs(unit_price=Decimal("100"), variable_cost_per_unit=Decimal("10"), refund_rate=Decimal("0"), payment_processor="stripe_us"))
        self.assertEqual(base_no_fee.unit_contribution_margin - base_stripe.unit_contribution_margin, Decimal("3.20"))

    def test_us_effective_tax_rate_reduces_positive_cash_flow(self):
        inp_no_tax = FinancialInputs(
            business_type=BusinessType.SAAS, unit_price=Decimal("80"),
            variable_cost_per_unit=Decimal("5"), fixed_monthly_costs=Decimal("500"),
            monthly_new_customers=20, monthly_acquisition_spend=Decimal("200"),
            starting_cash=Decimal("10000"), effective_tax_rate=Decimal("0.00"),
        )
        inp_us_corp = FinancialInputs(
            business_type=BusinessType.SAAS, unit_price=Decimal("80"),
            variable_cost_per_unit=Decimal("5"), fixed_monthly_costs=Decimal("500"),
            monthly_new_customers=20, monthly_acquisition_spend=Decimal("200"),
            starting_cash=Decimal("10000"), effective_tax_rate=Decimal("0.21"),
        )
        r0 = run_scenario(inp_no_tax)
        r21 = run_scenario(inp_us_corp)
        self.assertGreater(r0.ending_cash_balance, r21.ending_cash_balance)

    def test_monte_carlo_reproducible_and_distinguishes_risk_tiers(self):
        healthy = FinancialInputs(
            business_type=BusinessType.SAAS, unit_price=Decimal("79"),
            variable_cost_per_unit=Decimal("6"), fixed_monthly_costs=Decimal("800"),
            monthly_new_customers=15, monthly_acquisition_spend=Decimal("400"),
            monthly_churn_rate=Decimal("0.04"), starting_cash=Decimal("20000"),
            payment_processor="stripe_us", effective_tax_rate=Decimal("0.21"),
        )
        fragile = FinancialInputs(
            business_type=BusinessType.SAAS, unit_price=Decimal("15"),
            variable_cost_per_unit=Decimal("12"), fixed_monthly_costs=Decimal("2500"),
            monthly_new_customers=15, monthly_acquisition_spend=Decimal("800"),
            monthly_churn_rate=Decimal("0.12"), starting_cash=Decimal("4000"),
            payment_processor="stripe_us",
        )
        mc1 = run_monte_carlo(healthy, simulations=1000, seed=42)
        mc2 = run_monte_carlo(healthy, simulations=1000, seed=42)
        self.assertEqual(mc1.survival_probability_pct, mc2.survival_probability_pct)
        self.assertEqual(mc1.p50_ending_cash, mc2.p50_ending_cash)
        self.assertEqual(mc1.bankruptcy_risk_label, "LOW_RISK")
        self.assertLessEqual(mc1.p10_ending_cash, mc1.p50_ending_cash)
        self.assertLessEqual(mc1.p50_ending_cash, mc1.p90_ending_cash)

        mc_bad = run_monte_carlo(fragile, simulations=1000, seed=42)
        self.assertEqual(mc_bad.bankruptcy_risk_label, "CRITICAL_RISK")
        self.assertLess(mc_bad.survival_probability_pct, Decimal("20.00"))

        # Full analysis includes Monte Carlo automatically
        full = run_full_financial_analysis(healthy)
        self.assertIsNotNone(full.monte_carlo)
        self.assertEqual(full.monte_carlo.simulations, 1000)


if __name__ == "__main__":
    unittest.main()
