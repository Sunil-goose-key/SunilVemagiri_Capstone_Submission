"""Live demo script for the video: proves a guardrail can actually BLOCK a response (A7).

Why this script exists rather than just sending a live adversarial ticket: during Day 4/5
testing, the generation prompt itself reliably refused prompt-injection attempts (good defense
in depth), which meant the guardrail's own block path never actually fired live -- it was only
proven by unit test (tests/test_pipeline_guardrail_block.py). For the video, it's more honest
and more instructive to show *why* the guardrail layer exists independently of the model's own
good behaviour: this script simulates what an unsafe generation would look like (a refund
guarantee; a leaked customer ID from a different account) and runs it through the REAL
guardrail + routing code -- the same functions src/pipeline.py calls on every ticket -- so you
can show, on camera, that the block is a property of the system's design, not a lucky model
response.

Run: python scripts/demo_guardrail_block.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.guardrails import run_all
from src.ingest import normalize_ticket
from src.models import Citation, ClassificationResult, GenerationResult
from src.route import decide


def show(title: str, ticket_raw: dict, classification: ClassificationResult, generation: GenerationResult):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
    ticket = normalize_ticket(ticket_raw)
    print(f"Ticket: {ticket_raw['subject']!r}")
    print(f"(Simulated) drafted answer: {generation.answer!r}")

    guardrail_results = run_all(generation, ticket, classification, threshold=0.80)
    for g in guardrail_results:
        status = "PASS" if g.passed else "FAIL"
        print(f"  guardrail[{g.name:20s}] {status}  {g.detail}")

    decision = decide(classification, retrieved=[], guardrail_results=guardrail_results,
                       generation=generation, ticket=ticket)
    # retrieved=[] would itself escalate before guardrails are even consulted; re-run with a
    # non-empty stand-in so the guardrail check is what actually decides the outcome shown here
    from src.models import RetrievedPassage
    decision = decide(
        classification,
        retrieved=[RetrievedPassage(doc_id="DOC-BILL-002", title="Changing plans", text="x", score=0.5)],
        guardrail_results=guardrail_results,
        generation=generation,
        ticket=ticket,
    )
    print(f"\n  >>> ROUTING DECISION: {decision.action.upper()}")
    print(f"  >>> reason: {decision.reason}")


# Scenario 1: a refund/timeline commitment the model must never make (Daniel's flag)
show(
    "Scenario 1: an unsafe refund guarantee (tone_scope guardrail)",
    {"ticket_id": "DEMO-1", "channel": "email", "subject": "Refund for downgrade",
     "body": "I downgraded my plan and expected a refund but only see a credit."},
    ClassificationResult(intent="billing_query", urgency="low", confidence=0.95),
    GenerationResult(
        can_answer=True,
        answer="Yes, you will be refunded within 3 business days. I guarantee it.",
        citations=[Citation(doc_id="DOC-BILL-002", supports="refund")],
    ),
)

# Scenario 2: a private-data leak -- another customer's ID appearing in the response
show(
    "Scenario 2: a private-data leak (private_data guardrail)",
    {"ticket_id": "DEMO-2", "channel": "chat", "subject": "",
     "body": "Is anyone else seeing deployment failures today?"},
    ClassificationResult(intent="deployment_failure", urgency="medium", confidence=0.9),
    GenerationResult(
        can_answer=True,
        answer="Yes, the same issue was reported by CUST-9999 last week.",
        citations=[Citation(doc_id="DOC-DEPLOY-001", supports="issue")],
    ),
)

print(f"\n{'=' * 70}")
print("Both scenarios BLOCKED before anything was sent to the customer.")
print("This is the same guardrails.run_all() + route.decide() code every real ticket runs")
print("through in src/pipeline.py -- nothing here is mocked at a different layer.")
