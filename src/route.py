"""Deterministic routing decision (A5, FR-06, FR-07).

Same input always yields the same decision. must_not_auto_respond intents hard-escalate
regardless of confidence. Records a human-readable reason for every decision.

Defense in depth on the hard-escalate check: `classification.must_not_auto_respond` and the
`intent in MUST_ESCALATE_INTENTS` check below are BOTH derived from the single classified
`intent` value -- they are not independent signals. A real example found during video-prep
testing (ticket DEV-0003, an audit-log-retention question from an enterprise customer) was
misclassified as `data_export` instead of the correct `compliance_request`, so the intent-based
check never triggered and the ticket was auto-answered when it should have escalated. See
`_mentions_safety_sensitive_topic` below for the independent, intent-agnostic second check added
in response.
"""
from __future__ import annotations

import re

from src import config
from src.models import ClassificationResult, GenerationResult, GuardrailOutcome, NormalizedTicket, RetrievedPassage, RoutingDecision

# Deliberately independent of the classifier: a deterministic keyword scan over the raw ticket
# text, so hard-escalate coverage does not rest entirely on one categorical prediction being
# exactly right. Terms chosen to catch audit/compliance/legal/security-incident topics
# regardless of what intent the ticket gets classified as.
_SAFETY_KEYWORD_PATTERN = re.compile(
    r"\b("
    r"audit(?:or|ing|s)?|complian(?:ce|t)|regulat(?:or|ion|ory|ors)|"
    r"subpoena|legal hold|law\s?suit|litigation|"
    r"data breach|security incident|compromis(?:ed|e)|unauthori[sz]ed access|"
    r"gdpr|ccpa|hipaa|right to be forgotten|"
    r"sox\b|soc ?2|iso ?27001|"
    r"personal data request|data protection (?:officer|authority)"
    r")\b",
    re.IGNORECASE,
)


def _mentions_safety_sensitive_topic(ticket: NormalizedTicket | None) -> str | None:
    if ticket is None:
        return None
    text = f"{ticket.subject or ''} {ticket.body or ''}"
    match = _SAFETY_KEYWORD_PATTERN.search(text)
    return match.group(0) if match else None


def decide(
    classification: ClassificationResult,
    retrieved: list[RetrievedPassage],
    guardrail_results: list[GuardrailOutcome] | None = None,
    threshold: float | None = None,
    generation: GenerationResult | None = None,
    ticket: NormalizedTicket | None = None,
) -> RoutingDecision:
    threshold = threshold if threshold is not None else config.CONFIDENCE_THRESHOLD
    guardrail_results = guardrail_results or []

    if not config.AUTO_RESPOND_ENABLED:
        return RoutingDecision(
            action="escalate",
            reason="Auto-respond is disabled via the kill switch (AUTO_RESPOND_ENABLED=false).",
            threshold_applied=threshold,
        )

    if classification.must_not_auto_respond or classification.intent in config.MUST_ESCALATE_INTENTS:
        return RoutingDecision(
            action="escalate",
            reason=(
                f"Intent '{classification.intent}' is in the hard-escalate set "
                f"({sorted(config.MUST_ESCALATE_INTENTS)}); never auto-answered regardless of confidence."
            ),
            threshold_applied=threshold,
        )

    matched_keyword = _mentions_safety_sensitive_topic(ticket)
    if matched_keyword:
        return RoutingDecision(
            action="escalate",
            reason=(
                f"Ticket text mentions a safety-sensitive term ('{matched_keyword}') independently "
                f"of the classified intent ('{classification.intent}'); escalating as a defense-in-"
                f"depth check rather than trusting classification alone."
            ),
            threshold_applied=threshold,
        )

    if not retrieved:
        return RoutingDecision(
            action="escalate",
            reason="No retrieval result cleared the relevance floor; no grounded source available.",
            threshold_applied=threshold,
        )

    # A real bug found during the Day 4 gate run: retrieval can return passages that don't
    # actually answer the question, in which case generation correctly declines (can_answer =
    # False) -- but routing must still escalate rather than auto-responding with a blank
    # answer just because *some* passage was retrieved and confidence happened to be high.
    if generation is not None and not generation.can_answer:
        return RoutingDecision(
            action="escalate",
            reason=(
                "Retrieval returned candidate passages, but generation could not ground an "
                f"answer in them ({generation.uncertainty or 'no reason given'})."
            ),
            threshold_applied=threshold,
        )

    if classification.confidence < threshold:
        return RoutingDecision(
            action="escalate",
            reason=(
                f"Classification confidence {classification.confidence:.2f} is below the "
                f"threshold {threshold:.2f}."
            ),
            threshold_applied=threshold,
        )

    failed = [g for g in guardrail_results if not g.passed]
    if failed:
        return RoutingDecision(
            action="block",
            reason=f"Guardrail(s) failed: {', '.join(g.name for g in failed)}.",
            threshold_applied=threshold,
        )

    return RoutingDecision(
        action="auto_respond",
        reason=(
            f"Confidence {classification.confidence:.2f} >= threshold {threshold:.2f}; "
            f"grounded source available; all guardrails passed."
        ),
        threshold_applied=threshold,
    )
