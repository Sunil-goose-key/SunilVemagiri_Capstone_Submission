"""Segmented fairness audit (Governance Framework §3, NFR-06).

Joins the harness's per-ticket results.jsonl back against the original input file (for
customer_tier/customer_region/language_fluency) and reports resolution rate and quality
proxy (auto-response rate here as the available proxy; a live CSAT proxy would need human
review) per segment, plus the variation from the best-performing segment.

Usage:
    python -m evaluation.fairness_audit --input 05_Datasets/validation_tickets.json --results evaluation/results/results.jsonl
"""
from __future__ import annotations

import argparse
import json


def load_jsonl(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_json(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def segment_report(tickets: list[dict], results_by_id: dict[str, dict], key: str) -> dict:
    segments: dict[str, list[dict]] = {}
    for t in tickets:
        seg_value = t.get(key) or "unknown"
        result = results_by_id.get(t.get("ticket_id"))
        if result is None:
            continue
        segments.setdefault(seg_value, []).append(result)

    report = {}
    for seg_value, seg_results in segments.items():
        n = len(seg_results)
        resolved = sum(1 for r in seg_results if r["action"] == "auto_respond")
        answered = sum(1 for r in seg_results if r.get("can_answer"))
        report[seg_value] = {
            "n": n,
            "resolution_rate_pct": round(100 * resolved / n, 1) if n else 0.0,
            "answerable_rate_pct": round(100 * answered / n, 1) if n else 0.0,
        }

    if report:
        best = max(v["resolution_rate_pct"] for v in report.values())
        for v in report.values():
            v["variation_from_best_pts"] = round(best - v["resolution_rate_pct"], 1)

    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--results", required=True)
    args = parser.parse_args()

    tickets = load_json(args.input)
    results = load_jsonl(args.results)
    results_by_id = {r["ticket_id"]: r for r in results}

    report = {
        "by_customer_tier": segment_report(tickets, results_by_id, "customer_tier"),
        "by_customer_region": segment_report(tickets, results_by_id, "customer_region"),
        "by_language_fluency": segment_report(tickets, results_by_id, "language_fluency"),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
