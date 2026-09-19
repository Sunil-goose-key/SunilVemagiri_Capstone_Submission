"""Governance: the kill switch must force every ticket to escalate, immediately, without a
deployment (Governance_Framework_DRAFT.md §5)."""
from src import config
from src.models import ClassificationResult, RetrievedPassage
from src.route import decide


def test_kill_switch_escalates_even_a_normally_auto_respond_case(monkeypatch):
    monkeypatch.setattr(config, "AUTO_RESPOND_ENABLED", False)
    high_confidence = ClassificationResult(intent="billing_query", urgency="low", confidence=0.99)
    passage = RetrievedPassage(doc_id="DOC-1", title="t", text="x", score=0.9)
    decision = decide(high_confidence, [passage], [])
    assert decision.action == "escalate"
    assert "kill switch" in decision.reason.lower()


def test_kill_switch_off_allows_normal_auto_respond(monkeypatch):
    monkeypatch.setattr(config, "AUTO_RESPOND_ENABLED", True)
    high_confidence = ClassificationResult(intent="billing_query", urgency="low", confidence=0.99)
    passage = RetrievedPassage(doc_id="DOC-1", title="t", text="x", score=0.9)
    decision = decide(high_confidence, [passage], [])
    assert decision.action == "auto_respond"
