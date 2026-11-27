"""Industry base rates package."""

from ideastress.benchmarks.base_rates import (
    INDUSTRY_BASE_RATES,
    BenchmarkRecord,
    calibrate_against_base_rates,
    get_base_rates_for,
)

__all__ = [
    "INDUSTRY_BASE_RATES",
    "BenchmarkRecord",
    "calibrate_against_base_rates",
    "get_base_rates_for",
]
