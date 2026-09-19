"""A7: at least one guardrail can block a response, and does so when triggered.

The generation prompt (PR-02) already instructs the model not to make refund/timeline
commitments, and live testing (see PRD revision log) found the model reliably declines rather
than producing unsafe content -- which is good, but means a live ticket alone doesn't exercise
the block path. Guardrails exist precisely as a second line of defense for when generation
*isn't* well-behaved (a different/weaker model, a future prompt regression, an unusual input).

This test proves the mechanism the way it will actually run in production: a
(deliberately unsafe, to simulate a misbehaving generation step) GenerationResult is passed
through the real guardrails.run_all() + route.decide() -- the same functions pipeline.py calls
-- and the response is confirmed BLOCKED, not sent.
"""
from src.guardrails import run_all
from src.ingest import normalize_ticket
from src.models import Citation, ClassificationResult, GenerationResult
from src.route import decide


def _ticket():
    return normalize_ticket({"ticket_id": "ADV-1", "channel": "email", "subject": "Refund", "body": "Will I get a refund?"})


def _classification():
    return ClassificationResult(intent="billing_query", urgency="low", confidence=0.95)


def test_guardrail_blocks_an_unsafe_refund_commitment_end_to_end():
    unsafe_generation = GenerationResult(
        can_answer=True,
        answer="Yes, you will be refunded within 3 business days. I guarantee it.",
        citations=[Citation(doc_id="DOC-BILL-002", supports="refund")],
    )
    classification = _classification()
    guardrail_results = run_all(unsafe_generation, _ticket(), classification, threshold=0.80)

    tone_scope = next(g for g in guardrail_results if g.name == "tone_scope")
    assert tone_scope.passed is False

    from src.models import RetrievedPassage

    decision = decide(
        classification,
        retrieved=[RetrievedPassage(doc_id="DOC-BILL-002", title="t", text="x", score=0.5)],
        guardrail_results=guardrail_results,
        threshold=0.80,
        generation=unsafe_generation,
    )
    assert decision.action == "block"
    assert "tone_scope" in decision.reason


def test_guardrail_blocks_a_private_data_leak_end_to_end():
    from src.models import RetrievedPassage

    unsafe_generation = GenerationResult(
        can_answer=True,
        answer="I see the same issue was reported by CUST-9999 last week.",
        citations=[Citation(doc_id="DOC-DEPLOY-001", supports="issue")],
    )
    classification = _classification()
    guardrail_results = run_all(unsafe_generation, _ticket(), classification, threshold=0.80)
    private_data = next(g for g in guardrail_results if g.name == "private_data")
    assert private_data.passed is False

    decision = decide(
        classification,
        retrieved=[RetrievedPassage(doc_id="DOC-DEPLOY-001", title="t", text="x", score=0.5)],
        guardrail_results=guardrail_results,
        threshold=0.80,
        generation=unsafe_generation,
    )
    assert decision.action == "block"
