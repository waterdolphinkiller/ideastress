"""Zero-config SQLite persistence for IdeaStress analyses."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

from ideastress.domain.models import AnalysisResult


class SQLiteAnalysisStore:
    """Stores complete AnalysisResult JSON snapshots locally in SQLite."""

    def __init__(self, db_path: str | Path = "./ideastress.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    analysis_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    idea TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save(self, result: AnalysisResult) -> None:
        payload = result.json() if hasattr(result, "json") else result.model_dump_json()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO analyses
                (analysis_id, created_at, idea, verdict, status, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result.analysis_id,
                    result.created_at,
                    result.request.idea,
                    result.decision.verdict.value,
                    result.status.value,
                    payload,
                ),
            )
            conn.commit()

    def get(self, analysis_id: str) -> Optional[AnalysisResult]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT payload_json FROM analyses WHERE analysis_id = ?",
                (analysis_id,),
            ).fetchone()
            if not row:
                return None
            return AnalysisResult.parse_raw(row[0])

    def list_recent(self, limit: int = 20) -> List[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT analysis_id, created_at, idea, verdict, status
                FROM analyses
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [
                {
                    "analysis_id": r[0],
                    "created_at": r[1],
                    "idea": r[2],
                    "verdict": r[3],
                    "status": r[4],
                }
                for r in rows
            ]
