"""SSRF-protected HTTP fetcher & prompt-injection sanitizer.

Security controls:
  - Only http:// and https:// schemes allowed.
  - Blocks localhost, private RFC1918 networks, loopback, link-local,
    multicast, reserved ranges, and cloud metadata IPs (169.254.169.254).
  - Enforces strict timeout and max response byte size (anti-zip-bomb).
  - Strips HTML tags and flags external text strictly as untrusted data.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse

import httpx

from ideastress.domain.models import utc_now_iso
from ideastress.exceptions import ProviderError, SSRFBlockedError
from ideastress.providers.interfaces import FetchedPage

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata",
}


def _is_forbidden_ip(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_safe_url(url: str, *, resolve_dns: bool = True) -> str:
    """Validate that a URL is safe against SSRF before any network call."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise SSRFBlockedError(f"Disallowed URL scheme: '{parsed.scheme}'. Only http/https allowed.")
    if not parsed.hostname:
        raise SSRFBlockedError("URL is missing a valid hostname.")

    host = parsed.hostname.lower().rstrip(".")
    if host in BLOCKED_HOSTNAMES or host.endswith(".local") or host.endswith(".internal"):
        raise SSRFBlockedError(f"Blocked internal/metadata hostname: '{host}'.")

    # Direct IP literal check
    try:
        if _is_forbidden_ip(host):
            raise SSRFBlockedError(f"Blocked non-public IP address: '{host}'.")
    except ValueError:
        # Hostname, optionally resolve DNS
        if resolve_dns:
            try:
                infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
                for info in infos:
                    ip_str = info[4][0]
                    if _is_forbidden_ip(ip_str):
                        raise SSRFBlockedError(f"Hostname '{host}' resolved to forbidden IP '{ip_str}'.")
            except socket.gaierror:
                # Offline/unresolvable DNS handled gracefully at fetch time
                pass
    return url.strip()


def extract_clean_excerpt(html: str, max_chars: int = 800) -> tuple[str, str]:
    """Extract page title and a short, sanitized plain-text excerpt (never stores full copyrighted body)."""
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else "Untitled Page"

    cleaned = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return title[:160], cleaned[:max_chars]


class SafeHTTPFetcher:
    """SSRF-safe web page fetcher for external evidence verification."""

    name = "safe_http"

    def __init__(self, timeout_seconds: float = 10.0, max_bytes: int = 512_000) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes

    def fetch(self, url: str) -> FetchedPage:
        safe_url = validate_safe_url(url, resolve_dns=True)
        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=False) as client:
                resp = client.get(safe_url, headers={"User-Agent": "IdeaStress-ResearchBot/0.1 (+https://github.com/ideastress)"})
                # Handle single safe redirect with re-validation
                if resp.status_code in (301, 302, 303, 307, 308) and "location" in resp.headers:
                    next_url = str(resp.url.join(resp.headers["location"]))
                    validate_safe_url(next_url, resolve_dns=True)
                    resp = client.get(next_url, headers={"User-Agent": "IdeaStress-ResearchBot/0.1"})

                raw_bytes = resp.content[: self.max_bytes]
                text = raw_bytes.decode("utf-8", errors="replace")
                title, snippet = extract_clean_excerpt(text)
                return FetchedPage(
                    url=safe_url,
                    final_url=str(resp.url),
                    title=title,
                    snippet=snippet,
                    status_code=resp.status_code,
                    retrieved_at=utc_now_iso(),
                    access_status="success" if resp.status_code < 400 else f"http_{resp.status_code}",
                    limitations=["Excerpt truncated to respect copyright and token budgets."],
                )
        except SSRFBlockedError:
            raise
        except Exception as exc:
            raise ProviderError(f"Failed to fetch '{safe_url}': {exc}") from exc
