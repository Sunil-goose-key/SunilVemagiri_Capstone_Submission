"""Intent + urgency classification with confidence (A3, FR-03, FR-04)."""
from __future__ import annotations

import logging
from pathlib import Path

from src import config
from src.llm_client import chat, parse_json_response, ProviderUnavailable
from src.models import Alternative, ClassificationResult, NormalizedTicket

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "build" / "classify.txt"

# Verified directly against development_tickets.json (all 22 classes actually present, with
# their dev-set counts noted for reference): account_access(22), api_key_issue(18),
# api_usage_question(24), authentication_failure(20), billing_query(24),
# compliance_request(26), configuration_help(17), data_export(29), data_residency(29),
# database_issue(26), deployment_failure(27), feature_request(20), integration_help(21),
# onboarding(22), performance_degradation(23), quota_or_overage(23), rate_limit(13),
# rollback_request(28), security_incident(26), sso_configuration(26), unclear_request(15),
# webhook_issue(21).
INTENT_CLASSES = [
    "account_access", "api_key_issue", "api_usage_question", "authentication_failure",
    "billing_query", "compliance_request", "configuration_help", "data_export",
    "data_residency", "database_issue", "deployment_failure", "feature_request",
    "integration_help", "onboarding", "performance_degradation", "quota_or_overage",
    "rate_limit", "rollback_request", "security_incident", "sso_configuration",
    "unclear_request", "webhook_issue",
]

_FALLBACK = ClassificationResult(
    intent="unclear_request",
    urgency="medium",
    confidence=0.0,
    alternatives=[],
    rationale="Classification failed or was unavailable; defaulted to a safe fallback.",
    must_not_auto_respond=True,
)


def classify(ticket: NormalizedTicket) -> ClassificationResult:
    """Never raises -- on any failure, returns a defined fallback that hard-escalates (A11,
    Build Spec: "Returns a defined fallback rather than raising an exception when it cannot
    classify").
    """
    prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")
    user_prompt = (
        prompt_template.replace("{{INTENT_CLASS_LIST}}", ", ".join(INTENT_CLASSES))
        .replace("{{CHANNEL}}", ticket.channel)
        .replace("{{SUBJECT}}", ticket.subject or "")
        .replace("{{BODY}}", ticket.body or "")
    )
    # the system role is embedded in the same template file (PR-01); split it out for the
    # system/user separation the injection defense relies on
    system_prompt, _, user_only = user_prompt.partition("TASK:")
    user_only = "TASK:" + user_only

    try:
        response = chat(system_prompt=system_prompt, user_prompt=user_only)
        parsed = parse_json_response(response.text)
        intent = parsed.get("intent", "unclear_request")
        result = ClassificationResult(
            intent=intent if intent in INTENT_CLASSES else "unclear_request",
            urgency=parsed.get("urgency", "medium"),
            confidence=float(parsed.get("confidence", 0.0)),
            alternatives=[
                Alternative(intent=a.get("intent", ""), confidence=float(a.get("confidence", 0.0)))
                for a in parsed.get("alternatives", [])
            ],
            rationale=parsed.get("rationale", ""),
            must_not_auto_respond=intent in config.MUST_ESCALATE_INTENTS,
        )
        return result
    except ProviderUnavailable:
        logger.warning("provider unavailable during classification for %s; using fallback", ticket.ticket_id)
        return _FALLBACK
    except Exception:
        logger.exception("classification failed unexpectedly for %s; using fallback", ticket.ticket_id)
        return _FALLBACK
