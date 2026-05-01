"""
SQLite-based MistakeDB — stores BAD-verdict responses for RLHF negative signal.

No Docker required: SQLite ships with Python.
DB file: data/mistakes.db (relative to project root).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# DB lives under project_root/data/mistakes.db
_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "mistakes.db"

_DDL = """
CREATE TABLE IF NOT EXISTS mistakes (
    id            TEXT PRIMARY KEY,
    company_id    TEXT NOT NULL,
    role          TEXT NOT NULL,
    mode          TEXT NOT NULL,
    domain        TEXT NOT NULL,
    user_query    TEXT NOT NULL,
    llm_response  TEXT NOT NULL,
    verdict       TEXT NOT NULL,
    verdict_reason TEXT NOT NULL,
    rag_score     REAL NOT NULL,
    flagged_at    TEXT NOT NULL,
    reviewed      INTEGER NOT NULL DEFAULT 0,
    review_note   TEXT NOT NULL DEFAULT ''
);
"""


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(_DDL)
    conn.commit()
    return conn


class MistakeDB:
    """Lightweight SQLite store for bad LLM responses used as RLHF negative signal."""

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @staticmethod
    def record(
        company_id: str,
        role: str,
        mode: str,
        domain: str,
        query: str,
        response: str,
        verdict: str,
        reason: str,
        rag_score: float,
    ) -> str:
        """Insert a mistake record. Returns the generated UUID."""
        mistake_id = str(uuid4())
        flagged_at = datetime.now(timezone.utc).isoformat()
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO mistakes
                    (id, company_id, role, mode, domain, user_query,
                     llm_response, verdict, verdict_reason, rag_score, flagged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mistake_id, company_id, role, mode, domain,
                    query, response, verdict, reason, rag_score, flagged_at,
                ),
            )
        return mistake_id

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    def list_pending() -> list[dict]:
        """Return all unreviewed mistakes (reviewed=0)."""
        with _connect() as conn:
            rows = conn.execute(
                "SELECT * FROM mistakes WHERE reviewed = 0 ORDER BY flagged_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get(mistake_id: str) -> dict | None:
        """Fetch a single mistake by id."""
        with _connect() as conn:
            row = conn.execute(
                "SELECT * FROM mistakes WHERE id = ?", (mistake_id,)
            ).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @staticmethod
    def mark_reviewed(mistake_id: str, note: str = "") -> bool:
        """Mark a mistake as reviewed. Returns True if a row was updated."""
        with _connect() as conn:
            cur = conn.execute(
                "UPDATE mistakes SET reviewed = 1, review_note = ? WHERE id = ?",
                (note, mistake_id),
            )
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    @staticmethod
    def export_rlhf_jsonl(output_path: Path) -> int:
        """
        Export all mistakes to a JSONL file suitable for RLHF training.

        Each line format:
            {"prompt": query, "chosen": "", "rejected": response, "reason": reason}

        Returns the number of records exported.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with _connect() as conn:
            rows = conn.execute(
                "SELECT user_query, llm_response, verdict_reason FROM mistakes"
            ).fetchall()

        count = 0
        with output_path.open("w", encoding="utf-8") as f:
            for row in rows:
                record = {
                    "prompt": row["user_query"],
                    "chosen": "",
                    "rejected": row["llm_response"],
                    "reason": row["verdict_reason"],
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1
        return count
