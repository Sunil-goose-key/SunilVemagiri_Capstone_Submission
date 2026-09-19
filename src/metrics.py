"""Prometheus instrumentation (Setup Guide §06). Exposed on :8001/metrics when
start_metrics_server() is called (e.g. from api.py); harmless no-op registration cost if never
scraped, so it's safe to import from the harness too.
"""
from __future__ import annotations

from prometheus_client import Counter, Histogram, start_http_server

TICKETS = Counter("tickets_processed_total", "Tickets processed", ["channel", "outcome"])
LATENCY = Histogram("response_seconds", "End to end response time")
GUARDRAIL = Counter("guardrail_blocks_total", "Responses blocked", ["guardrail"])
CONFIDENCE = Histogram(
    "classification_confidence", "Distribution of classification confidence scores",
    buckets=(0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 1.0),
)

_server_started = False


def start_metrics_server(port: int = 8001) -> None:
    global _server_started
    if not _server_started:
        start_http_server(port)
        _server_started = True
