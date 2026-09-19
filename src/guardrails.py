"""Guardrails that can block a response (A7). Each guardrail runs on every generated response,
before release, and records what it checked and what it found -- whether or not it blocked
(Build Spec: "A guardrail that only warns is not a guardrail").
"""
from __future__ import annotations

import re

from src.models import ClassificationResult, GenerationResult, GuardrailOutcome, NormalizedTicket

# Patterns that would identify a *different* customer if they leaked into a response.
# (The current ticket's own customer_id/name are legitimate context, not a leak -- the check
# is whether the response text contains identifiers that don't belong to this ticket.)
_PII_PATTERNS = [
    re.compile(r"\bCUST-\d{3,}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),  # email address
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),  # card-number-shaped digit runs
]

_COMMITMENT_PATTERNS = [
    re.compile(r"\brefund(ed|s)?\b", re.I),
    re.compile(r"\bcredit(ed|s)? (to|your) account\b", re.I),
    re.compile(r"\bwill be fixed by\b", re.I),
    re.compile(r"\bguarantee(d)?\b", re.I),
    re.compile(r"\bwithin \d+ (hours?|days?|business days?)\b", re.I),
]

_INJECTION_ECHO_PATTERNS = [
    re.compile(r"ignore (all|previous|prior) instructions", re.I),
    re.compile(r"you are now", re.I),
    re.compile(r"system prompt", re.I),
]


def check_private_data(result: GenerationResult, ticket: NormalizedTicket) -> GuardrailOutcome:
    text = result.answer or ""
    for pattern in _PII_PATTERNS:
        for match in pattern.finditer(text):
            # allow the current ticket's own customer_id to appear (legitimate context)
            if ticket.customer_id and match.group(0) == ticket.customer_id:
                continue
            return GuardrailOutcome(name="private_data", passed=False, detail=f"matched {pattern.pattern!r}")
    return GuardrailOutcome(name="private_data", passed=True, detail="no identifier patterns found")


def check_grounding(result: GenerationResult) -> GuardrailOutcome:
    if not result.can_answer:
        return GuardrailOutcome(name="grounding", passed=True, detail="no answer was produced, nothing to ground")
    if not result.citations:
        return GuardrailOutcome(name="grounding", passed=False, detail="answer produced with zero citations")
    return GuardrailOutcome(
        name="grounding", passed=True, detail=f"{len(result.citations)} citation(s) present and doc_id-validated"
    )


def check_instruction_integrity(result: GenerationResult, ticket: NormalizedTicket) -> GuardrailOutcome:
    text = result.answer or ""
    for pattern in _INJECTION_ECHO_PATTERNS:
        if pattern.search(text):
            return GuardrailOutcome(
                name="instruction_integrity", passed=False, detail=f"response echoes injection-like pattern {pattern.pattern!r}"
            )
    return GuardrailOutcome(name="instruction_integrity", passed=True, detail="no injection echo detected")


def check_tone_scope(result: GenerationResult) -> GuardrailOutcome:
    text = result.answer or ""
    for pattern in _COMMITMENT_PATTERNS:
        if pattern.search(text):
            return GuardrailOutcome(
                name="tone_scope", passed=False, detail=f"response makes a commitment matching {pattern.pattern!r}"
            )
    return GuardrailOutcome(name="tone_scope", passed=True, detail="no refund/credit/timeline commitment found")


def check_confidence_floor(classification: ClassificationResult, threshold: float) -> GuardrailOutcome:
    if classification.confidence is None:
        return GuardrailOutcome(name="confidence_floor", passed=False, detail="missing confidence score")
    passed = classification.confidence >= threshold
    return GuardrailOutcome(
        name="confidence_floor",
        passed=passed,
        detail=f"confidence {classification.confidence:.2f} vs threshold {threshold:.2f}",
    )


def run_all(
    result: GenerationResult,
    ticket: NormalizedTicket,
    classification: ClassificationResult,
    threshold: float,
) -> list[GuardrailOutcome]:
    return [
        check_private_data(result, ticket),
        check_grounding(result),
        check_instruction_integrity(result, ticket),
        check_tone_scope(result),
        check_confidence_floor(classification, threshold),
    ]
