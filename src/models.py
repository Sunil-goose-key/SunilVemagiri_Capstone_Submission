"""Shared data shapes used across the pipeline (FR-01, FR-02)."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NormalizedTicket(BaseModel):
    """One internal representation regardless of source channel (A2)."""

    ticket_id: str
    channel: str  # email | chat | docs_comment | forum
    subject: str = ""
    body: str = ""
    raw_text: str  # preserved original text, whatever the source shape was
    received_at: Optional[str] = None
    customer_id: Optional[str] = None
    customer_tier: Optional[str] = None
    customer_region: Optional[str] = None
    language_fluency: Optional[str] = None


class Alternative(BaseModel):
    intent: str
    confidence: float


class ClassificationResult(BaseModel):
    intent: str
    urgency: str
    confidence: float = Field(ge=0.0, le=1.0)
    alternatives: list[Alternative] = Field(default_factory=list)
    rationale: str = ""
    must_not_auto_respond: bool = False


class RetrievedPassage(BaseModel):
    doc_id: str
    title: str = ""
    text: str
    score: float
    last_reviewed_days_ago: Optional[int] = None


class Citation(BaseModel):
    doc_id: str
    supports: str


class GenerationResult(BaseModel):
    can_answer: bool
    answer: str = ""
    citations: list[Citation] = Field(default_factory=list)
    uncertainty: str = ""


class GuardrailOutcome(BaseModel):
    name: str
    passed: bool
    detail: str = ""


class RoutingDecision(BaseModel):
    action: str  # auto_respond | escalate | block
    reason: str
    threshold_applied: float


class Decision(BaseModel):
    """Mirrors the Governance Framework's minimum decision-log record."""

    model_config = ConfigDict(protected_namespaces=())

    decision_id: str
    timestamp: str
    ticket_id: str
    stage: str  # classification | routing | generation | validation
    input_summary: str
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    prediction_value: Optional[str] = None
    prediction_confidence: Optional[float] = None
    alternatives: list[Alternative] = Field(default_factory=list)
    sources_used: list[dict] = Field(default_factory=list)
    threshold_applied: Optional[float] = None
    action_taken: str = ""
    reason: str = ""
    guardrail_results: dict = Field(default_factory=dict)
    prompt_version: Optional[str] = None
    requirement_ids: list[str] = Field(default_factory=list)
