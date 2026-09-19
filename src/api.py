"""FastAPI application (application layer, per docs/architecture.md)."""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from src.logging_store import DecisionLog
from src.metrics import start_metrics_server
from src.pipeline import process_ticket
from src.retrieve import load_store

app = FastAPI(title="CloudServe Support Triage")

start_metrics_server()  # exposes Prometheus metrics on :8001/metrics
_log = DecisionLog()
try:
    _store = load_store()
except Exception:
    _store = None


class TicketIn(BaseModel):
    ticket_id: str
    channel: str
    subject: str = ""
    body: str = ""
    customer_id: str | None = None
    customer_tier: str | None = None
    customer_region: str | None = None
    language_fluency: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets")
def submit_ticket(ticket: TicketIn):
    return process_ticket(ticket.model_dump(), _log, _store)
