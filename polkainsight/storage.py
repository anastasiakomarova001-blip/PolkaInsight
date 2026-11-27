from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class HistoryStorage:
    def __init__(self, path: str | Path = "data/polkainsight.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    period_days INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    integrated_score REAL,
                    algorithm_version TEXT NOT NULL,
                    result_json TEXT NOT NULL
                )
            """)

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def save(self, result: dict) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """INSERT INTO analysis_history
                (created_at, asset, period_days, mode, integrated_score, algorithm_version, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    result["metadata"]["created_at"],
                    "DOT",
                    result["metadata"]["period_days"],
                    result["metadata"]["mode"],
                    result["integrated"]["score"],
                    result["metadata"]["algorithm_version"],
                    json.dumps(result, ensure_ascii=False),
                ),
            )
            return int(cursor.lastrowid)

    def list(self, limit: int = 50) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT id, created_at, asset, period_days, mode,
                integrated_score, algorithm_version FROM analysis_history
                ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, analysis_id: int) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT result_json FROM analysis_history WHERE id = ?", (analysis_id,)
            ).fetchone()
        return json.loads(row["result_json"]) if row else None
