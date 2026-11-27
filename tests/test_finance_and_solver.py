"""Unit tests for deterministic Decimal finance engine & Reverse Unit-Economics Solver."""

import unittest
from decimal import Decimal

from ideastress.benchmarks.base_rates import calibrate_against_base_rates
from ideastress.domain.models import BusinessType, FinancialInputs
from ideastress.exceptions import CurrencyMismatchError, FinancialValidationError
from ideastress.finance.engine import run_full_financial_analysis, run_scenario
from ideastress.finance.solver import solve_reverse_frontier


class TestFinanceEngineAndSolver(unittest.TestCase):
    def test_saas_base_scenario_and_exact_formulas(self):
        inputs = FinancialInputs(
            business_type=BusinessType.SAAS,
            currency="USD",
            unit_price=Decimal("49"),
            variable_cost_per_unit=Decimal("5"),
            fixed_monthly_costs=Decimal("800"),
            monthly_new_customers=15,
            monthly_acquisition_spend=Decimal("600"),
            monthly_churn_rate=Decimal("0.05"),
            refund_rate=Decimal("0.00"),
            starting_cash=Decimal("10000"),
            horizon_months=12,
        )
        res = run_scenario(inputs, "base")
        self.assertEqual(res.unit_contribution_margin, Decimal("44.00"))
        self.assertEqual(res.cac, Decimal("40.00"))
        # LTV = 44 / 0.05 = 880.00
        self.assertEqual(res.ltv, Decimal("880.00"))
        # LTV:CAC = 880 / 40 = 22.00
        self.assertEqual(res.ltv_to_cac, Decimal("22.00"))
        # Break-even = ceil((800 + 600) / 44) = ceil(31.81) = 32
        self.assertEqual(res.break_even_units, 32)
        self.assertEqual(res.break_even_status, "REACHABLE")
        self.assertEqual(len(res.projections), 12)
        self.assertGreater(res.ending_cash_balance, Decimal("10000"))

    def test_negative_unit_margin_triggers_unreachable_and_impossible(self):
        inputs = FinancialInputs(
            business_type=BusinessType.ECOMMERCE,
            currency="USD",
            unit_price=Decimal("20"),
            variable_cost_per_unit=Decimal("25"),
            fixed_monthly_costs=Decimal("1000"),
            monthly_new_customers=50,
            monthly_acquisition_spend=Decimal("500"),
            starting_cash=Decimal("5000"),
        )
        analysis = run_full_financial_analysis(inputs)
        self.assertEqual(
            analysis.scenarios["base"].break_even_status,
            "NOT_REACHABLE_UNDER_CURRENT_ASSUMPTIONS",
        )
        self.assertIsNone(analysis.scenarios["base"].break_even_units)
        self.assertEqual(
            analysis.reverse_frontier.mathematical_verdict,
            "UNIT_ECONOMICS_IMPOSSIBLE",
        )
        self.assertTrue(len(analysis.reverse_frontier.impossibility_reasons) >= 1)

    def test_zero_churn_never_divides_by_zero(self):
        inputs = FinancialInputs(
            business_type=BusinessType.SAAS,
            currency="USD",
            unit_price=Decimal("30"),
            variable_cost_per_unit=Decimal("3"),
            fixed_monthly_costs=Decimal("200"),
            monthly_new_customers=10,
            monthly_churn_rate=Decimal("0"),
            starting_cash=Decimal("5000"),
        )
        res = run_scenario(inputs, "base")
        self.assertIsNone(res.ltv)
        self.assertEqual(res.ltv_status, "REQUIRES_NONZERO_CHURN_DATA")

    def test_marketplace_take_rate_model(self):
        inputs = FinancialInputs(
            business_type=BusinessType.MARKETPLACE,
            currency="MYR",
            unit_price=Decimal("200"),  # average GMV per order
            take_rate=Decimal("0.15"),  # 15% take rate => RM 30 gross rev
            refund_rate=Decimal("0.00"),
            variable_cost_per_unit=Decimal("5"),
            fixed_monthly_costs=Decimal("2000"),
            monthly_new_customers=120,
            monthly_acquisition_spend=Decimal("500"),
            starting_cash=Decimal("15000"),
        )
        res = run_scenario(inputs, "base")
        self.assertEqual(res.unit_contribution_margin, Decimal("25.00"))
        self.assertEqual(res.break_even_units, 100)  # 2500 / 25 = 100

    def test_reverse_frontier_solver_bounds(self):
        inputs = FinancialInputs(
            business_type=BusinessType.SAAS,
            currency="USD",
            unit_price=Decimal("49"),
            variable_cost_per_unit=Decimal("7"),
            fixed_monthly_costs=Decimal("1500"),
            monthly_new_customers=12,
            monthly_acquisition_spend=Decimal("600"),
            monthly_churn_rate=Decimal("0.06"),
            starting_cash=Decimal("12000"),
            horizon_months=12,
        )
        frontier = solve_reverse_frontier(inputs)
        self.assertIsNotNone(frontier.max_viable_cac)
        self.assertGreater(frontier.max_viable_cac, Decimal("50"))
        self.assertIsNotNone(frontier.min_viable_unit_price)
        self.assertLess(frontier.min_viable_unit_price, Decimal("49"))
        self.assertIsNotNone(frontier.max_tolerable_monthly_churn_pct)
        self.assertIsNotNone(frontier.min_monthly_new_customers_to_survive)
        self.assertTrue(len(frontier.hard_rules_for_red_team) >= 4)

    def test_base_rate_calibration_flags_optimistic_ecommerce_cvr(self):
        inputs = FinancialInputs(
            business_type=BusinessType.ECOMMERCE,
            currency="USD",
            unit_price=Decimal("60"),
            variable_cost_per_unit=Decimal("20"),
            fixed_monthly_costs=Decimal("1000"),
            monthly_visitors=2000,
            conversion_rate=Decimal("0.06"),  # 6% is an extreme outlier vs 1.4% Shopify median
            monthly_acquisition_spend=Decimal("1000"),
            starting_cash=Decimal("15000"),
        )
        analysis = run_full_financial_analysis(inputs)
        checks = calibrate_against_base_rates(inputs, analysis)
        statuses = [c.status for c in checks]
        self.assertIn("SEVERE_OUTLIER", statuses)

    def test_validation_guards(self):
        with self.assertRaises(CurrencyMismatchError):
            run_scenario(
                FinancialInputs(currency="US", unit_price=Decimal("10"))
            )
        with self.assertRaises(FinancialValidationError):
            run_scenario(
                FinancialInputs(currency="USD", unit_price=Decimal("-5"))
            )


if __name__ == "__main__":
    unittest.main()
