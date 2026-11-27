"""Competitor Pricing Page Drift & Free-Tier Sunset Radar.

Snapshots competitor pricing pages in SQLite (`content_hash`, extracted price points,
and free-tier presence) and detects high-opportunity market shifts:
  - `PRICE_INCREASE` (competitor raised entry/pro prices)
  - `FREE_TIER_REMOVED` (competitor sunsetted their free plan)
  - `CONTENT_CHANGED` (pricing page copy/structure changed)
  - `NO_CHANGE` / `INITIAL_BASELINE`
"""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from ideastress.domain.models import utc_now_iso
from ideastress.storage.cache import SQLiteSignalCache

PRICE_REGEX = re.compile(r"\$\s*(\d+(?:\.\d{1,2})?)")


class PriceSnapshot(BaseModel):
    url: str
    content_hash: str
    extracted_prices_usd: List[str]
    min_price_usd: Optional[str] = None
    has_free_tier: bool
    captured_at: str


class PriceDriftReport(BaseModel):
    url: str
    status: str  # INITIAL_BASELINE | NO_CHANGE | PRICE_INCREASE | FREE_TIER_REMOVED | CONTENT_CHANGED
    previous_min_price: Optional[str] = None
    current_min_price: Optional[str] = None
    previous_has_free_tier: Optional[bool] = None
    current_has_free_tier: bool
    summary: str


def extract_pricing_signals(url: str, text: str) -> PriceSnapshot:
    """Deterministically extract USD price mentions and free-tier signals from a page excerpt."""
    h = "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    raw_prices = sorted({Decimal(m) for m in PRICE_REGEX.findall(text) if Decimal(m) > Decimal("0")})
    lower = text.lower()
    has_free = any(tok in lower for tok in ("free tier", "free plan", "$0/mo", "free forever", "starter free"))
    return PriceSnapshot(
        url=url,
        content_hash=h,
        extracted_prices_usd=[str(p) for p in raw_prices],
        min_price_usd=str(raw_prices[0]) if raw_prices else None,
        has_free_tier=has_free,
        captured_at=utc_now_iso(),
    )


def check_price_drift(url: str, current_text: str, cache: SQLiteSignalCache) -> PriceDriftReport:
    """Compare a competitor pricing page against its last saved SQLite snapshot."""
    curr = extract_pricing_signals(url, current_text)
    prev_raw, hit = cache.get("price_radar", url)

    # Save latest snapshot (365-day retention)
    cache.set("price_radar", url, curr.dict(), ttl_days=365.0)

    if not hit or not isinstance(prev_raw, dict):
        return PriceDriftReport(
            url=url,
            status="INITIAL_BASELINE",
            current_min_price=curr.min_price_usd,
            current_has_free_tier=curr.has_free_tier,
            summary=f"Saved initial pricing baseline for {url} (min price: {curr.min_price_usd or 'N/A'}, free tier: {curr.has_free_tier}).",
        )

    prev = PriceSnapshot(**prev_raw)
    if prev.has_free_tier and not curr.has_free_tier:
        return PriceDriftReport(
            url=url,
            status="FREE_TIER_REMOVED",
            previous_min_price=prev.min_price_usd,
            current_min_price=curr.min_price_usd,
            previous_has_free_tier=prev.has_free_tier,
            current_has_free_tier=curr.has_free_tier,
            summary=f"OPPORTUNITY ALERT: {url} appears to have removed its free tier!",
        )

    if prev.min_price_usd and curr.min_price_usd and Decimal(curr.min_price_usd) > Decimal(prev.min_price_usd):
        return PriceDriftReport(
            url=url,
            status="PRICE_INCREASE",
            previous_min_price=prev.min_price_usd,
            current_min_price=curr.min_price_usd,
            previous_has_free_tier=prev.has_free_tier,
            current_has_free_tier=curr.has_free_tier,
            summary=f"OPPORTUNITY ALERT: {url} raised its entry price from ${prev.min_price_usd} to ${curr.min_price_usd}.",
        )

    if prev.content_hash != curr.content_hash:
        return PriceDriftReport(
            url=url,
            status="CONTENT_CHANGED",
            previous_min_price=prev.min_price_usd,
            current_min_price=curr.min_price_usd,
            previous_has_free_tier=prev.has_free_tier,
            current_has_free_tier=curr.has_free_tier,
            summary=f"Pricing page content changed at {url} (min price unchanged at {curr.min_price_usd or 'N/A'}).",
        )

    return PriceDriftReport(
        url=url,
        status="NO_CHANGE",
        previous_min_price=prev.min_price_usd,
        current_min_price=curr.min_price_usd,
        previous_has_free_tier=prev.has_free_tier,
        current_has_free_tier=curr.has_free_tier,
        summary=f"No pricing changes detected at {url}.",
    )
