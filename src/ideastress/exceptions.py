"""Typed exception hierarchy for IdeaStress."""

from __future__ import annotations


class IdeaStressError(Exception):
    """Base exception for all IdeaStress errors."""


class ConfigurationError(IdeaStressError):
    """Raised when configuration or environment settings are invalid."""


class CurrencyMismatchError(IdeaStressError):
    """Raised when operations attempt to mix different ISO-4217 currencies."""


class FinancialValidationError(IdeaStressError):
    """Raised when financial inputs violate mathematical or domain constraints."""


class BudgetExceededError(IdeaStressError):
    """Raised when an analysis run hits its configured call, page, or USD budget."""

    def __init__(self, message: str, partial_state: dict | None = None) -> None:
        super().__init__(message)
        self.partial_state = partial_state or {}


class ProviderError(IdeaStressError):
    """Raised when an external LLM, Search, or Fetch provider fails."""


class SSRFBlockedError(IdeaStressError):
    """Raised when a URL targets localhost, private networks, metadata IPs, or disallowed schemes."""


class LedgerValidationError(IdeaStressError):
    """Raised when a venture.yaml assumption ledger cannot be parsed or validated."""
