"""Live demo script for the video -- NOT part of the submitted system, just a walkthrough aid.
Run from the repo root: python scripts/demo_walkthrough.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.logging_store import DecisionLog
from src.pipeline import process_ticket
from src.retrieve import load_store

tickets = json.load(open("05_Datasets/development_tickets.json", encoding="utf-8"))
demo_ids = {"DEV-0001", "DEV-0003", "DEV-0005", "DEV-0023"}
demo_tickets = [t for t in tickets if t["ticket_id"] in demo_ids]

store = load_store()

# Start fresh every run. DecisionLog.record() uses a new random decision_id each call, so
# without this, re-running the demo (which you will, while rehearsing) just appends more rows
# on top of whatever's already in the file, and the coverage summary below inflates with each
# run even though only 4 tickets are ever processed. This is purely a quirk of this throwaway
# demo file, not of the real decision log used by evaluation/harness.py -- the actual gate
# run's metrics are computed from that run's in-memory results, not by querying accumulated
# history, so this never affected any graded number.
demo_db_path = Path("./storage/demo_decisions.db")
demo_db_path.unlink(missing_ok=True)
log = DecisionLog(db_path=str(demo_db_path))

for raw in demo_tickets:
    r = process_ticket(raw, log, store)
    print(f"\n=== {r['ticket_id']} ===")
    print(f"  intent={r['intent']}  confidence={r['confidence']:.2f}  action={r['action']}")
    print(f"  reason: {r['reason']}")
    if r["can_answer"]:
        print(f"  answer: {r['answer'][:150]}")
        print(f"  citations: {[c['doc_id'] for c in r['citations']]}")

print("\n\n--- Decision log coverage for this demo run ---")
print(log.coverage())
