"""Decision log persistence (A8, Governance Framework minimum record).

Every automated decision at every stage is written here. Coverage is checked by comparing
COUNT(DISTINCT ticket_id) against tickets processed at the end of a run.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.models import Decision

_SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
    decision_id      TEXT PRIMARY KEY,
    created_at       TEXT NOT NULL,
    ticket_id        TEXT NOT NULL,
    stage            TEXT NOT NULL,
    input_summary    TEXT,
    model_name       TEXT,
    model_version    TEXT,
    prediction       TEXT,
    confidence       REAL,
    alternatives     TEXT,
    sources_used     TEXT,
    threshold        REAL,
    action_taken     TEXT NOT NULL,
    reason           TEXT NOT NULL,
    guardrails       TEXT,
    prompt_version   TEXT,
    requirement_ids  TEXT
)
"""


class DecisionLog:
    def __init__(self, db_path: str = "./storage/decisions.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def record(self, decision: Decision) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO decisions
            (decision_id, created_at, ticket_id, stage, input_summary, model_name,
             model_version, prediction, confidence, alternatives, sources_used,
             threshold, action_taken, reason, guardrails, prompt_version, requirement_ids)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                decision.decision_id,
                decision.timestamp,
                decision.ticket_id,
                decision.stage,
                decision.input_summary,
                decision.model_name,
                decision.model_version,
                decision.prediction_value,
                decision.prediction_confidence,
                json.dumps([a.model_dump() for a in decision.alternatives]),
                json.dumps(decision.sources_used),
                decision.threshold_applied,
                decision.action_taken,
                decision.reason,
                json.dumps(decision.guardrail_results),
                decision.prompt_version,
                json.dumps(decision.requirement_ids),
            ),
        )
        self._conn.commit()

    def coverage(self) -> dict:
        """Distinct tickets logged, and counts by final action -- used to reconcile A8."""
        cur = self._conn.execute("SELECT COUNT(DISTINCT ticket_id) FROM decisions")
        distinct_tickets = cur.fetchone()[0]
        cur = self._conn.execute(
            "SELECT action_taken, COUNT(*) FROM decisions WHERE stage='routing' GROUP BY action_taken"
        )
        by_action = dict(cur.fetchall())
        return {"distinct_tickets_logged": distinct_tickets, "routing_actions": by_action}

    def close(self) -> None:
        self._conn.close()


def new_decision_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
