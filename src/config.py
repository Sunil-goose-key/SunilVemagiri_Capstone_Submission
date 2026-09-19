"""Central place to read configuration from environment (Setup Guide §03)."""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/llama-3.1-8b-instruct")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./storage/chroma")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./storage/decisions.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
# Calibrated empirically, not guessed: chromadb 0.4.24's relevance_score_fn for this embedding
# model produces strongly negative scores (-0.35 to -0.40) for genuinely irrelevant queries and
# positive scores (0.09-0.61) for every relevant match probed during Day 2 retrieval testing.
# A floor of 0.35 (an arbitrary first guess) was filtering out real matches -- e.g. the correct
# passage for "my deployment keeps dying and rolling back" scored only 0.23. 0.05 sits safely
# above the observed irrelevant range and below every relevant hit seen so far; revisit against
# the full validation-set retrieval-hit-rate figure once the harness runs (Day 3/4).
RETRIEVAL_RELEVANCE_FLOOR = float(os.getenv("RETRIEVAL_RELEVANCE_FLOOR", "0.05"))
AUTO_RESPOND_ENABLED = os.getenv("AUTO_RESPOND_ENABLED", "true").lower() != "false"  # kill switch

# Intents that must never be auto-answered regardless of confidence. Verified directly
# against development_tickets.json rather than assumed from interview: these four classes
# account for a 100% must_not_auto_respond rate and, together, for all 87/500 (17.4%) flagged
# tickets. (Daniel's interview named security/billing/data-residency as concerns; the labelled
# data instead ties the hard-escalate flag to these specific classes -- including
# "unclear_request", i.e. if intent itself can't be confidently determined, escalate.)
MUST_ESCALATE_INTENTS = {
    "security_incident",
    "compliance_request",
    "feature_request",
    "unclear_request",
}
