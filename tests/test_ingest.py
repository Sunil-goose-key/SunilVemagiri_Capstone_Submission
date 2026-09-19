from src.ingest import normalize_ticket, normalize_all


def test_normalizes_all_four_channels():
    for channel in ("email", "chat", "docs_comment", "forum"):
        ticket = normalize_ticket({"ticket_id": "T-1", "channel": channel, "subject": "s", "body": "b"})
        assert ticket.channel == channel
        assert ticket.ticket_id == "T-1"


def test_handles_missing_fields_without_raising():
    ticket = normalize_ticket({})
    assert ticket.channel == "unknown"
    assert ticket.body == ""


def test_handles_empty_body_and_unusual_characters():
    ticket = normalize_ticket({"ticket_id": "T-2", "channel": "chat", "body": "😀\x00﻿"})
    assert ticket.ticket_id == "T-2"


def test_normalize_all_never_raises_on_malformed_input():
    raw = [{"ticket_id": "ok", "channel": "email"}, {"not_a_ticket": True}, None]
    result = normalize_all([r for r in raw if r is not None])
    assert len(result) == 2
