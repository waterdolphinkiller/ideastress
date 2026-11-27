"""Persistent SQLite TTL Cache for external CPC, complaint signals, and web fetches.

Prevents redundant DataForSEO API charges and Reddit rate-limiting across repeated runs.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional, Tuple


class SQLiteSignalCache:
    """Zero-config local SQLite key-value cache with per-entry TTL expiration."""

    def __init__(self, db_path: str | Path = "./ideastress_cache.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._hits = 0
        self._misses = 0
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signal_cache (
                    namespace TEXT NOT NULL,
                    cache_key TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    PRIMARY KEY (namespace, cache_key)
                )
                """
            )
            conn.commit()

    def get(self, namespace: str, cache_key: str, *, now: Optional[float] = None) -> Tuple[Optional[Any], bool]:
        """Return (payload, True) if a fresh cached entry exists, else (None, False)."""
        ts = now if now is not None else time.time()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT payload_json, expires_at FROM signal_cache
                WHERE namespace = ? AND cache_key = ?
                """,
                (namespace, cache_key),
            ).fetchone()
            if not row:
                self._misses += 1
                return None, False
            payload_json, expires_at = row
            if ts > expires_at:
                self._misses += 1
                return None, False
            self._hits += 1
            return json.loads(payload_json), True

    def set(
        self,
        namespace: str,
        cache_key: str,
        payload: Any,
        *,
        ttl_days: float = 30.0,
        now: Optional[float] = None,
    ) -> None:
        ts = now if now is not None else time.time()
        expires_at = ts + (ttl_days * 86400.0)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO signal_cache
                (namespace, cache_key, payload_json, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (namespace, cache_key, json.dumps(payload), ts, expires_at),
            )
            conn.commit()

    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_pct": round((self._hits / total) * 100.0, 1) if total > 0 else 0.0,
        }
