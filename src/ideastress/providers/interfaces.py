"""Pluggable provider protocol interfaces for LLM, Search, and Web Fetch."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    publisher: str = ""
    published_at: str | None = None


@dataclass
class FetchedPage:
    url: str
    final_url: str
    title: str
    snippet: str
    status_code: int
    retrieved_at: str
    access_status: str = "success"
    limitations: List[str] = field(default_factory=list)


class LLMProvider(Protocol):
    name: str

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_schema: Type[T],
        context: Dict[str, Any] | None = None,
    ) -> T: ...


class SearchProvider(Protocol):
    name: str

    def search(self, query: str, *, limit: int = 8) -> List[SearchResult]: ...


class FetchProvider(Protocol):
    name: str

    def fetch(self, url: str) -> FetchedPage: ...
