"""Grounded answer generation with citations (A6, FR-09, FR-10)."""
from __future__ import annotations

import logging
from pathlib import Path

from src.llm_client import chat, parse_json_response, ProviderUnavailable
from src.models import Citation, GenerationResult, NormalizedTicket, RetrievedPassage

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "build" / "generate.txt"

_CANNOT_ANSWER = GenerationResult(
    can_answer=False,
    answer="",
    citations=[],
    uncertainty="Generation failed or was unavailable; escalating rather than guessing.",
)


def _format_passages(passages: list[RetrievedPassage]) -> str:
    return "\n\n".join(f"[{p.doc_id}] {p.title}\n{p.text}" for p in passages)


def generate(ticket: NormalizedTicket, passages: list[RetrievedPassage]) -> GenerationResult:
    """Never raises -- on any failure, returns a "cannot answer" result rather than a
    fabricated one (A11; Build Spec Generate: "states plainly when it does not know").
    """
    if not passages:
        return GenerationResult(
            can_answer=False,
            answer="",
            citations=[],
            uncertainty="No retrieved passages cleared the relevance floor for this ticket.",
        )

    template = _PROMPT_PATH.read_text(encoding="utf-8")
    full_prompt = (
        template.replace("{{RETRIEVED_PASSAGES}}", _format_passages(passages))
        .replace("{{CHANNEL}}", ticket.channel)
        .replace("{{SUBJECT}}", ticket.subject or "")
        .replace("{{BODY}}", ticket.body or "")
    )
    system_prompt, _, user_only = full_prompt.partition("TASK:")
    user_only = "TASK:" + user_only

    valid_doc_ids = {p.doc_id for p in passages}
    try:
        response = chat(system_prompt=system_prompt, user_prompt=user_only)
        parsed = parse_json_response(response.text)
        citations = [
            Citation(doc_id=c.get("doc_id", ""), supports=c.get("supports", ""))
            for c in parsed.get("citations", [])
            if c.get("doc_id") in valid_doc_ids  # never trust a citation to a passage we didn't provide
        ]
        return GenerationResult(
            can_answer=bool(parsed.get("can_answer", False)) and bool(citations),
            answer=parsed.get("answer", "") if parsed.get("can_answer") else "",
            citations=citations,
            uncertainty=parsed.get("uncertainty", ""),
        )
    except ProviderUnavailable:
        logger.warning("provider unavailable during generation for %s", ticket.ticket_id)
        return _CANNOT_ANSWER
    except Exception:
        logger.exception("generation failed unexpectedly for %s", ticket.ticket_id)
        return _CANNOT_ANSWER
