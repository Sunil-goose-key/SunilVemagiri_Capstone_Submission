"""A11: the system must degrade without crashing on no-retrieval-hit, provider
timeout/outage, rate limiting, and malformed input."""
from unittest.mock import patch

from src.classify import classify
from src.generate import generate
from src.ingest import normalize_ticket
from src.llm_client import ProviderUnavailable
from src.models import RetrievedPassage


def _ticket():
    return normalize_ticket({"ticket_id": "T-1", "channel": "email", "subject": "s", "body": "b"})


def test_classify_degrades_to_fallback_on_provider_unavailable():
    with patch("src.classify.chat", side_effect=ProviderUnavailable("simulated outage")):
        result = classify(_ticket())
    assert result.must_not_auto_respond is True  # fails safe, not silently
    assert result.confidence == 0.0


def test_classify_degrades_to_fallback_on_timeout():
    with patch("src.classify.chat", side_effect=ProviderUnavailable("simulated timeout")):
        result = classify(_ticket())
    assert result.intent == "unclear_request"


def test_classify_degrades_on_rate_limit():
    with patch("src.classify.chat", side_effect=ProviderUnavailable("HTTP 429: rate limited")):
        result = classify(_ticket())
    assert result.must_not_auto_respond is True


def test_classify_degrades_on_unexpected_exception():
    with patch("src.classify.chat", side_effect=RuntimeError("something else entirely")):
        result = classify(_ticket())
    assert result.intent == "unclear_request"


def test_generate_returns_no_answer_with_no_retrieved_passages():
    result = generate(_ticket(), [])
    assert result.can_answer is False
    assert result.answer == ""


def test_generate_degrades_on_provider_unavailable():
    passages = [RetrievedPassage(doc_id="D-1", title="t", text="x", score=0.5)]
    with patch("src.generate.chat", side_effect=ProviderUnavailable("simulated outage")):
        result = generate(_ticket(), passages)
    assert result.can_answer is False


def test_ingest_handles_malformed_input_types():
    # None, missing keys, wrong types -- must never raise
    for bad in [{}, {"channel": 12345}, {"body": ["not", "a", "string"]}, {"ticket_id": None}]:
        normalize_ticket(bad)  # should not raise
