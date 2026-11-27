"""Unit tests for IdeaStress v0.8.0 calculators (Quit-Job MRR, Freemium Drag, Paid Social CPM)."""

import unittest
from decimal import Decimal

from ideastress.finance.calculators import (
    evaluate_freemium_economics,
    evaluate_paid_social_cpm,
    solve_quit_job_mrr,
)


class TestV08Calculators(unittest.TestCase):
    def test_quit_job_mrr_and_stripe_vs_mor(self):
        res = solve_quit_job_mrr(
            target_annual_salary_usd=Decimal("120000"),
            effective_tax_rate=Decimal("0.30"),
            monthly_operating_costs_usd=Decimal("1500"),
            unit_price_usd=Decimal("49"),
            payment_processor="stripe_us",
        )
        self.assertGreater(res.required_mrr_usd, Decimal("16000"))
        self.assertGreater(res.annual_mor_fees_usd, res.annual_stripe_fees_usd)
        self.assertGreater(res.annual_fee_savings_with_stripe_usd, Decimal("4000"))

    def test_freemium_bleeding_when_free_ai_cost_is_high(self):
        bad = evaluate_freemium_economics(
            total_monthly_active_users=10000,
            free_to_paid_conversion_rate=Decimal("0.015"),
            paid_price_usd=Decimal("29"),
            monthly_cost_per_free_user_usd=Decimal("0.60"),
            monthly_cost_per_paid_user_usd=Decimal("4.00"),
        )
        self.assertEqual(bad.verdict, "FREEMIUM_BLEEDING")
        self.assertLess(bad.monthly_net_gross_profit_usd, Decimal("0"))

        good = evaluate_freemium_economics(
            total_monthly_active_users=10000,
            free_to_paid_conversion_rate=Decimal("0.04"),
            paid_price_usd=Decimal("39"),
            monthly_cost_per_free_user_usd=Decimal("0.10"),
            monthly_cost_per_paid_user_usd=Decimal("3.00"),
        )
        self.assertEqual(good.verdict, "FREEMIUM_HEALTHY")

    def test_paid_social_cpm_funnel_math(self):
        res = evaluate_paid_social_cpm(
            cpm_usd=Decimal("18"),
            ctr_pct=Decimal("1.2"),
            landing_cvr_pct=Decimal("2.5"),
            aov_usd=Decimal("68"),
            pre_ad_margin_pct=Decimal("60"),
        )
        self.assertEqual(res.effective_cpc_usd, Decimal("1.50"))
        self.assertEqual(res.implied_cpa_usd, Decimal("60.00"))
        self.assertEqual(res.verdict, "SOCIAL_UNPROFITABLE")


if __name__ == "__main__":
    unittest.main()
