from src import config
from src.ingest import normalize_ticket
from src.models import ClassificationResult, GenerationResult, GuardrailOutcome, RetrievedPassage
from src.route import decide


def _classification(intent="billing_query", confidence=0.9, must_escalate=False):
    return ClassificationResult(
        intent=intent, urgency="medium", confidence=confidence, must_not_auto_respond=must_escalate
    )


def _passage():
    return RetrievedPassage(doc_id="DOC-1", title="t", text="x", score=0.9)


def test_same_input_yields_same_decision():
    c, p = _classification(), [_passage()]
    d1 = decide(c, p, [])
    d2 = decide(c, p, [])
    assert d1.action == d2.action == "auto_respond"


def test_must_escalate_intent_always_escalates_even_with_high_confidence():
    c = _classification(intent="security_incident", confidence=0.99, must_escalate=True)
    d = decide(c, [_passage()], [])
    assert d.action == "escalate"


def test_no_retrieval_result_escalates():
    d = decide(_classification(), [], [])
    assert d.action == "escalate"


def test_low_confidence_escalates():
    d = decide(_classification(confidence=0.10), [_passage()], [])
    assert d.action == "escalate"


def test_failed_guardrail_blocks():
    d = decide(_classification(), [_passage()], [GuardrailOutcome(name="grounding", passed=False)])
    assert d.action == "block"


def test_kill_switch_forces_escalate(monkeypatch):
    monkeypatch.setattr(config, "AUTO_RESPOND_ENABLED", False)
    d = decide(_classification(), [_passage()], [])
    assert d.action == "escalate"


def test_generation_could_not_answer_escalates_even_with_retrieved_passages_and_high_confidence():
    """Regression test for a real bug found during the Day 4 gate run: 9/80 validation tickets
    retrieved candidate passages and had high classification confidence, but generation
    correctly declined to answer (can_answer=False) -- routing must escalate rather than
    auto-responding with a blank answer just because retrieval wasn't empty.
    """
    generation = GenerationResult(can_answer=False, answer="", citations=[], uncertainty="no passage covers this")
    d = decide(_classification(confidence=0.95), [_passage()], [], generation=generation)
    assert d.action == "escalate"


def test_safety_keyword_escalates_even_when_classifier_mislabels_intent():
    """Regression test for a real, live misclassification found during video-prep testing:
    ticket DEV-0003 (an enterprise customer's auditor asking about access-record retention,
    ground-truth intent `compliance_request`, must_not_auto_respond=true) was classified as
    `data_export` -- an intent NOT in the hard-escalate set -- at 0.95 confidence, so it was
    auto-answered when it should have escalated. `classification.must_not_auto_respond` and
    the intent-membership check are both derived from the same single classified intent value,
    so neither catches a misclassification. This test proves the independent keyword-based
    check (which reads the ticket's own text, not the classifier's output) closes that gap.
    """
    ticket = normalize_ticket({
        "ticket_id": "DEV-0003",
        "channel": "docs_comment",
        "subject": "Evidence for a compliance review",
        "body": (
            "Our auditor has asked for access records covering the last six months. "
            "Can I export these, and is that period within what you retain?"
        ),
    })
    # Simulate the actual misclassification: high-confidence, wrong, non-escalate intent.
    misclassified = _classification(intent="data_export", confidence=0.95, must_escalate=False)
    d = decide(misclassified, [_passage()], [], ticket=ticket)
    assert d.action == "escalate"
    assert "safety-sensitive term" in d.reason.lower()


def test_safety_keyword_does_not_fire_on_an_unrelated_ticket():
    ticket = normalize_ticket({
        "ticket_id": "T-1", "channel": "email", "subject": "Cannot deploy",
        "body": "My deployment keeps rolling back after the last release.",
    })
    d = decide(_classification(confidence=0.95), [_passage()], [], ticket=ticket)
    assert d.action == "auto_respond"
