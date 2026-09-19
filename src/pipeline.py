"""Wires ingest -> classify -> retrieve -> route -> generate -> guardrails -> log into one
per-ticket pipeline, used by both the API (api.py) and the evaluation harness.
"""
from __future__ import annotations

import logging
import time

from src import config, classify as classify_mod, generate as generate_mod, guardrails, route as route_mod
from src.ingest import normalize_ticket
from src.logging_store import Decision, DecisionLog, new_decision_id, now_iso
from src.metrics import CONFIDENCE, GUARDRAIL, LATENCY, TICKETS
from src.retrieve import retrieve as retrieve_passages

logger = logging.getLogger(__name__)


def process_ticket(raw_ticket: dict, log: DecisionLog, store=None) -> dict:
    """Process one raw ticket end to end. Never raises -- every failure degrades to an
    escalation with a recorded reason (A11), and every stage writes a decision-log row (A8).

    Returns a dict summarising the outcome, used by the evaluation harness to build the
    metrics report.
    """
    _start = time.perf_counter()
    ticket = normalize_ticket(raw_ticket)

    classification = classify_mod.classify(ticket)
    CONFIDENCE.observe(classification.confidence)
    log.record(
        Decision(
            decision_id=new_decision_id(),
            timestamp=now_iso(),
            ticket_id=ticket.ticket_id,
            stage="classification",
            input_summary=f"{ticket.channel}: {ticket.subject}"[:200],
            model_name=config.MODEL_NAME,
            prediction_value=classification.intent,
            prediction_confidence=classification.confidence,
            alternatives=classification.alternatives,
            action_taken="classified",
            reason=classification.rationale,
            prompt_version="PR-01 v1.0",
            requirement_ids=["FR-03", "FR-04"],
        )
    )

    query_text = f"{ticket.subject} {ticket.body}".strip() or ticket.raw_text
    passages = retrieve_passages(query_text, store=store)
    log.record(
        Decision(
            decision_id=new_decision_id(),
            timestamp=now_iso(),
            ticket_id=ticket.ticket_id,
            stage="retrieval",
            input_summary=query_text[:200],
            sources_used=[{"doc_id": p.doc_id, "score": p.score} for p in passages],
            action_taken="retrieved" if passages else "no_result",
            reason=f"{len(passages)} passage(s) cleared the relevance floor",
            requirement_ids=["FR-05"],
        )
    )

    generation = generate_mod.generate(ticket, passages)
    guardrail_results = guardrails.run_all(generation, ticket, classification, config.CONFIDENCE_THRESHOLD)
    log.record(
        Decision(
            decision_id=new_decision_id(),
            timestamp=now_iso(),
            ticket_id=ticket.ticket_id,
            stage="generation",
            input_summary=query_text[:200],
            sources_used=[{"doc_id": c.doc_id} for c in generation.citations],
            action_taken="answered" if generation.can_answer else "no_answer",
            reason=generation.uncertainty or "grounded answer produced",
            guardrail_results={g.name: ("pass" if g.passed else "fail") for g in guardrail_results},
            prompt_version="PR-02 v1.0",
            requirement_ids=["FR-09", "FR-10", "FR-11"],
        )
    )

    decision = route_mod.decide(
        classification, passages, guardrail_results, config.CONFIDENCE_THRESHOLD, generation, ticket
    )
    log.record(
        Decision(
            decision_id=new_decision_id(),
            timestamp=now_iso(),
            ticket_id=ticket.ticket_id,
            stage="routing",
            input_summary=query_text[:200],
            threshold_applied=decision.threshold_applied,
            action_taken=decision.action,
            reason=decision.reason,
            requirement_ids=["FR-06", "FR-07"],
        )
    )

    LATENCY.observe(time.perf_counter() - _start)
    TICKETS.labels(channel=ticket.channel, outcome=decision.action).inc()
    for g in guardrail_results:
        if not g.passed:
            GUARDRAIL.labels(guardrail=g.name).inc()

    return {
        "ticket_id": ticket.ticket_id,
        "channel": ticket.channel,
        "intent": classification.intent,
        "urgency": classification.urgency,
        "confidence": classification.confidence,
        "retrieved_doc_ids": [p.doc_id for p in passages],
        "action": decision.action,
        "reason": decision.reason,
        "can_answer": generation.can_answer,
        "answer": generation.answer,
        "citations": [c.model_dump() for c in generation.citations],
        "guardrails": {g.name: g.passed for g in guardrail_results},
    }
