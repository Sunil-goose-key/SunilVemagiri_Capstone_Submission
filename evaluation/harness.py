"""The end-to-end evaluation harness (A9, A10).

Single documented command, takes --input and --output path arguments (never a hardcoded
filename, since the graded run points at a file we have never seen). Processes every ticket
in the input file, unattended, and writes a metrics report without further manual work.

Usage:
    python -m evaluation.harness --input data/validation_tickets.json --output evaluation/results/
"""
from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from src.ingest import load_tickets
from src.logging_store import DecisionLog
from src.pipeline import process_ticket
from src.retrieve import load_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _safe_process(raw_ticket: dict, log: DecisionLog, store) -> tuple[dict, float]:
    """Wrap process_ticket so that even a truly unexpected exception still produces an output
    row rather than silently dropping the ticket (Build Spec: "None are silently dropped").
    """
    start = time.perf_counter()
    try:
        result = process_ticket(raw_ticket, log, store)
    except Exception:
        logger.exception("unhandled failure processing ticket %s; recording as escalated", raw_ticket.get("ticket_id"))
        result = {
            "ticket_id": raw_ticket.get("ticket_id", "UNKNOWN"),
            "channel": raw_ticket.get("channel", "unknown"),
            "intent": None,
            "urgency": None,
            "confidence": 0.0,
            "retrieved_doc_ids": [],
            "action": "escalate",
            "reason": "unhandled exception during processing; escalated for safety",
            "can_answer": False,
            "answer": "",
            "citations": [],
            "guardrails": {},
        }
    elapsed = time.perf_counter() - start
    return result, elapsed


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(int(pct * len(ordered)), len(ordered) - 1)
    return ordered[idx]


def _classification_report(tickets: list[dict], results: list[dict]) -> dict:
    y_true, y_pred = [], []
    for raw, result in zip(tickets, results):
        expected = raw.get("labels", {}).get("intent")
        if expected is None:
            continue
        y_true.append(expected)
        y_pred.append(result.get("intent") or "unclear_request")
    if not y_true:
        return {"note": "no ground-truth intent labels present in this input file"}
    try:
        from sklearn.metrics import classification_report

        return classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    except Exception:
        logger.exception("sklearn classification_report failed")
        return {"note": "classification_report could not be computed"}


def _retrieval_hit_rate(tickets: list[dict], results: list[dict]) -> float:
    checked, hits = 0, 0
    for raw, result in zip(tickets, results):
        expected_docs = set(raw.get("labels", {}).get("expected_doc_ids") or [])
        if not expected_docs:
            continue
        checked += 1
        if expected_docs & set(result.get("retrieved_doc_ids") or []):
            hits += 1
    return (hits / checked) if checked else 0.0


def run(input_path: str, output_dir: str) -> dict:
    tickets = load_tickets(input_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    log = DecisionLog()
    try:
        store = load_store()
    except Exception:
        logger.warning("could not load vector store; retrieval will degrade to empty results (A11)")
        store = None

    results, latencies = [], []
    for raw in tickets:
        result, elapsed = _safe_process(raw, log, store)
        results.append(result)
        latencies.append(elapsed)

    total = len(results)
    auto_responded = sum(1 for r in results if r["action"] == "auto_respond")
    escalated = sum(1 for r in results if r["action"] == "escalate")
    blocked = sum(1 for r in results if r["action"] == "block")

    guardrail_activations: dict[str, int] = {}
    private_data_detections = 0
    for r in results:
        for name, passed in (r.get("guardrails") or {}).items():
            if not passed:
                guardrail_activations[name] = guardrail_activations.get(name, 0) + 1
                if name == "private_data":
                    private_data_detections += 1

    coverage = log.coverage()

    metrics = {
        "run_metadata": {
            "input_path": str(input_path),
            "output_path": str(output_dir),
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "tickets_in_file": total,
        },
        "volume": {
            "processed": total,
            "auto_responded": auto_responded,
            "escalated": escalated,
            "blocked": blocked,
        },
        "business": {
            "first_contact_resolution_pct": round(100 * auto_responded / total, 1) if total else 0.0,
            "escalation_rate_pct": round(100 * (escalated + blocked) / total, 1) if total else 0.0,
            "note": (
                "auto_responded/escalated here describe THIS run's routing decisions, not "
                "measured live customer outcomes -- there are no live customers. Compare "
                "against the historical baseline in history.* for context, not as equivalence."
            ),
        },
        "technical": {
            "classification_report": _classification_report(tickets, results),
            "retrieval_hit_rate_pct": round(100 * _retrieval_hit_rate(tickets, results), 1),
            "latency_seconds": {
                "mean": round(statistics.mean(latencies), 3) if latencies else 0.0,
                "median": round(statistics.median(latencies), 3) if latencies else 0.0,
                "p95": round(_percentile(latencies, 0.95), 3),
            },
        },
        "governance": {
            "decisions_logged_distinct_tickets": coverage["distinct_tickets_logged"],
            "tickets_processed": total,
            "log_reconciles": coverage["distinct_tickets_logged"] == total,
            "guardrail_activations": guardrail_activations,
            "private_data_detections": private_data_detections,
        },
    }

    log.close()

    report_path = output_path / f"metrics_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    with open(output_path / "results.jsonl", "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    logger.info("wrote metrics report to %s", report_path)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full evaluation harness end to end, unattended.")
    parser.add_argument("--input", required=True, help="Path to a ticket JSON file (any file matching the schema)")
    parser.add_argument("--output", required=True, help="Directory to write the metrics report and results into")
    args = parser.parse_args()

    metrics = run(args.input, args.output)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
