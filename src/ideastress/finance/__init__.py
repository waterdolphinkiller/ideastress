"""Deterministic financial engine and reverse unit-economics solver."""

from ideastress.finance.engine import (
    run_full_financial_analysis,
    run_scenario,
    run_sensitivity_analysis,
    validate_financial_inputs,
)
from ideastress.finance.solver import solve_reverse_frontier

__all__ = [
    "run_full_financial_analysis",
    "run_scenario",
    "run_sensitivity_analysis",
    "solve_reverse_frontier",
    "validate_financial_inputs",
]
