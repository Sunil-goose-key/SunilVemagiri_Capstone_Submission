"""Automated NFR-03 evidence: checks generated answers against ground_truth_responses.json.

ground_truth_responses.json was previously unused anywhere in this codebase -- a real gap
disclosed in the report. Its 200 entries key off development_tickets.json ticket_ids and carry
two auto-checkable fields per entry: must_mention (points a correct answer should cover) and
must_not_claim (claims the answer must never make). must_not_claim is populated on all 200/200
entries; must_mention only on 59/200 (the rest are empty arrays), so must_not_claim is the
higher-value, safety-relevant check here.

This uses an LLM judge (PR-04, prompts/evaluation/ground_truth_judge.txt) rather than plain
keyword matching, because the forbidden claims are concepts ("a refund has been issued"), not
fixed phrases a generated answer would repeat verbatim -- substring matching would under-detect
real violations, which is the worse failure direction for a safety check.

IMPORTANT CAVEAT, stated here and repeated in the report: this is an automated proxy, not the
human review (>=50 sampled responses, 2 raters) that NFR-03's verification method specifies.
An LLM judge can itself be wrong or inconsistent; it is additional evidence, not a replacement
for the human step.

Usage: python -m evaluation.ground_truth_check [--limit N]
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.llm_client import chat, parse_json_response, ProviderUnavailable
from src.logging_store import DecisionLog
from src.pipeline import process_ticket
from src.retrieve import load_store

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

_JUDGE_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "evaluation" / "ground_truth_judge.txt"


def load_ground_truth(path: str = "05_Datasets/ground_truth_responses.json") -> dict:
    entries = json.loads(Path(path).read_text(encoding="utf-8"))
    return {e["ticket_id"]: e for e in entries}


def judge(answer: str, must_mention: list[str], must_not_claim: list[str]) -> dict:
    """Never raises -- on failure, returns a result flagging itself as unjudged rather than
    silently omitting the ticket from the aggregate (A11-style degradation, applied here too).
    """
    if not must_mention and not must_not_claim:
        return {"mentions_covered": [], "mentions_missed": [], "claims_violated": [], "notes": "nothing to check"}

    template = _JUDGE_PROMPT_PATH.read_text(encoding="utf-8")
    prompt = (
        template.replace("{{ANSWER}}", answer)
        .replace("{{MUST_MENTION}}", json.dumps(must_mention))
        .replace("{{MUST_NOT_CLAIM}}", json.dumps(must_not_claim))
    )
    system_prompt, _, user_only = prompt.partition("TASK:")
    user_only = "TASK:" + user_only

    try:
        response = chat(system_prompt=system_prompt, user_prompt=user_only)
        parsed = parse_json_response(response.text)
        mention_results = parsed.get("must_mention_results", [])
        claim_results = parsed.get("must_not_claim_results", [])
        return {
            "mentions_covered": [r["item"] for r in mention_results if r.get("covered")],
            "mentions_missed": [r["item"] for r in mention_results if not r.get("covered")],
            "claims_violated": [r["item"] for r in claim_results if r.get("violated")],
            "claims_cleared": [r["item"] for r in claim_results if not r.get("violated")],
            "notes": parsed.get("notes", ""),
        }
    except (ProviderUnavailable, Exception) as exc:  # noqa: BLE001 -- deliberately broad, see docstring
        logger.warning("judge call failed: %s", exc)
        return {"mentions_covered": [], "mentions_missed": must_mention, "claims_violated": [],
                "claims_cleared": [], "notes": f"JUDGE CALL FAILED, not counted as covered or violated: {exc}",
                "judge_error": True}


def run(limit: int | None = None) -> dict:
    ground_truth = load_ground_truth()
    dev_tickets = {
        t["ticket_id"]: t
        for t in json.loads(Path("05_Datasets/development_tickets.json").read_text(encoding="utf-8"))
    }
    target_ids = [tid for tid in ground_truth if tid in dev_tickets]
    if limit:
        target_ids = target_ids[:limit]

    store = load_store()
    db_path = Path("./storage/ground_truth_check_decisions.db")
    db_path.unlink(missing_ok=True)
    log = DecisionLog(db_path=str(db_path))

    results = []
    for i, tid in enumerate(target_ids, 1):
        gt = ground_truth[tid]
        raw = dev_tickets[tid]
        r = process_ticket(raw, log, store)

        row = {
            "ticket_id": tid,
            "action": r["action"],
            "can_answer": r["can_answer"],
            "expected_doc_ids": gt["expected_doc_ids"],
            "cited_doc_ids": r["retrieved_doc_ids"],
        }
        if gt["expected_doc_ids"]:
            row["citation_hit"] = bool(set(gt["expected_doc_ids"]) & set(r["retrieved_doc_ids"]))
        else:
            row["citation_hit"] = None

        if r["can_answer"] and r["answer"]:
            jr = judge(r["answer"], gt["must_mention"], gt["must_not_claim"])
            row.update(jr)
        else:
            row.update({"mentions_covered": [], "mentions_missed": gt["must_mention"],
                        "claims_violated": [], "notes": "no answer generated (escalated/blocked)"})

        results.append(row)
        if i % 20 == 0:
            print(f"  ... {i}/{len(target_ids)} processed")

    return summarize(results)


def summarize(results: list[dict]) -> dict:
    total = len(results)
    answered = [r for r in results if r["can_answer"]]
    judged = [r for r in answered if not r.get("judge_error")]

    total_must_mention = sum(len(r["mentions_covered"]) + len(r["mentions_missed"]) for r in judged)
    total_mentions_covered = sum(len(r["mentions_covered"]) for r in judged)

    violations = [(r["ticket_id"], r["claims_violated"]) for r in judged if r["claims_violated"]]

    with_expected_docs = [r for r in results if r["expected_doc_ids"]]
    citation_hits = [r for r in with_expected_docs if r["citation_hit"]]

    return {
        "run_metadata": {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "method": "LLM judge (PR-04) over ground_truth_responses.json -- an automated proxy, "
                      "NOT the human review (>=50 samples, 2 raters) NFR-03's verification method specifies",
            "tickets_checked": total,
        },
        "volume": {
            "processed": total,
            "answered": len(answered),
            "escalated_or_blocked": total - len(answered),
            "judge_call_failures": len(answered) - len(judged),
        },
        "must_mention_coverage": {
            "total_points": total_must_mention,
            "covered": total_mentions_covered,
            "coverage_pct": round(100 * total_mentions_covered / total_must_mention, 1) if total_must_mention else None,
            "note": "only entries with a non-empty must_mention list contribute (59/200 in the full ground-truth set)",
        },
        "must_not_claim_safety": {
            "tickets_with_answer_and_judged": len(judged),
            "tickets_with_at_least_one_violation": len(violations),
            "violation_rate_pct": round(100 * len(violations) / len(judged), 2) if judged else None,
            "violations": [{"ticket_id": tid, "claims": claims} for tid, claims in violations],
            "note": "must_not_claim is populated on all 200/200 ground-truth entries -- this is the headline safety figure",
        },
        "citation_accuracy_proxy": {
            "tickets_with_expected_doc_ids": len(with_expected_docs),
            "citation_hits": len(citation_hits),
            "hit_rate_pct": round(100 * len(citation_hits) / len(with_expected_docs), 1) if with_expected_docs else None,
            "note": "checks whether ANY expected_doc_id appears among the tickets's cited doc_ids -- a proxy for "
                    "citation accuracy, not the same as NFR-03's 'does the passage support the sentence' definition",
        },
        "per_ticket_results": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N tickets (for a quick sanity check)")
    parser.add_argument("--output", default="evaluation/results", help="Directory to write the report to")
    args = parser.parse_args()

    print(f"Running ground-truth check{' (limit=' + str(args.limit) + ')' if args.limit else ''}...")
    summary = run(limit=args.limit)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"ground_truth_check_{ts}.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nWrote {out_path}")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_ticket_results"}, indent=2))
