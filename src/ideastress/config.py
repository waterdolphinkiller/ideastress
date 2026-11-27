"""Environment configuration and secret-safe budget settings for IdeaStress."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class BudgetConfig:
    """Hard execution limits to prevent runaway LLM/search costs."""

    max_search_calls: int = 12
    max_pages_fetched: int = 20
    max_llm_calls: int = 20
    max_runtime_seconds: int = 900
    max_estimated_cost_usd: Decimal = Decimal("2.00")


@dataclass(frozen=True)
class IdeaStressConfig:
    """Application configuration loaded from environment variables."""

    llm_provider: str = "mock"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    search_provider: str = "mock"
    search_api_key: str = ""

    fetch_provider: str = "safe_http"
    cpc_provider: str = "mock"
    dataforseo_login: str = ""
    dataforseo_password: str = ""
    database_path: Path = field(default_factory=lambda: Path("./ideastress.db"))
    cache_db_path: Path = field(default_factory=lambda: Path("./ideastress_cache.db"))
    log_level: str = "INFO"
    budget: BudgetConfig = field(default_factory=BudgetConfig)

    @classmethod
    def from_env(cls) -> IdeaStressConfig:
        """Load configuration from IDEASTESS_* environment variables."""
        db_raw = os.getenv("IDEASTESS_DATABASE_PATH", "./ideastress.db")
        return cls(
            llm_provider=os.getenv("IDEASTESS_LLM_PROVIDER", "mock").strip().lower(),
            llm_api_key=os.getenv("IDEASTESS_LLM_API_KEY", "").strip(),
            llm_base_url=os.getenv("IDEASTESS_LLM_BASE_URL", "https://api.openai.com/v1").strip(),
            llm_model=os.getenv("IDEASTESS_LLM_MODEL", "gpt-4o-mini").strip(),
            search_provider=os.getenv("IDEASTESS_SEARCH_PROVIDER", "mock").strip().lower(),
            search_api_key=os.getenv("IDEASTESS_SEARCH_API_KEY", "").strip(),
            fetch_provider=os.getenv("IDEASTESS_FETCH_PROVIDER", "safe_http").strip().lower(),
            cpc_provider=os.getenv("IDEASTESS_CPC_PROVIDER", "mock").strip().lower(),
            dataforseo_login=os.getenv("IDEASTESS_DATAFORSEO_LOGIN", "").strip(),
            dataforseo_password=os.getenv("IDEASTESS_DATAFORSEO_PASSWORD", "").strip(),
            database_path=Path(db_raw),
            cache_db_path=Path(os.getenv("IDEASTESS_CACHE_DB_PATH", "./ideastress_cache.db")),
            log_level=os.getenv("IDEASTESS_LOG_LEVEL", "INFO").upper(),
            budget=BudgetConfig(
                max_search_calls=int(os.getenv("IDEASTESS_MAX_SEARCH_CALLS", "12")),
                max_pages_fetched=int(os.getenv("IDEASTESS_MAX_PAGES_FETCHED", "20")),
                max_llm_calls=int(os.getenv("IDEASTESS_MAX_LLM_CALLS", "20")),
                max_runtime_seconds=int(os.getenv("IDEASTESS_MAX_RUNTIME_SECONDS", "900")),
                max_estimated_cost_usd=Decimal(os.getenv("IDEASTESS_MAX_ESTIMATED_COST_USD", "2.00")),
            ),
        )

    def safe_summary(self) -> dict:
        """Return a redacted summary safe for logs, CLI output, and reports."""
        return {
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_api_key_configured": bool(self.llm_api_key),
            "search_provider": self.search_provider,
            "search_api_key_configured": bool(self.search_api_key),
            "fetch_provider": self.fetch_provider,
            "cpc_provider": self.cpc_provider,
            "dataforseo_configured": bool(self.dataforseo_login and self.dataforseo_password),
            "cache_db_path": str(self.cache_db_path),
            "database_path": str(self.database_path),
            "log_level": self.log_level,
            "budget": {
                "max_search_calls": self.budget.max_search_calls,
                "max_pages_fetched": self.budget.max_pages_fetched,
                "max_llm_calls": self.budget.max_llm_calls,
                "max_runtime_seconds": self.budget.max_runtime_seconds,
                "max_estimated_cost_usd": str(self.budget.max_estimated_cost_usd),
            },
        }


def redact_secrets(text: str, secrets: list[str] | None = None) -> str:
    """Scrub API keys from any log or report string."""
    cleaned = text
    for secret in secrets or []:
        if secret and len(secret) >= 6:
            cleaned = cleaned.replace(secret, "[REDACTED]")
    return cleaned
