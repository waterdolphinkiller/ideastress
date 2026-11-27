"""Provider package exports."""

from ideastress.providers.interfaces import (
    FetchedPage,
    FetchProvider,
    LLMProvider,
    SearchProvider,
    SearchResult,
)
from ideastress.providers.mock import MockFetchProvider, MockLLMProvider, MockSearchProvider
from ideastress.providers.openai_compat import OpenAICompatibleLLMProvider, TavilySearchProvider
from ideastress.providers.safe_fetch import SafeHTTPFetcher, validate_safe_url
from ideastress.providers.signals import (
    AppStoreSignalAdapter,
    ComplaintSignal,
    G2SignalAdapter,
    MockSignalAdapter,
    RedditSignalAdapter,
    aggregate_pain_themes,
    collect_complaint_signals,
)

__all__ = [
    "AppStoreSignalAdapter",
    "ComplaintSignal",
    "FetchedPage",
    "FetchProvider",
    "G2SignalAdapter",
    "LLMProvider",
    "MockFetchProvider",
    "MockLLMProvider",
    "MockSearchProvider",
    "MockSignalAdapter",
    "OpenAICompatibleLLMProvider",
    "RedditSignalAdapter",
    "SafeHTTPFetcher",
    "SearchProvider",
    "SearchResult",
    "TavilySearchProvider",
    "aggregate_pain_themes",
    "collect_complaint_signals",
    "validate_safe_url",
]
