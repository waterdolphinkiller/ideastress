"""Geo-Arbitrage Cross-Country CPC & Survival Scanner (US / UK / DE / SG / MY).

Exposes blue-ocean international opportunities where an idea is mathematically dead
in crowded US Google Ads ($8+ CPC) yet highly viable in lower-CPC markets.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel

from ideastress.finance.engine import q2
from ideastress.providers.cpc import CPCProvider, MockCPCProvider, evaluate_paid_channel_falsification
from ideastress.storage.cache import SQLiteSignalCache


@dataclass(frozen=True)
class MarketProfile:
    code: str
    name: str
    location_code: int
    mock_cpc_factor: Decimal  # Relative CPC ratio vs US baseline in offline mock mode
    purchasing_power_factor: Decimal  # Realistic localized pricing ratio vs US


MARKETS: Dict[str, MarketProfile] = {
    "US": MarketProfile("US", "United States", 2840, Decimal("1.00"), Decimal("1.00")),
    "UK": MarketProfile("UK", "United Kingdom", 2826, Decimal("0.72"), Decimal("0.95")),
    "DE": MarketProfile("DE", "Germany (DACH)", 2276, Decimal("0.58"), Decimal("0.92")),
    "SG": MarketProfile("SG", "Singapore", 2702, Decimal("0.52"), Decimal("0.90")),
    "MY": MarketProfile("MY", "Malaysia", 2458, Decimal("0.26"), Decimal("0.55")),
}


class GeoMarketResult(BaseModel):
    market_code: str
    market_name: str
    location_code: int
    weighted_avg_cpc_usd: Decimal
    implied_paid_cac_usd: Decimal
    localized_max_viable_cac_usd: Decimal
    required_cvr_pct: Optional[Decimal] = None
    verdict: str  # CHANNEL_VIABLE | CHANNEL_TIGHT | CHANNEL_IMPOSSIBLE
    arbitrage_score: Decimal  # localized_max_viable_cac / implied_paid_cac (>1.0 = profitable headroom)


class GeoArbitrageReport(BaseModel):
    keywords: List[str]
    us_max_viable_cac_usd: Decimal
    assumed_conversion_rate_pct: Decimal
    best_market: str
    markets: List[GeoMarketResult]
    summary: str


class _LocalizedMockCPCProvider:
    """Scales MockCPCProvider baseline by realistic country CPC ratio for offline demos/tests."""

    name = "mock_cpc_localized"

    def __init__(self, factor: Decimal) -> None:
        self.factor = factor
        self._base = MockCPCProvider()

    def fetch_keyword_cpc(self, keywords: List[str], *, location_code: int = 2840, language_code: str = "en"):
        rows = self._base.fetch_keyword_cpc(keywords, location_code=location_code, language_code=language_code)
        for r in rows:
            r.cpc_low = q2(r.cpc_low * self.factor)
            r.cpc_avg = q2(r.cpc_avg * self.factor)
            r.cpc_high = q2(r.cpc_high * self.factor)
        return rows


def scan_geo_arbitrage(
    keywords: List[str],
    *,
    us_max_viable_cac_usd: Decimal,
    assumed_conversion_rate: Decimal = Decimal("0.025"),
    market_codes: Optional[List[str]] = None,
    live_provider: Optional[CPCProvider] = None,
    cache: Optional[SQLiteSignalCache] = None,
) -> GeoArbitrageReport:
    """Compare paid search viability across 5 countries simultaneously."""
    codes = market_codes or ["US", "UK", "DE", "SG", "MY"]
    results: List[GeoMarketResult] = []

    for code in codes:
        mp = MARKETS.get(code.upper())
        if not mp:
            continue
        loc_max_cac = q2(us_max_viable_cac_usd * mp.purchasing_power_factor)
        prov = live_provider if live_provider is not None else _LocalizedMockCPCProvider(mp.mock_cpc_factor)
        res = evaluate_paid_channel_falsification(
            keywords,
            max_viable_cac=loc_max_cac,
            assumed_conversion_rate=assumed_conversion_rate,
            provider=prov,
            cache=cache,
            location_code=mp.location_code,
        )
        score = q2(loc_max_cac / res.implied_paid_cac) if res.implied_paid_cac > Decimal("0") else Decimal("0.00")
        results.append(
            GeoMarketResult(
                market_code=mp.code,
                market_name=mp.name,
                location_code=mp.location_code,
                weighted_avg_cpc_usd=res.weighted_avg_cpc,
                implied_paid_cac_usd=res.implied_paid_cac,
                localized_max_viable_cac_usd=loc_max_cac,
                required_cvr_pct=res.required_conversion_rate_for_cpc_pct,
                verdict=res.verdict,
                arbitrage_score=score,
            )
        )

    results.sort(key=lambda r: r.arbitrage_score, reverse=True)
    best = results[0] if results else None
    us_row = next((r for r in results if r.market_code == "US"), None)

    if best and us_row and us_row.verdict == "CHANNEL_IMPOSSIBLE" and best.verdict != "CHANNEL_IMPOSSIBLE":
        summary = (
            f"GEO-ARBITRAGE OPPORTUNITY: Paid ads fail in US (CPC ${us_row.weighted_avg_cpc_usd}, {us_row.verdict}), "
            f"but {best.market_name} ({best.market_code}) clears at ${best.weighted_avg_cpc_usd} CPC ({best.verdict}, score {best.arbitrage_score}x)."
        )
    elif best:
        summary = (
            f"Best paid-search headroom is {best.market_name} ({best.market_code}) with ${best.weighted_avg_cpc_usd} CPC, "
            f"implied CAC ${best.implied_paid_cac_usd} vs localized ceiling ${best.localized_max_viable_cac_usd} ({best.verdict})."
        )
    else:
        summary = "No markets evaluated."

    return GeoArbitrageReport(
        keywords=keywords,
        us_max_viable_cac_usd=q2(us_max_viable_cac_usd),
        assumed_conversion_rate_pct=q2(assumed_conversion_rate * Decimal("100")),
        best_market=best.market_code if best else "N/A",
        markets=results,
        summary=summary,
    )
