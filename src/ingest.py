"""Normalize tickets from all four channels into one internal shape (A2, FR-01, FR-02).

Handles missing fields, unusual characters and empty bodies without raising (A11).
"""
from __future__ import annotations

import json
from typing import Any

from src.models import NormalizedTicket

VALID_CHANNELS = {"email", "chat", "docs_comment", "forum"}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def normalize_ticket(raw: dict) -> NormalizedTicket:
    """Convert one raw ticket record (as found in the dataset JSON) into a NormalizedTicket.

    Never raises on malformed input -- missing/odd fields degrade to safe defaults rather
    than crashing the ingest step, per A11.
    """
    channel = _safe_str(raw.get("channel", "")).strip().lower()
    if channel not in VALID_CHANNELS:
        channel = channel or "unknown"

    subject = _safe_str(raw.get("subject", ""))
    body = _safe_str(raw.get("body", ""))

    return NormalizedTicket(
        ticket_id=_safe_str(raw.get("ticket_id") or raw.get("id") or "UNKNOWN"),
        channel=channel,
        subject=subject,
        body=body,
        raw_text=json.dumps(raw, ensure_ascii=False, default=str),
        received_at=raw.get("received_at"),
        customer_id=raw.get("customer_id"),
        customer_tier=raw.get("customer_tier"),
        customer_region=raw.get("customer_region"),
        language_fluency=raw.get("language_fluency"),
    )


def load_tickets(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        # tolerate a top-level {"tickets": [...]} wrapper if the hidden set is ever shaped that way
        data = data.get("tickets", [])
    return data


def normalize_all(raw_tickets: list[dict]) -> list[NormalizedTicket]:
    normalized = []
    for raw in raw_tickets:
        try:
            normalized.append(normalize_ticket(raw))
        except Exception:
            # A11: never let one malformed ticket abort the whole run
            normalized.append(
                NormalizedTicket(
                    ticket_id=_safe_str(raw.get("ticket_id", "MALFORMED")) if isinstance(raw, dict) else "MALFORMED",
                    channel="unknown",
                    subject="",
                    body="",
                    raw_text=_safe_str(raw),
                )
            )
    return normalized


if __name__ == "__main__":
    # Quick manual check (Build Spec Day 1 checkpoint): print one normalized ticket per channel
    import sys

    tickets = load_tickets(sys.argv[1] if len(sys.argv) > 1 else "05_Datasets/development_tickets.json")
    seen = set()
    for raw in tickets:
        ch = raw.get("channel")
        if ch in VALID_CHANNELS and ch not in seen:
            seen.add(ch)
            print(normalize_ticket(raw).model_dump_json(indent=2))
        if seen == VALID_CHANNELS:
            break
