"""Real CPC -> Implied CAC Paid Channel Falsification Engine (DataForSEO + SQLite Cache + Mock).

Cross-checks the mathematical `max_viable_cac` solved by the Reverse Unit-Economics Frontier
against real Google Ads keyword CPC data:
    implied_paid_cac = volume_weighted_avg_cpc / assumed_conversion_rate
    required_conversion_rate = (volume_weighted_avg_cpc / max_viable_cac) * 100

If `implied_paid_cac > max_viable_cac` or required CVR exceeds 15%, automatically flags
`CHANNEL_IMPOSSIBLE` so founders do not burn cash on mathematically unviable paid ads.
"""

from __future__ import annotations

import base64
from decimal import Decimal
from typing import List, Optional, Protocol

import httpx

from ideastress.domain.models import (
    ChannelFalsificationResult,
    KeywordCPCRecord,
    utc_now_iso,
)
from ideastress.exceptions import ProviderError
from ideastress.finance.engine import q2
from ideastress.providers.safe_fetch import validate_safe_url
from ideastress.storage.cache import SQLiteSignalCache


class CPCProvider(Protocol):
    name: str

    def fetch_keyword_cpc(
        self,
        keywords: List[str],
        *,
        location_code: int = 2840,  # 2840 = United States
        language_code: str = "en",
    ) -> List[KeywordCPCRecord]: ...


class DataForSEOCPCProvider:
    """Live Google Ads CPC & search volume provider via DataForSEO Keywords Data API (~$0.09/live task)."""

    name = "dataforseo_live"
    ENDPOINT = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"

    def __init__(self, login: str, password: str, timeout_seconds: float = 20.0) -> None:
        if not login or not password:
            raise ProviderError("IDEASTESS_DATAFORSEO_LOGIN and IDEASTESS_DATAFORSEO_PASSWORD are required.")
        self.login = login
        self.password = password
        self.timeout_seconds = timeout_seconds

    def fetch_keyword_cpc(
        self,
        keywords: List[str],
        *,
        location_code: int = 2840,
        language_code: str = "en",
    ) -> List[KeywordCPCRecord]:
        validate_safe_url(self.ENDPOINT, resolve_dns=True)
        token = base64.b64encode(f"{self.login}:{self.password}".encode("utf-8")).decode("ascii")
        payload = [
            {
                "keywords": [k.strip() for k in keywords if k.strip()][:20],
                "location_code": location_code,
                "language_code": language_code,
            }
        ]
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.post(
                    self.ENDPOINT,
                    headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                tasks = data.get("tasks") or []
                results: List[KeywordCPCRecord] = []
                for task in tasks:
                    for item in task.get("result") or []:
                        kw = item.get("keyword")
                        if not kw:
                            continue
                        cpc_val = item.get("cpc") or 0.0
                        low_val = item.get("low_top_of_page_bid") or (cpc_val * 0.7)
                        high_val = item.get("high_top_of_page_bid") or (cpc_val * 1.4)
                        vol = int(item.get("search_volume") or 0)
                        comp = str(item.get("competition") or "MEDIUM").upper()
                        results.append(
                            KeywordCPCRecord(
                                keyword=kw,
                                monthly_search_volume=vol,
                                cpc_low=q2(Decimal(str(low_val))),
                                cpc_high=q2(Decimal(str(high_val))),
                                cpc_avg=q2(Decimal(str(cpc_val))),
                                competition_level=comp,
                                currency="USD",
                                location_code=location_code,
                                source=self.name,
                                retrieved_at=utc_now_iso(),
                            )
                        )
                return results
        except Exception as exc:
            raise ProviderError(f"DataForSEO Keywords Data API call failed: {exc}") from exc


class MockCPCProvider:
    """Deterministic US Google Ads CPC reference provider for offline demos and CI tests."""

    name = "mock_cpc"

    def fetch_keyword_cpc(
        self,
        keywords: List[str],
        *,
        location_code: int = 2840,
        language_code: str = "en",
    ) -> List[KeywordCPCRecord]:
        out: List[KeywordCPCRecord] = []
        for kw in keywords:
            ql = kw.lower()
            if any(w in ql for w in ("accounting", "bookkeeping", "tax", "invoice", "payroll")):
                low, avg, high, vol, comp = Decimal("5.40"), Decimal("8.90"), Decimal("14.20"), 14800, "HIGH"
            elif any(w in ql for w in ("crm", "booking", "appointment", "saas", "software")):
                low, avg, high, vol, comp = Decimal("3.80"), Decimal("6.20"), Decimal("10.50"), 9900, "HIGH"
            elif any(w in ql for w in ("supplement", "sleep", "magnesium", "shopify", "dropshipping")):
                low, avg, high, vol, comp = Decimal("1.40"), Decimal("2.45"), Decimal("4.10"), 22200, "HIGH"
            elif any(w in ql for w in ("cleaning", "plumber", "hvac", "local", "service")):
                low, avg, high, vol, comp = Decimal("4.10"), Decimal("6.40"), Decimal("9.80"), 8100, "MEDIUM"
            elif any(w in ql for w in ("resume", "cv", "template", "notion")):
                low, avg, high, vol, comp = Decimal("1.60"), Decimal("2.85"), Decimal("4.60"), 33100, "HIGH"
            else:
                low, avg, high, vol, comp = Decimal("2.20"), Decimal("3.80"), Decimal("6.10"), 5400, "MEDIUM"

            out.append(
                KeywordCPCRecord(
                    keyword=kw,
                    monthly_search_volume=vol,
                    cpc_low=low,
                    cpc_high=high,
                    cpc_avg=avg,
                    competition_level=comp,
                    currency="USD",
                    location_code=location_code,
                    source=self.name,
                    retrieved_at=utc_now_iso(),
                )
            )
        return out


def derive_default_keywords(idea: str, business_type: str) -> List[str]:
    """Derive 2 concise search-intent keywords from an idea string when none are explicitly given."""
    cleaned = " ".join(idea.strip().split()[:6])
    return [cleaned, f"{cleaned} {business_type} pricing"]


def evaluate_paid_channel_falsification(
    keywords: List[str],
    *,
    max_viable_cac: Optional[Decimal],
    assumed_conversion_rate: Decimal = Decimal("0.025"),
    provider: Optional[CPCProvider] = None,
    cache: Optional[SQLiteSignalCache] = None,
    ttl_days: float = 30.0,
    location_code: int = 2840,
) -> ChannelFalsificationResult:
    """Fetch (or read cached) keyword CPCs and test whether paid search can survive max_viable_cac."""
    clean_kws = [k.strip() for k in keywords if k.strip()]
    if not clean_kws:
        raise ProviderError("At least one keyword is required for CPC channel falsification.")
    if assumed_conversion_rate <= Decimal("0") or assumed_conversion_rate > Decimal("1"):
        raise ProviderError("assumed_conversion_rate must be in (0, 1].")

    prov = provider or MockCPCProvider()
    cache_key = f"{location_code}::{'|'.join(sorted(k.lower() for k in clean_kws))}"
    cache_hit = False
    records: List[KeywordCPCRecord] = []

    if cache is not None:
        cached_payload, is_hit = cache.get("keyword_cpc", cache_key)
        if is_hit and isinstance(cached_payload, list):
            cache_hit = True
            records = [KeywordCPCRecord(**item) for item in cached_payload]
            for r in records:
                r.source = "sqlite_cache"

    if not records:
        records = prov.fetch_keyword_cpc(clean_kws, location_code=location_code)
        if cache is not None and records:
            serialized = [
                {
                    "keyword": r.keyword,
                    "monthly_search_volume": r.monthly_search_volume,
                    "cpc_low": str(r.cpc_low),
                    "cpc_high": str(r.cpc_high),
                    "cpc_avg": str(r.cpc_avg),
                    "competition_level": r.competition_level,
                    "currency": r.currency,
                    "location_code": r.location_code,
                    "source": r.source,
                    "retrieved_at": r.retrieved_at,
                }
                for r in records
            ]
            cache.set("keyword_cpc", cache_key, serialized, ttl_days=ttl_days)

    # Compute volume-weighted average CPC
    total_vol = sum(r.monthly_search_volume for r in records)
    if total_vol > 0:
        weighted_cpc = q2(
            sum(r.cpc_avg * Decimal(r.monthly_search_volume) for r in records) / Decimal(total_vol)
        )
    else:
        weighted_cpc = q2(sum(r.cpc_avg for r in records) / Decimal(len(records)))

    implied_cac = q2(weighted_cpc / assumed_conversion_rate)
    assumed_cvr_pct = q2(assumed_conversion_rate * Decimal("100"))

    req_cvr_pct: Optional[Decimal] = None
    if max_viable_cac is not None and max_viable_cac > Decimal("0"):
        req_cvr_pct = q2((weighted_cpc / max_viable_cac) * Decimal("100"))

    # Verdict logic
    if max_viable_cac is None or max_viable_cac <= Decimal("0"):
        verdict = "CHANNEL_IMPOSSIBLE"
        explanation = (
            f"Weighted avg CPC is USD {weighted_cpc:.2f} (implied CAC USD {implied_cac:.2f} at {assumed_cvr_pct}% CVR), "
            "and your Reverse Frontier has $0 CAC headroom. Paid search is mathematically unviable."
        )
    elif implied_cac > max_viable_cac or (req_cvr_pct is not None and req_cvr_pct > Decimal("15.00")):
        verdict = "CHANNEL_IMPOSSIBLE"
        explanation = (
            f"PAID SEARCH FALSIFIED: Weighted avg CPC is USD {weighted_cpc:.2f} -> implied CAC USD {implied_cac:.2f} "
            f"(at {assumed_cvr_pct}% CVR) exceeds your solved max viable CAC of USD {max_viable_cac:.2f}. "
            f"Breaking even on ads would require an unrealistic {req_cvr_pct}% landing-page conversion rate."
        )
    elif implied_cac > max_viable_cac * Decimal("0.75"):
        verdict = "CHANNEL_TIGHT"
        explanation = (
            f"TIGHT PAID MARGIN: Weighted avg CPC USD {weighted_cpc:.2f} -> implied CAC USD {implied_cac:.2f} "
            f"consumes >75% of your USD {max_viable_cac:.2f} max viable CAC ceiling (needs >= {req_cvr_pct}% CVR)."
        )
    else:
        verdict = "CHANNEL_VIABLE"
        explanation = (
            f"PAID SEARCH VIABLE: Weighted avg CPC USD {weighted_cpc:.2f} -> implied CAC USD {implied_cac:.2f} "
            f"fits comfortably under your USD {max_viable_cac:.2f} max viable CAC ceiling (requires >= {req_cvr_pct}% CVR)."
        )

    return ChannelFalsificationResult(
        keywords_analyzed=records,
        weighted_avg_cpc=weighted_cpc,
        assumed_conversion_rate_pct=assumed_cvr_pct,
        implied_paid_cac=implied_cac,
        max_viable_cac=max_viable_cac,
        required_conversion_rate_for_cpc_pct=req_cvr_pct,
        verdict=verdict,
        cache_hit=cache_hit,
        explanation=explanation,
    )
