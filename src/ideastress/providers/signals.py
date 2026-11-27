"""Competitor Complaint & Pain-Point Signal Adapters (Reddit, App Store, G2).

Extracts real qualitative demand & dissatisfaction signals from public endpoints:
  - Reddit public search JSON API
  - Apple iTunes Search API + App Store public RSS customer reviews JSON
  - G2 / review discovery via SearchProvider + SSRF-safe fetch (never bypasses captchas/paywalls)
  - Offline MockSignalAdapter for deterministic CI & zero-network demos

All signals are tagged `SourceReliability.QUALITATIVE` and converted into
traceable `Evidence` entries in `EvidenceStore`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol
from urllib.parse import quote_plus

import httpx

from ideastress.domain.models import Evidence, SourceReliability, utc_now_iso
from ideastress.providers.interfaces import SearchProvider
from ideastress.providers.safe_fetch import validate_safe_url
from ideastress.storage.cache import SQLiteSignalCache

PAIN_TAXONOMY: Dict[str, List[str]] = {
    "pricing_and_billing": ["expensive", "overpriced", "price hike", "billing", "cancel", "refund", "hidden fee", "too much"],
    "missing_features": ["missing", "wish it had", "no support for", "doesn't integrate", "lacks", "need a way to"],
    "ux_and_complexity": ["clunky", "confusing", "bloated", "hard to use", "steep learning curve", "slow", "overkill"],
    "reliability_and_bugs": ["crash", "bug", "broken", "sync failed", "downtime", "lost data", "glitch"],
    "customer_support": ["support", "no response", "unhelpful", "ticket", "ghosted", "terrible service"],
}


def classify_pain_tags(text: str) -> List[str]:
    lower = text.lower()
    tags = [
        theme
        for theme, keywords in PAIN_TAXONOMY.items()
        if any(kw in lower for kw in keywords)
    ]
    return tags or ["general_friction"]


@dataclass
class ComplaintSignal:
    platform: str  # reddit | app_store | g2
    title: str
    excerpt: str
    url: str
    rating: Optional[int] = None  # 1-5 for App Store / G2, None for Reddit
    pain_tags: List[str] = field(default_factory=list)
    retrieved_at: str = field(default_factory=utc_now_iso)
    access_status: str = "success"

    def to_evidence(self) -> Evidence:
        rating_note = f" (rating: {self.rating}/5)" if self.rating is not None else ""
        return Evidence(
            source_type=f"{self.platform}_complaint_signal",
            title=f"[{self.platform.upper()}{rating_note}] {self.title[:120]}",
            url=self.url,
            publisher=self.platform,
            retrieved_at=self.retrieved_at,
            snippet=self.excerpt[:450],
            source_reliability=SourceReliability.QUALITATIVE,
            access_status=self.access_status,
            limitations=[
                "Qualitative user complaint signal; indicates friction but does not prove aggregate willingness to pay."
            ],
        )


class SignalAdapter(Protocol):
    name: str

    def fetch_complaints(self, query: str, *, limit: int = 5) -> List[ComplaintSignal]: ...


class RedditSignalAdapter:
    """Fetches public Reddit complaint discussions via Reddit's public JSON search."""

    name = "reddit_public"

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch_complaints(self, query: str, *, limit: int = 5) -> List[ComplaintSignal]:
        q = quote_plus(f"{query} (alternative OR frustrating OR overpriced OR hate OR cancel)")
        url = f"https://www.reddit.com/search.json?q={q}&sort=relevance&limit={min(limit, 15)}"
        validate_safe_url(url, resolve_dns=True)
        headers = {"User-Agent": "IdeaStress-SignalBot/0.2 (open-source research)"}
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code != 200:
                    return []
                children = resp.json().get("data", {}).get("children", [])
                signals: List[ComplaintSignal] = []
                for item in children[:limit]:
                    d = item.get("data", {})
                    title = d.get("title", "").strip()
                    body = (d.get("selftext") or "").strip()
                    permalink = d.get("permalink", "")
                    if not title or not permalink:
                        continue
                    excerpt = re.sub(r"\s+", " ", f"{title}. {body}")[:420]
                    signals.append(
                        ComplaintSignal(
                            platform="reddit",
                            title=title,
                            excerpt=excerpt,
                            url=f"https://www.reddit.com{permalink}",
                            pain_tags=classify_pain_tags(excerpt),
                        )
                    )
                return signals
        except Exception:
            return []


class AppStoreSignalAdapter:
    """Fetches real 1-to-3 star App Store complaints via Apple's official iTunes + RSS JSON feeds."""

    name = "app_store_rss"

    def __init__(self, country: str = "us", timeout_seconds: float = 10.0) -> None:
        self.country = country
        self.timeout_seconds = timeout_seconds

    def fetch_complaints(self, query: str, *, limit: int = 5) -> List[ComplaintSignal]:
        search_url = f"https://itunes.apple.com/search?term={quote_plus(query)}&country={self.country}&entity=software&limit=2"
        validate_safe_url(search_url, resolve_dns=True)
        signals: List[ComplaintSignal] = []
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                s_resp = client.get(search_url)
                if s_resp.status_code != 200:
                    return []
                apps = s_resp.json().get("results", [])
                for app in apps[:2]:
                    track_id = app.get("trackId")
                    track_name = app.get("trackName", "App")
                    track_url = app.get("trackViewUrl", f"https://apps.apple.com/{self.country}/app/id{track_id}")
                    if not track_id:
                        continue
                    rss_url = f"https://itunes.apple.com/{self.country}/rss/customerreviews/id={track_id}/sortBy=mostRecent/json"
                    validate_safe_url(rss_url, resolve_dns=True)
                    r_resp = client.get(rss_url)
                    if r_resp.status_code != 200:
                        continue
                    entries = r_resp.json().get("feed", {}).get("entry", [])
                    if isinstance(entries, dict):
                        entries = [entries]
                    for entry in entries:
                        rating_raw = entry.get("im:rating", {}).get("label")
                        if not rating_raw:
                            continue
                        rating = int(rating_raw)
                        if rating > 3:
                            continue  # Focus on 1-3 star dissatisfaction signals
                        r_title = entry.get("title", {}).get("label", "").strip()
                        r_body = entry.get("content", {}).get("label", "").strip()
                        excerpt = re.sub(r"\s+", " ", f"[{track_name}] {r_title}: {r_body}")[:420]
                        signals.append(
                            ComplaintSignal(
                                platform="app_store",
                                title=f"{track_name}: {r_title}",
                                excerpt=excerpt,
                                url=track_url,
                                rating=rating,
                                pain_tags=classify_pain_tags(excerpt),
                            )
                        )
                        if len(signals) >= limit:
                            return signals
        except Exception:
            return []
        return signals


class G2SignalAdapter:
    """Discovers public G2/Capterra review snippets via SearchProvider (respects anti-bot & ToS)."""

    name = "g2_discovery"

    def __init__(self, search_provider: SearchProvider) -> None:
        self.search_provider = search_provider

    def fetch_complaints(self, query: str, *, limit: int = 4) -> List[ComplaintSignal]:
        q = f'site:g2.com/products "{query}" reviews cons OR pricing OR alternatives'
        results = self.search_provider.search(q, limit=limit)
        signals: List[ComplaintSignal] = []
        for r in results[:limit]:
            if not r.url:
                continue
            signals.append(
                ComplaintSignal(
                    platform="g2",
                    title=r.title,
                    excerpt=r.snippet[:420],
                    url=r.url,
                    pain_tags=classify_pain_tags(f"{r.title} {r.snippet}"),
                )
            )
        return signals


class MockSignalAdapter:
    """Deterministic offline complaint signal adapter across Reddit, G2, and App Store."""

    name = "mock_signals"

    def fetch_complaints(self, query: str, *, limit: int = 6) -> List[ComplaintSignal]:
        q = query.lower()
        if any(k in q for k in ("accounting", "bookkeeping", "invoice", "tax", "saas")):
            pool = [
                ComplaintSignal(
                    platform="reddit",
                    title="QuickBooks Online price hike again — any simple alternative for solo freelancers?",
                    excerpt="Paying $35+/mo just to categorize 40 bank transactions and send 5 invoices feels overpriced and bloated for a 1-person business.",
                    url="https://www.reddit.com/r/freelance/comments/example_qb_pricing/",
                    pain_tags=["pricing_and_billing", "ux_and_complexity"],
                ),
                ComplaintSignal(
                    platform="g2",
                    title="Xero Reviews: Cons & Steep Learning Curve for Non-Accountants",
                    excerpt="Users report bank feed sync delays and confusing reconciliation screens when operating without a dedicated bookkeeper.",
                    url="https://www.g2.com/products/xero/reviews",
                    rating=3,
                    pain_tags=["ux_and_complexity", "reliability_and_bugs"],
                ),
                ComplaintSignal(
                    platform="app_store",
                    title="Wave Invoicing: Support ticket ghosted after Pro upgrade",
                    excerpt="App works fine for basic receipts, but customer support took 9 days to answer a payout hold question.",
                    url="https://apps.apple.com/us/app/wave-invoicing/id881629660",
                    rating=2,
                    pain_tags=["customer_support", "pricing_and_billing"],
                ),
            ]
        elif any(k in q for k in ("supplement", "ecommerce", "shopify", "dropshipping", "store")):
            pool = [
                ComplaintSignal(
                    platform="reddit",
                    title="Tired of supplement brands hiding subscription cancel buttons",
                    excerpt="Ordered a trial bottle and got billed $79 again with no reminder; had to email support twice to get a refund.",
                    url="https://www.reddit.com/r/Supplements/comments/example_sub_cancel/",
                    pain_tags=["pricing_and_billing", "customer_support"],
                ),
                ComplaintSignal(
                    platform="app_store",
                    title="Sleep Tracker & Supplement App: Expensive refill pricing",
                    excerpt="Product works decently but shipping delays and overpriced monthly refills made me switch to generic magnesium.",
                    url="https://apps.apple.com/us/app/example-sleep-brand/id123456789",
                    rating=2,
                    pain_tags=["pricing_and_billing"],
                ),
            ]
        else:
            pool = [
                ComplaintSignal(
                    platform="reddit",
                    title="Local service marketplaces charge high lead fees with low show-up rates",
                    excerpt="Contractors complain about paying $20-$45 per lead on Thumbtack/Angi where customers ghost or only shop lowest price.",
                    url="https://www.reddit.com/r/sweatystartup/comments/example_lead_fees/",
                    pain_tags=["pricing_and_billing", "customer_support"],
                ),
                ComplaintSignal(
                    platform="g2",
                    title="Field Service Scheduling Reviews: Clunky mobile app for small teams",
                    excerpt="Small 3-person crews say enterprise scheduling tools are overkill and hard to use on mobile.",
                    url="https://www.g2.com/categories/field-service-management",
                    rating=3,
                    pain_tags=["ux_and_complexity"],
                ),
            ]
        return pool[:limit]


def aggregate_pain_themes(signals: List[ComplaintSignal]) -> Dict[str, int]:
    """Count complaint frequency by pain theme for Red Team & differentiation synthesis."""
    counts: Dict[str, int] = {}
    for sig in signals:
        for tag in sig.pain_tags:
            counts[tag] = counts.get(tag, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


def collect_complaint_signals(
    query: str,
    *,
    mode: str = "mock",
    search_provider: Optional[SearchProvider] = None,
    limit_per_platform: int = 3,
    cache: Optional[SQLiteSignalCache] = None,
    ttl_days: float = 7.0,
) -> List[ComplaintSignal]:
    """Collect competitor complaint signals with optional 7-day SQLite caching."""
    cache_key = f"{mode}::{query.strip().lower()}::{limit_per_platform}"
    if cache is not None:
        cached, hit = cache.get("complaint_signals", cache_key)
        if hit and isinstance(cached, list):
            return [ComplaintSignal(**item) for item in cached]

    if mode == "mock":
        all_signals = MockSignalAdapter().fetch_complaints(query, limit=limit_per_platform * 2)
    else:
        all_signals = []
        all_signals.extend(RedditSignalAdapter().fetch_complaints(query, limit=limit_per_platform))
        all_signals.extend(AppStoreSignalAdapter().fetch_complaints(query, limit=limit_per_platform))
        if search_provider is not None:
            all_signals.extend(G2SignalAdapter(search_provider).fetch_complaints(query, limit=limit_per_platform))

    if cache is not None and all_signals:
        cache.set(
            "complaint_signals",
            cache_key,
            [
                {
                    "platform": s.platform,
                    "title": s.title,
                    "excerpt": s.excerpt,
                    "url": s.url,
                    "rating": s.rating,
                    "pain_tags": s.pain_tags,
                    "retrieved_at": s.retrieved_at,
                    "access_status": s.access_status,
                }
                for s in all_signals
            ],
            ttl_days=ttl_days,
        )
    return all_signals
