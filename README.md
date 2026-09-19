# CloudServe Support Triage System

An intelligent support-ticket triage system built for the Forward Deployed AI Engineering
capstone. See `PROJECT_PLAN.md` for the full discovery-to-submission narrative and
`docs/architecture.md` for design decisions.

## What this is

CloudServe asked for a chatbot. Discovery (see
`02_Stage_Workbooks/Stage_1_Discovery_Workbook_FILLED.md`) found the actual problem is
retrieval/findability, not a knowledge gap: 71.4% of tickets are answerable from existing
documentation, and 49.1% of everything escalated to tier two was itself answerable from that
documentation. This system classifies, retrieves, routes, answers-with-citations, and
guardrails every ticket, logging every decision, and escalates anything it cannot defend.

## Setup

1. **Prerequisites**: Python 3.10+ (this project was built and tested against 3.10.9 — the
   pack's pinned dependency versions are not installable on 3.13, see the note below), Git.

2. **Create and activate a virtual environment**:
   ```
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```
   `requirements.txt` at the repo root is a corrected version of the pack's
   `06_Configuration/requirements.txt` — five genuine pin problems in the original file were
   found and fixed while getting a real environment working (each documented inline in
   `requirements.txt` and in the PRD revision log, not silently changed):
   - `openai==1.0.0` conflicted with `langchain-openai`'s own `openai>=1.10.0,<2.0.0` requirement.
   - `pydantic==2.0.0` is explicitly rejected by `fastapi==0.104.0`.
   - `langchain==0.1.0`/`langchain-community==0.0.10` had mutually inconsistent `langsmith`
     requirements once combined with a resolvable `langchain-core`.
   - `chromadb==0.3.21` imports `pydantic.BaseSettings`, a pydantic-v1-only API that doesn't
     exist once `pydantic==2.5.3` (itself required by the `fastapi` fix above) is installed.
   - `sentence-transformers==2.2.2` imports `cached_download` from `huggingface_hub`, which was
     removed from the version of `huggingface_hub` pulled in by this stack's other pins.

   Every one of these is re-pinned to the nearest verified-installable version within the same
   release line, not upgraded to an unrelated major version or a different library.

4. **Configure environment variables**:
   ```
   cp 06_Configuration/.env.example .env
   ```
   Edit `.env` and set `OPENROUTER_API_KEY` to a free OpenRouter (or Groq) key. `.env` is
   already in `.gitignore` — never commit it.

5. **Verify model access** (do this before anything else — most later problems trace back to
   skipping this step):
   ```
   python -c "from src.llm_client import chat; print(chat('You are a test.', 'Reply with the word ready.').text)"
   ```

6. **Build the retrieval index** (local embeddings, no API key needed):
   ```
   python -m src.retrieve build
   ```

## Running the system

Start the API:
```
python -m uvicorn src.api:app --reload
```

Submit a ticket:
```
curl -X POST http://localhost:8000/tickets -H "Content-Type: application/json" -d "{\"ticket_id\":\"T-1\",\"channel\":\"email\",\"subject\":\"Cannot deploy\",\"body\":\"My deployment keeps rolling back\"}"
```

## Running the full evaluation (the gate)

```
python -m evaluation.harness --input 05_Datasets/validation_tickets.json --output evaluation/results/
```

Takes any file matching the ticket schema via `--input`/`--output` — this is what allows the
harness to be pointed at a file never seen during development (A9). Writes a timestamped
metrics report (`evaluation/results/metrics_*.json`) and per-ticket results
(`evaluation/results/results.jsonl`) automatically, with no further manual work (A10).

## Running the tests

```
python -m pytest tests/ -v
```

## Project structure

```
src/            application code (ingest, classify, retrieve, route, generate, guardrails, logging, api)
prompts/        the versioned prompt library (build/, evaluation/, README.md register)
evaluation/     harness.py + results/
tests/          test suite
docs/           architecture notes
02_Stage_Workbooks/   the five stage workbooks (discovery, PRD, prompt library, sprint plan, revision log)
03_Reference/   setup/evaluation/governance reference docs + the governance framework draft
05_Datasets/    the pack's datasets (development/validation tickets, documentation, ground truth)
06_Configuration/  the pack's original requirements.txt/.env.example (kept for reference; see repo-root requirements.txt for the corrected, working version)
storage/        generated at runtime (Chroma index, SQLite decision log) — never committed
```

## Design decisions and known limitations

See `docs/architecture.md` and the PRD's assumptions table
(`02_Stage_Workbooks/Stage_2_PRD_v1.md`) for what was decided, why, and what's still open.
