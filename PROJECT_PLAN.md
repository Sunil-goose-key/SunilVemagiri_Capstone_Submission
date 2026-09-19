# CloudServe Capstone — Full Project Plan

## Context

This is a solo, three-week capstone: build an intelligent support-triage system for a
fictional company, CloudServe Solutions, whose support function is failing (8–12hr first
reply against a 2hr SLA, 42% first-contact resolution, 3.2/5 CSAT). The client asked for "a
chatbot"; the brief is explicit that building literally that fails the assignment — the real
job is discovery-driven: find why tickets aren't self-resolving, design a system that answers
what it can defend and escalates the rest with useful context, and prove it works against data
you've never seen.

**Status: the pack is now on disk and verified.** `02_Stage_Workbooks/`, `03_Reference/`,
`04_Submission/`, `05_Datasets/` and `06_Configuration/` all exist and every file in them has
been read. The only pieces not physically in this repo are `00_PROJECT_INSTRUCTIONS.docx` and
the `01_Read_First/` folder contents (Start Here, Project Brief, Build Specification, README)
— those were supplied as pasted documents earlier in this conversation and have already been
analyzed, so their absence from disk does not block anything. There is still no git repo.

## What each document established (reading order)

0. **Capstone Pack Contents** — confirmed this is a 6-folder pack plus a root
   `00_PROJECT_INSTRUCTIONS.docx` that should be read before Start Here (rules, deadline,
   submission format, marking) — not yet obtained, but nothing else depends on it.
1. **Start Here** — six stages each feeding the next (discovery → PRD → prompts → sprint plan
   → build+revision → submission), non-skippable. Mandatory PRD revision once during build,
   logged. Marking weights: Implementation 35%, Evaluation 20%, Discovery 15%, Requirements
   10%, Governance 10%, Communication 10%.
2. **Project Brief** — "chatbot is a delivery mechanism, not a fix"; six components (Ingest →
   Classify → Retrieve → Route → Generate → Validate) over three cross-cutting concerns (audit
   log, monitoring, feedback loop); three-layer architecture; routing threshold must be
   *derived from data*; business/technical/governance targets; risk matrix.
3. **Build Specification** — the software is graded against this. A pass/fail gate runs
   before anything else: full validation set, unattended, clean checkout. Twelve acceptance
   criteria (A1–A12), pass/fail, no partial credit. Day-by-day week-two checkpoints.
4. **README** — six-stage table with due dates, ordered task list, time allocation
   (22% discovery / 50% build / 18% eval+governance / 10% report+video), and the harness must
   take `--input`/`--output` args since the graded run uses a file never seen.

## Every workbook and reference document, now read in full

- **Stage 1 Discovery Workbook** — six sections: (1) what each of the 5 interviews told you
  vs. what they didn't know, plus a table of ≥3 places the transcripts disagree, resolved by
  the ticket data; (2) counted figures from `development_tickets.json` (channel/intent/urgency
  split, FCR, satisfaction, % answerable from docs, non-fluent segment outcomes, repeat
  contacts); (3) volume vs. effort per ticket category, and Sofia's workflow broken into
  timed, automatable steps; (4) what CloudServe actually measures vs. what Marcus said he
  actually cares about (FCR, not response time — a key transcript detail); (5) a data/risk
  register per source (tickets, docs, past resolutions, customer records); (6) the problem
  statement, built only from cited rows, non-technical, sanity-checked against all 5
  transcripts.
- **Stage 2 PRD Template** — document control, one-paragraph problem statement (copied from
  the workbook, not rewritten), a user table (customers / T1 / T2 / head of support),
  functional requirements (FR-xx with Must/Should/Could/Won't priority + discovery citation +
  acceptance criteria), non-functional requirements (latency, availability, accuracy, privacy,
  auditability, fairness, cost), explicit out-of-scope table, assumptions-and-consequences
  table, success measures (FCR 42%→60%, reply time, CSAT 3.2→4.0, escalation rate), open
  questions with owner+date.
- **Stage 3 Prompt Library** — four prompt categories (specification / build / review /
  evaluation); a per-requirement spec table (inputs/outputs/acceptance criteria); a prompt
  register (one block per prompt: name, category, requirement served, version, model,
  inputs/output format, known weaknesses, change history, full text); a "what makes a prompt
  worth keeping" checklist (role/task separation, delimited inputs, exact output format,
  explicit "don't know" behavior, representative examples, positive constraints); explicit
  instruction on defending against prompt injection from ticket text; a traceability check
  (FR → spec → prompts → test case → gaps) before moving to Stage 4.
- **Stage 4 Sprint Plan** — capacity table per week; a concrete backlog already partly
  populated that this plan adopts directly (see Backlog below); a week-two and week-three
  daily table; a "what you will drop if you run out of time" cut-order table; a daily
  three-question che ck-in log.
- **Stage 5 PRD Revision Log** — compulsory. Revision summary (version 2.0, date, who,
  reviewer, counts changed/added/removed), one row per change (before/after/trigger/agreed
  by), a table of which v1 assumptions held or failed, a table of things deliberately left
  unchanged, and a five-question reflection that feeds the report directly.
- **Evaluation Framework** — three-tier pyramid (technical → business → governance, in that
  priority order for what the client cares about, though governance is pass/fail). Ships
  runnable code for FCR, reply-time mean/median/p95, calibration-by-confidence-band, latency
  p95. Targets: FCR ≥60% (baseline 42%), reply <5min (baseline 8-12hr), CSAT ≥4.0 (proxy via
  human-rubric review, baseline 3.2), escalation ≤30% (baseline 58%), repeat contacts halved;
  classification precision ≥85%, hallucination ≤5% (2 human raters, ≥50 samples), citation
  accuracy ≥95%, latency p95 <3s, availability ≥99.5%; governance conditions are zero-tolerance
  (0 PII leaks, <5pp cross-group variation, 100% decision-log coverage, confidence calibrated
  within 5pts of observed accuracy). Explicitly: develop against the 500 dev tickets, self-
  check against the 80 validation tickets *as often as you like*, and report a caveat sentence
  ("the figures above should be treated with caution because...").
- **Governance Framework** — the exact minimum decision-log JSON record (see Decision Log
  schema below); a risk register template pre-seeded with 8 risks (R-01..R-08: wrong-but-
  confident answers, PII leak, prompt injection, unequal quality, stale docs, provider outage,
  latency under load, cost blowup); a fairness-audit table by segment (tier, region, fluency,
  length) — explicitly flags that retrieval-based systems tend to underperform on non-fluent
  English; five named guardrails (private data / grounding / instruction-integrity / tone-
  scope / confidence-floor), each must **block**, not warn; a 6-step incident-response
  template; a kill-switch spec (mechanism, who can operate it, time-to-effect, in-flight
  tickets, how it's tested); a closing declaration ("this system must never...").
- **Setup Guide** — the exact order to work through (prereqs → venv → deps → protect+fill
  `.env` → verify one real model call returns text → build the vector store) and warns not to
  skip the "verify a real call returns text" step. Ships working code for: venv creation, key
  protection (`.env` in `.gitignore` *before* the key is written), a live OpenRouter call,
  Chroma ingestion (chunk_size=800, chunk_overlap=120, `all-MiniLM-L6-v2`, explicitly says try
  ≥2 chunk configs and record which was chosen and why), the SQLite decision-log DDL,
  Prometheus counters/histograms + a `prometheus.yml` scrape config, a GitHub Actions
  `ci.yml`, the exact repo tree (see Project Structure below), and a troubleshooting table
  (venv not active, `.env` not loaded, bad key, Chroma path mismatch, chunks too large, first-
  run embedding download, "works locally fails in CI").
- **Effort Log** — filled in every second day, task-level not weekly-summary, actual hours
  including dead ends; a stage-by-stage planned-vs-actual table; week 1/2/3 daily entry
  tables; a "5 largest items, estimate vs. actual" table; a 4-question retrospective; a
  signed declaration.
- **Submission Guide** — single archive `FirstnameLastname_Capstone_Submission.zip` (no
  spaces/dates), exactly four top-level folders in order: `01_Video`, `02_Report`,
  `03_Workbooks`, `04_Source_Code`. Video: ~20min (18–22 marked), visible on camera at
  open/close, ≥7min live demo (a success, an escalation, a guardrail block, evidence of the
  unattended run), 1080p+, audible, legible fonts, filename
  `FirstnameLastname_Capstone_Video.mp4`, with a prescribed minute-by-minute structure
  (problem → discovery findings → architecture → live demo → results → governance → next
  steps). Report: single PDF, 20–30 pages excluding appendices, prescribed 10-section order
  (exec summary → problem → discovery findings → requirements → architecture → implementation
  → evaluation → governance → PRD revision → conclusions), full prose not bullet-dumps, every
  figure numbered/captioned/referenced, a declaration of AI tool use required, filename
  `FirstnameLastname_Capstone_Report.pdf`. Workbooks: all 5 + effort log, task-level entries
  throughout, not skeletons. Source code: the repo tree from the Setup Guide, must run from a
  clean checkout; the check procedure explicitly includes searching for committed credentials,
  reviewing commit history for steady work vs. one big commit, and checking attribution of any
  AI-generated code. Final pre-submission checklist provided (15 items) — work through it the
  day before, not the day of.
- **Dataset Guide** (`05_Datasets/Dataset_Guide.docx`) — resolves an apparent tension between
  the Project Brief/README wording: **`validation_tickets.json` (80 tickets) may be used and
  re-checked as often as you like during development — it is not the single-use protected
  set.** The single-use, never-distributed set is the separate 120-ticket hidden set applied
  only at final assessment. Also gives the exact schemas (below) and dataset composition: 500
  dev tickets, 22 intent classes (uneven), channel order email > chat > docs_comment > forum,
  tiers ~50% standard / ~33% business / rest enterprise, ~25% non-fluent, **~75% answerable
  from documentation**, ~2/3 expected auto-respond. Confirms `must_not_auto_respond` is a
  labelled field for classes that should always escalate (safety, not scoring).
- **Stakeholder Interviews** (`05_Datasets/Stakeholder_Interviews.docx`) — full transcripts,
  now read. Key discovery signal already visible, to verify against the ticket data in Stage 1
  rather than assume:
  - **Marcus (Head of Support)**: cares about FCR more than response time even though response
    time is the SLA metric he reports; admits he doesn't actually know the ticket breakdown;
    hard failure condition is "sends something wrong to a customer"; compliance review this
    autumn means decisions must be explainable; enterprise tier must not silently get worse
    service.
  - **Sofia (T1 agent)**: estimates ~70% of tickets are ones she's answered before; the
    documentation itself is fine, but *internal search fails on phrasing* so agents keep
    private snippet files instead of searching docs (a specific, checkable claim); escalates
    on low confidence, unknown answers, or anything security-flagged; wants a system that
    hands her a draft + relevant page rather than replacing her; flags non-fluent-English
    tickets as slower and worse-scoring, and thinks nobody has measured this.
  - **Daniel (T2 engineer)**: claims roughly half of what reaches him could have been resolved
    at T1 with more confidence or better findability — a direct, checkable contradiction of
    the escalation-rate figure Marcus reports; escalations arrive with zero context today
    (this is exactly why the Build Spec requires escalations to carry drafted summary +
    sources); warns that private snippet files contain stale/wrong answers that would get
    "learned" if used as training signal; flags security, billing/refund commitments, and data
    residency as categories that must never be automated.
  - **Ines (technical writer)**: 29 articles, reviewed on rotation, accurate within that cycle;
    the failure is *internal keyword search not matching customer phrasing* ("my deployment
    keeps dying" vs. article titled "resolving container health check failures") — this is
    direct evidence a semantic/embedding retrieval layer is the right response to the client's
    actual problem, not just an assumption; wants citations so a wrong answer can be traced to
    "article wrong" vs. "system misread it"; confirms feature requests, roadmap questions, and
    genuinely novel incidents have no article to retrieve (so "correctly say I don't know" is
    load-bearing, not decorative).
  - **Ravi (customer)**: waiting cost is not uniform — a blocked-deployment ticket costs him
    far more than a "how does pagination work" ticket, same queue; wants transparency about
    what's automated so he can calibrate trust and verify before acting; worried about the
    business-vs-enterprise tier response-time gap widening and surfacing at renewal.
  - At least three disagreements to resolve with data per the workbook's own instruction:
    (1) Marcus's reported escalation rate vs. Daniel's claim that ~half of escalations were
    T1-resolvable; (2) "documentation is bad" (implied) vs. Sofia/Ines's shared view that the
    docs are fine and *findability* is the actual defect; (3) Marcus's "broadly" guess at
    ticket-type breakdown vs. what `development_tickets.json` actually shows.

## Concrete technical scaffolding already specified (adopt rather than re-derive)

**Project structure** (from Setup Guide §08 — matches what Submission Guide requires):
```
README.md, requirements.txt, .env.example, .gitignore (.env + storage/)
src/  ingest.py  classify.py  retrieve.py  route.py  generate.py  guardrails.py
      logging_store.py  api.py
prompts/  build/  evaluation/  README.md (the register, versioned)
tests/
evaluation/  harness.py  results/
docs/  architecture.md
data/   (small samples only — the real dataset JSON files stay out of git per size/PII norms
         unless confirmed safe; check before committing 05_Datasets/*.json wholesale)
storage/  (generated at runtime, never committed)
.github/workflows/ci.yml
```

**Pinned dependencies** (`06_Configuration/requirements.txt`, already in repo): langchain
0.1.0, langgraph 0.0.20, langchain-community 0.0.10, langchain-openai 0.0.7, chromadb 0.3.21,
sentence-transformers 2.2.2, pandas 2.0.0, numpy 1.24.0, scikit-learn 1.3.0, fastapi 0.104.0,
uvicorn 0.24.0, pydantic 2.0.0, openai 1.0.0, requests, python-dotenv, aiohttp,
prometheus-client, python-json-logger, psycopg2-binary, SQLAlchemy 2.0.0, pytest(+asyncio+cov),
flake8, black, jupyter, ipython, tqdm, PyYAML.

**Env vars** (`06_Configuration/.env.example`, already in repo): `OPENROUTER_API_KEY`,
`MODEL_NAME=meta-llama/llama-3.1-8b-instruct`, `EMBEDDING_MODEL=all-MiniLM-L6-v2`,
`CHROMA_PATH=./storage/chroma`, `DATABASE_URL=sqlite:///./storage/decisions.db`,
`LOG_LEVEL=INFO`, `CONFIDENCE_THRESHOLD=0.80` (starting point, to be re-derived from data per
the Brief's explicit instruction), `RETRIEVAL_TOP_K=5`.

**Ticket schema** (`Dataset_Guide.docx`): `ticket_id`, `channel` (email/chat/docs_comment/
forum), `subject`, `body`, `received_at`, `customer_id`, `customer_name`, `customer_tier`
(enterprise/business/standard), `customer_region`, `language_fluency` (fluent/non_fluent),
`labels.{intent (22 classes), urgency (high/medium/low), expected_route (auto_respond/
escalate), answerable_from_docs, expected_doc_ids, must_not_auto_respond}`,
`history.{first_contact_resolution, resolution_time_minutes, csat_rating, escalated,
repeat_contact}` — the `history` block is the human baseline to beat, **not** a label to
imitate (imitating a 3.2 CSAT is explicitly called out as the wrong objective).

**Documentation schema**: `doc_id`, `title`, `category` (8 categories: authentication,
deployment, api, performance, billing, data, security, account/onboarding/integration),
`applies_to`, `content` (markdown, each article has a consistent title/symptoms/causes/steps/
notes structure — a hint for chunking strategy), `related_docs`, `last_reviewed_days_ago`.

**Ground truth schema**: `ticket_id`, `intent`, `expected_doc_ids`, `reference_response`,
`must_mention` (auto-checkable coverage points), `must_not_claim` (auto-checkable safety
violations), `written_by`.

**Decision log record** (`Governance_Framework.docx` — implement this shape in
`logging_store.py`):
```json
{
  "decision_id": "...", "timestamp": "...", "ticket_id": "...",
  "stage": "classification|routing|generation|validation",
  "input_summary": "...", "model": {"name": "...", "version": "..."},
  "prediction": {"value": "...", "confidence": 0.00},
  "alternatives": [{"value": "...", "confidence": 0.00}],
  "sources_used": [{"doc_id": "...", "score": 0.00}],
  "threshold_applied": 0.00, "action_taken": "auto_respond|escalate|block",
  "reason": "human readable", "guardrail_results": {"pii": "pass", "grounding": "pass", "tone": "pass"},
  "prompt_version": "PR-02 v1.3", "requirement_ids": ["FR-03", "FR-07"]
}
```

**Sprint backlog** (`Stage_4_Sprint_Plan.docx` §2 — adopt these IDs directly, add hour
estimates and priorities in the actual workbook):
B-01 env/dependency setup → B-02 data loading/normalisation → B-03 chunking+embedding
→ B-04 vector store/retrieval → B-05 evaluation harness (parallel with B-02) → B-06
intent/urgency classifier (parallel with B-02) → B-07 routing logic/thresholds → B-08 answer
generation w/ citations → B-09 guardrails/validation → B-10 decision logging → **B-11 first
full unattended run over the hidden(validation) evaluation set — THE GATE** → B-12 monitoring/
dashboards → B-13 CI pipeline → B-14 fairness audit → B-15 report/video/submission package.

## Immediate blocker, resolved

The only remaining gap is `00_PROJECT_INSTRUCTIONS.docx` and the four `01_Read_First/` files
— not physically on disk, but already fully analyzed via chat. Nothing is blocked by their
absence; add them to the repo later purely for completeness/reference if convenient.

## Execution timeline: compressed to 5 working days

**Actual hands-on-keyboard work is compressed from 3 weeks to 5 working days.** The
deliverables below are unchanged in scope and structure — all six stages, all workbooks, the
same report/video/governance requirements — the templates aren't date-stamped, so filling them
fast doesn't change what has to be in them. The effort log will record genuine dates/hours
(compressed), not a fabricated 3-week calendar.

| Day | Covers (original steps) | Produces |
|---|---|---|
| 1 | Setup + steps 6–7 (Discovery) | Env/git/venv ready; Discovery Workbook complete; data-verified problem statement |
| 2 | Steps 8–11 (Requirements, Architecture+Risk, Prompt Library, Sprint Plan) | PRD v1; architecture + initial risk register; full prompt library; sprint backlog |
| 3 | Step 12, Build Spec Days 1–3 | `ingest.py`, `retrieve.py`, `classify.py`, `route.py`, `logging_store.py` |
| 4 | Step 12 (Days 4–5), 13, 14, 15 | `generate.py`, `guardrails.py`, `api.py`, `evaluation/harness.py`; the gate run over `validation_tickets.json`; PRD revision |
| 5 | Steps 16–19 | Governance + fairness audit; monitoring + CI; video + report + effort log; packaged submission |

**Correction on step 14**: the true 120-ticket hidden set is never distributed and is applied
by the grader post-submission — it cannot be run by us. Day 4's "evaluation against the hidden
set" is, honestly, a clean single run against `validation_tickets.json`, reported as a
validation-set result and clearly labelled as such in the report, distinct from the graded run.

### Day 1 progress log (setup + discovery)

- `git init` done; `.gitignore` created (`.venv/`, `.env`, `storage/`, etc.).
- Python 3.13 (system default) is incompatible with the pack's pinned dependencies
  (`pandas==2.0.0` has no cp313 wheel and its legacy sdist build fails). Recreated the venv
  with **Python 3.10.9** (available via `py -3.10`), matching the Setup Guide's stated minimum.
- The pack's `06_Configuration/requirements.txt` has two real pin conflicts, independent of
  the Python version — fixed in a corrected root-level `requirements.txt` (kept alongside the
  original pack copy for reference):
  - `openai==1.0.0` conflicts with `langchain-openai==0.0.7`, which requires
    `openai>=1.10.0,<2.0.0` → bumped to `openai==1.12.0`.
  - `pydantic==2.0.0` is explicitly excluded by `fastapi==0.104.0` (which rejects
    2.0.0/2.0.1/2.1.0) → bumped to `pydantic==2.5.3`.
  - Both are documented here and will go in the PRD revision log / setup notes as pack
    corrections, not design deviations.
- `.env` created from `.env.example`, already `.gitignore`d. **Still needed from you**: a real
  free OpenRouter or Groq API key pasted into `.env` — I cannot generate one. Once it's there,
  the Setup Guide's verification call (one request that must return real text) is the next
  gating step before any build work.
- Discovery is done and data-verified, not estimated — see
  `02_Stage_Workbooks/Stage_1_Discovery_Workbook_FILLED.md` for the completed workbook,
  computed directly from `development_tickets.json` (n=500). Headline verified findings:
  - 71.4% of tickets are answerable from the existing 29-article documentation.
  - 49.1% of all escalated tickets were themselves answerable from documentation — confirming
    Daniel's estimate almost exactly, and reframing the core problem as retrieval/findability,
    not knowledge or agent competence.
  - Non-fluent-English tickets do **not** score worse in the current human-handled baseline
    (contradicts Sofia's stated belief) — flagged as a risk to actively test once retrieval is
    introduced, not a settled non-issue.
  - Enterprise tier already has the **worst** FCR of any tier today (37.3% vs. 48.2% business),
    predating any automation — reframes Marcus/Ravi's "don't make it worse" concern into "this
    already needs active repair."
  - Full disagreement-resolution table, effort-vs-volume breakdown, and the finished
    one-paragraph problem statement are in the filled workbook file.

### Day 2 progress log (requirements, architecture, prompts, sprint plan, build starting early)

- `02_Stage_Workbooks/Stage_2_PRD_v1.md` — PRD v1 written, FR-01..FR-15 + NFR-01..07, each
  citing discovery evidence or acceptance criteria.
- **Correction found while writing FR-07**: the interview-derived guess that billing/data-
  residency must hard-escalate was checked against the labelled data and was wrong. The real,
  verified signal: `must_not_auto_respond` is a 100%-deterministic function of exactly four
  intent classes — `security_incident`, `compliance_request`, `feature_request`,
  `unclear_request` — accounting for all 87/500 (17.4%) flagged tickets. Updated the PRD, and
  `src/config.py`'s `MUST_ESCALATE_INTENTS` reflects this verified set, not the interview
  guess. This resolves what was an open PRD question into a closed one on Day 2 itself.
- `docs/architecture.md` — component/layer decisions with reasoning tied to discovery, not
  the brief's diagram followed blindly.
- `03_Reference/Governance_Framework_DRAFT.md` — risk register (R-01..R-08) filled with real
  mitigations; guardrail spec; incident response; kill switch; fairness audit table structured
  (real figures pending Day 4 build).
- `prompts/` — `build/classify.txt`, `build/generate.txt`, `evaluation/grounding_check.txt`,
  and `prompts/README.md` (the register, with traceability back to FR-03/04/09/10/11).
- `02_Stage_Workbooks/Stage_4_Sprint_Plan_v1.md` — backlog B-01..B-15 with real hour estimates
  fitted to Days 3–5, cut-order table.
- Started Day 3 work early: `src/models.py`, `src/ingest.py`, `src/config.py`,
  `src/logging_store.py`, `src/llm_client.py` (resilient OpenRouter client with retry/backoff
  for A11), `src/retrieve.py`, `src/classify.py` (with the verified 22-class intent list, not
  a guessed one — see below), `src/route.py`, `src/generate.py`, `src/guardrails.py`,
  `src/pipeline.py` (orchestrates all stages + decision logging), `src/api.py`,
  `evaluation/harness.py` (the A9/A10 gate harness), root `README.md`, `tests/` (21 passing so
  far, no network dependency), `.github/workflows/ci.yml`.
- **Verified the real 22 intent classes directly from data** rather than guessing plausible
  ones — `src/classify.py`'s `INTENT_CLASSES` now matches `development_tickets.json` exactly
  (account_access, api_key_issue, api_usage_question, authentication_failure, billing_query,
  compliance_request, configuration_help, data_export, data_residency, database_issue,
  deployment_failure, feature_request, integration_help, onboarding,
  performance_degradation, quota_or_overage, rate_limit, rollback_request, security_incident,
  sso_configuration, unclear_request, webhook_issue).
- **Day 1 ingest checkpoint passed**: one ticket normalized per channel, printed successfully,
  no errors.
- **Four real, documented dependency-pin corrections** found and fixed while getting a working
  environment (each is a genuine bug in the pack's `requirements.txt`, independent of anything
  we chose — see `requirements.txt`'s inline comments and the list below). This is exactly the
  kind of engineering judgement call the brief expects to be recorded, not hidden:
  1. `openai==1.0.0` vs. `langchain-openai==0.0.7`'s own `openai>=1.10.0,<2.0.0` requirement.
  2. `pydantic==2.0.0` explicitly excluded by `fastapi==0.104.0`.
  3. `langchain==0.1.0`/`langchain-community==0.0.10` had mutually inconsistent `langsmith`
     requirements once combined with a resolvable `langchain-core` — re-pinned within the same
     0.1.x line to `langchain==0.1.20`/`langchain-community==0.0.38`/`langchain-openai==0.0.8`.
  4. `sentence-transformers==2.2.2` imports a `huggingface_hub` function removed well before
     the version pulled in by the (also pinned) modern `transformers`/`torch` — bumped to
     `sentence-transformers==3.0.1`.
  5. `chromadb==0.3.21` imports `pydantic.BaseSettings`, a pydantic-v1-only API — fundamentally
     incompatible with `pydantic==2.5.3` (itself required by `fastapi==0.104.0`, see #2).
     Bumped to `chromadb==0.4.24`.
- **Retrieval relevance floor recalibrated with evidence, not guessed**: irrelevant queries
  score -0.35 to -0.40 with this embedding/chromadb combination; every relevant match tested
  scored +0.09 to +0.61. The initial 0.35 floor was filtering out correct answers (e.g. the
  right passage for a deployment-rollback query scored only 0.23). Recalibrated to 0.05.
  Verified: a real query now correctly retrieves `DOC-DEPLOY-002`/`DOC-DEPLOY-001`.
- **A real API key was added and live model access verified** (Setup Guide's required first
  check) — a test call returned "Ready." as expected.
- **Day 3 checkpoint run**: 20 real dev tickets through the full
  ingest→classify→retrieve→route→log pipeline. Every decision has a reason; decision-log
  coverage matched exactly (20/20 distinct tickets logged); hard-escalate intents
  (`compliance_request`, `feature_request`, `security_incident`) correctly routed to escalate
  regardless of confidence.
- **A genuine A5-compliance bug found and fixed**: classification calls an LLM, and at default
  sampling temperature, re-running the same 20 tickets produced *different* predictions and a
  different accuracy figure run-to-run — which would fail A5's literal test procedure ("run the
  same ticket twice, the decision does not change") if triggered during grading. Fixed by
  calling the model at `temperature=0`/`seed=0` **and** adding a disk-backed response cache
  keyed on exact prompt content (`src/llm_client.py`), so a repeated call for the same ticket
  returns the identical recorded response. Verified: two full runs over the same 20 tickets now
  produce byte-identical output. This also conserves the free-tier allowance during
  development, per the Setup Guide's own recommendation.
- **A real classifier confusion found and fixed with a prompt change, not a code patch**: two
  `feature_request` tickets (a must-escalate class) were confidently (0.95) misclassified as
  `billing_query`, because both were phrased as billing-adjacent capability requests ("please
  add per-project spend caps"). This is safety-relevant, not just a scoring miss — a
  misclassified must-escalate intent skips the hard-escalate path entirely. Fixed by adding an
  explicit disambiguation rule to `prompts/build/classify.txt` (PR-01 → v1.1: requests to add
  capability are `feature_request` even in billing language). Re-tested: both tickets now
  classify correctly. Classification accuracy on this 20-ticket sample: **19/20 (95%)** after
  the fix and with temperature=0, comfortably above the NFR-03 target of 85% — though a
  20-ticket sample is too small to treat as the reportable figure; the real number comes from
  the full gate run in Day 4.

### Day 4 progress log (the gate, a real bug found and fixed, A7 proven end-to-end)

- **First full gate run** (`evaluation.harness` over all 80 `validation_tickets.json` tickets,
  unattended): 80/80 processed, decision-log coverage reconciled exactly, retrieval hit rate
  96.2%, weighted classification accuracy 81.25%, latency mean 5.3s / median 3.3s / **p95
  11.8s (above the NFR-01 target of 3s — a real, honestly-reported miss, see below)**.
- **A genuinely serious correctness bug found by the gate run itself, not by inspection**: 9 of
  80 tickets (11.25%) were routed to `auto_respond` with an **empty answer** — retrieval
  returned candidate passages and classification confidence was high, but generation had
  correctly declined to answer (`can_answer=False`, e.g. the retrieved passages didn't
  actually cover the question). `route.decide()` never checked `generation.can_answer` at all
  — it only checked whether *any* passage was retrieved. This means the system would have sent
  blank responses to real customers, which is worse than escalating. **Fixed** in
  `src/route.py`: routing now escalates whenever generation could not ground an answer,
  regardless of confidence or retrieval non-emptiness. Regression test added
  (`test_route.py::test_generation_could_not_answer_escalates...`). This is exactly the class
  of failure the Build Spec's A9 warning describes — invisible testing one ticket at a time,
  visible immediately at full-set scale.
- **Confirmed by re-running the full gate after the fix**: auto_responded dropped from 66→57
  and escalated rose from 14→23 (exactly the 9 affected tickets, now correctly escalating).
  FCR (this run) moved from 82.5%→71.2%, escalation 17.5%→28.8% — a real, explainable change,
  not noise: the pre-fix 82.5% FCR was partly counting blank non-answers as "resolved."
  Classification accuracy and retrieval hit rate were unaffected (routing-only fix). The
  re-run's latency figures (~0.03s) are a caching artifact (identical tickets, cached
  classify/generate responses) — **the first run's cold latency (p95 11.8s) is the honest
  figure for the report**, not the re-run's.
- **A7 (guardrail blocking) proven end-to-end, honestly**: live adversarial testing (a prompt-
  injection attempt demanding a fabricated refund confirmation) was correctly defeated by the
  generation prompt itself — the model declined rather than complying, which is good defense-
  in-depth but doesn't exercise the guardrail's own block path, since a well-aligned model
  rarely produces the unsafe content guardrails exist to catch. Rather than claim A7 is
  satisfied by a demo that never actually blocks anything, added
  `tests/test_pipeline_guardrail_block.py`: it constructs a deliberately unsafe
  `GenerationResult` (a refund guarantee; a leaked foreign customer ID) and runs it through the
  *real* `guardrails.run_all()` + `route.decide()` code path exactly as `pipeline.py` calls
  them — confirming `tone_scope` and `private_data` both correctly **block**
  (`action == "block"`), not just warn. The video's live demo will use this same constructed
  scenario, since "run a real ticket through the live model" didn't reliably trigger it given
  how well the generation prompt already defends itself.
- **Honest limitation to report**: p95 latency of ~11.8s (cold) is well above the 3s NFR-01
  target. Root cause: two sequential LLM calls per ticket (classify, then generate) against a
  free-tier model, no parallelization. Reported plainly with a named cause, per the Evaluation
  Framework's own guidance to state a caveat sentence rather than omit an unfavourable figure.
- **A second generation defect found and fixed the same day**: inspecting the "escalated but
  answerable_from_docs=true" subset after the routing fix showed 7 tickets where the *correct*
  passage was retrieved (one, `DOC-DEPLOY-001`, literally titled for the ticket's exact
  symptom) but generation still declined, reasoning that the ticket hadn't pre-stated a detail
  the passage's own resolution steps explain how to check. Fixed with an explicit prompt rule
  (`prompts/build/generate.txt` → v1.1). Re-tested: 7/7 now answer correctly with valid
  citations.
- **Final gate run** (after both fixes, `metrics_20260906T172820Z.json`): 80/80 processed, 0
  blank auto-responses (down from 9), **FCR 82.5%**, **escalation 17.5%** (14/80), retrieval
  hit rate 96.2%, weighted classification accuracy 81.25%, latency mean 2.18s / median 2.08s /
  p95 5.75s (mixed cached-classification + fresh-generation run; the fully-cold figure is the
  first run's p95 11.8s, the more representative worst case). **The core discovery metric —
  share of escalations still avoidable per ground truth — dropped from the 49.1% baseline to
  28.6% (4/14), and 3 of those 4 are intentional safety escalations on must-escalate intents,
  not defects, leaving a genuine miss rate of 1/14 (7.1%).** This is the direct, quantified
  evidence that the system fixed the problem discovery identified, not just a proxy metric.
- **Fairness audit run on the final results**: the non-fluent-English risk flagged in
  discovery did not materialize (73.7% vs. 70.5% resolution, non-fluent slightly ahead, 3.2pt
  gap — passes the 5pt target). A different, statistically credible gap appeared on customer
  tier: standard (n=42, the largest segment) resolved at 64.3% vs. 87.5% enterprise — a 23.2pt
  gap on a sample large enough to be a real signal, flagged as the priority open finding rather
  than smoothed over. Full table and honest caveats about small-sample segments (enterprise
  n=8, Latin America n=7) in `03_Reference/Governance_Framework_DRAFT.md` §3.
- All three gate runs, the routing fix, and the generation fix are documented as dated PRD
  revision entries in `02_Stage_Workbooks/Stage_5_PRD_Revision_Log_v1.md` §4b, with the
  before/after evidence for each.

**Addendum (2026-09-17), added without editing the entry above**: while finalizing the
submission, re-ran `evaluation.fairness_audit` against a fresh harness pass and found the
segment-level numbers in the entry above no longer reproduce — `results.jsonl` has no per-run
filename, so it gets overwritten by every harness invocation, and several reruns happened
between this entry (Day 4) and submission for unrelated reasons. Fresh, current numbers:
standard tier 69.0% (n=42) vs. business 93.3% (n=30, now the best tier, not enterprise), a
24.3pt gap; non-fluent English 84.2% (n=19) vs. fluent 78.7% (n=61), a 5.5pt gap, still passing.
The qualitative findings above are unchanged and reproduce — standard tier still trails by 20+
points, non-fluent English still isn't disadvantaged — only the exact percentages moved. The
report, PRD and governance doc were updated to the fresh numbers; this historical entry is left
as originally written, since it accurately reflects what Day 4's run actually showed at the
time.

**Second addendum (same day), a real correction to how this finding was being framed**: a
sharper look at *why* standard tier trails revealed most of the 24.3pt raw gap is not a service
defect. Standard tier submits tickets whose true category always hard-escalates regardless of
system quality (`unclear_request`, `security_incident`, `feature_request`, `compliance_request`)
at 26.2% (11/42), versus 6.7% business and 12.5% enterprise — a ticket-mix difference, not
unequal treatment. Restricting to tickets actually eligible for auto-answer, the real,
like-for-like gap is 93.5% (29/31) vs. 100% for both other tiers, fully explained by one
retrieval miss (`VAL-0029`) and one already-disclosed FR-16 trade-off (`VAL-0037`) — nothing
else hiding underneath. The report and governance doc now present both numbers (raw and
eligible-only) rather than only the raw one, which on its own overstated this as a fairness
defect.

### Day 5 progress log (a fourth, governance-critical defect found live, not by any test)

While running the pipeline live on real tickets to prepare for the video (not while writing
code or reading the metrics report), ticket `DEV-0003` — an enterprise customer's auditor
asking about access-record retention, true intent `compliance_request`,
`must_not_auto_respond=true` — was watched going the wrong way in real time: classified as
`data_export` at 0.95 confidence, and auto-answered.

- **Root cause**: `classification.must_not_auto_respond` and the `intent in
  MUST_ESCALATE_INTENTS` check in `route.decide()` are both derived from the *same single*
  classified `intent` value. Neither is actually independent of the other, so a misclassification
  defeats both simultaneously. This is precisely the risk the Governance Framework's own
  declaration had already named as "the most likely way it could still cause harm" — it had
  been sitting there since Day 2 as a documented risk, unconfirmed, until this session.
- **Fix (FR-16)**: added `route._mentions_safety_sensitive_topic()`, a deterministic keyword
  scan over the ticket's own raw text (audit/compliance/legal/security-incident terms),
  escalating regardless of predicted intent. Deliberately not another model call — it reads
  the ticket directly, so it can't fail for the same reason the thing it's meant to catch fails.
  Regression tests added (`test_route.py`), using the real `DEV-0003` ticket text.
- **Verified by a fourth full gate run** (`metrics_20260907T173221Z.json`): escalation rose
  17.5%→20.0% (14→16/80) and FCR fell 82.5%→80.0% — both expected and correct, not a
  regression: two tickets now escalate that didn't before. One (`VAL-0009`) is the same class
  of bug as `DEV-0003`, now correctly caught. The other (`VAL-0037`) is a disclosed
  efficiency trade-off — its true label didn't strictly require escalation, but the keyword
  ("compliance") fired anyway; accepted as a safety-margin cost, not hidden. **The governance
  payoff: 0/80 tickets with a true `must_not_auto_respond=true` label are now missed, down
  from 1/80.** The core discovery metric (share of escalations still avoidable) moved to
  31.2% (5/16), with a genuine miss rate of 1/16 (6.25%) — a *better* real-miss figure than
  before this fix (1/14, 7.1%), despite the higher escalation rate.
- All of PRD (FR-16, success measures), the revision log (§4c), the Governance Framework
  (risk R-09, guardrails table, the declaration's "most likely way it could still cause harm"
  answer), and the report draft were updated to match — this was checked for consistency
  across documents, not just fixed in code.

## Day-by-day detail (content unchanged from the original 3-week structure, just compressed)

**Day 1 — setup + Discovery.** ✅ Env/git progress logged above. Discovery workbook filled
(`02_Stage_Workbooks/Stage_1_Discovery_Workbook_FILLED.md`), problem statement written and
sanity-checked against all 5 transcripts. Effort log started.

**Day 2 — Requirements, Architecture+Risk, Prompt Library, Sprint Plan.**
- PRD v1: one FR per discovery-cited behavior; provisional confidence threshold 0.80 (per
  `.env.example`), to be re-derived from real precision/recall once the classifier exists.
- Explicitly scope `must_not_auto_respond` intents (security, billing/refund commitments, data
  residency per Daniel) as hard-escalate regardless of confidence.
- Architecture decisions + initial risk register (the 8 pre-seeded R-01..R-08 risks, real
  mitigations/owners).
- Prompt library: specification prompts per FR, build prompts (classification, generation with
  ticket/instruction separation, guardrail checks), traceability table.
- Sprint plan: adopt backlog B-01..B-15 with real hour estimates sized to fit Days 3–4, and a
  cut-order table (what drops first if Day 3/4 overruns).

**Day 3 — Build Spec Days 1–3 compressed into one day.**
| Component | Must work | Check |
|---|---|---|
| Ingest | All 4 channels → 1 normalized shape | Print normalized object per channel |
| Retrieve | Docs embedded (start chunk_size=800/overlap=120, compare against ≥1 alt config), ranked passages with resolvable IDs | Query a known question, confirm right passage |
| Classify + Route | Confidence-scored, threshold applied, decision logged | Run 20 tickets, read the log, every decision has a reason |

**Day 4 — Build Spec Days 4–5 + the gate + PRD revision.**
| Component | Must work | Check |
|---|---|---|
| Generate + Guardrails | Cited answers; ≥1 guardrail that actually blocks | Engineered ticket triggers the guardrail and is blocked |
| Full chain | Unattended run, one documented command, auto metrics report | Start it, walk away, come back to a report |

- Run `python -m evaluation.harness --input <path> --output <path>` unattended over the 80
  validation tickets — per the Dataset Guide this can be freely re-run/tuned against (it is
  *not* the single-use hidden set); report the metrics honestly as a **validation-set** result.
- Metrics report must contain: Volume, Business (FCR/reply-time/escalation), Technical
  (precision+recall per class, retrieval hit rate, latency p50/p95), Governance (decisions
  logged, guardrail activations, PII detections) — computed by code.
- Rehearse a clean-checkout clone-and-run now, not on Day 5.
- PRD revision log: real before/after/trigger table, assumptions-that-failed table,
  deliberately-unchanged table, five-question reflection.

**Day 5 — Governance, monitoring/CI, video, report, effort log, package.**
- Governance Framework: fairness audit across tier/region/fluency (report the non-fluent
  finding honestly — no gap in the human baseline, flagged as an emergent risk to test in the
  built system); all 5 guardrails confirmed as blockers; incident-response steps; kill-switch
  spec; closing declaration.
- Prometheus/Grafana + GitHub Actions CI (`.github/workflows/ci.yml`).
- Video (~20min, live demo: success + escalation + guardrail block + gate-run evidence) —
  budget time for a second take.
- Report in the prescribed 10-section order, 20–30 pages, full prose, every claim sourced,
  AI-tool-use declaration included.
- Effort log finished; estimate-vs-actual table for the 5 largest backlog items.
- Package as `FirstnameLastname_Capstone_Submission.zip` with `01_Video/`, `02_Report/`,
  `03_Workbooks/`, `04_Source_Code/`; run the final 15-item checklist before submitting.

## Acceptance criteria to keep visible throughout (Build Spec §02)

A1 clean-checkout boot · A2 four-channel ingest → one shape · A3 intent+urgency+confidence ·
A4 retrieval returns verifiable real passages · A5 deterministic routing · A6 citations resolve
to actually-retrieved text · A7 a guardrail that blocks, not warns · A8 complete reconciling
decision log · A9 full unattended run, then re-run on an unseen file · A10 auto metrics report
· A11 graceful degradation (no-hit / timeout / outage / rate-limit / malformed input) ·
A12 tests pass via one documented command.

## Notes on scope/cost

Free-tier only (OpenRouter/Groq + local Chroma + SQLite is enough); no acceptance criterion
needs paid capacity. Caching model responses during development is explicitly encouraged.

## Next actions

1. `git init`, `.gitignore`, venv, install deps, verify a live model call — all of Day 1 above.
2. Start Stage 1 discovery: count the flagged figures in `development_tickets.json` and
   resolve the three interview disagreements against real data.
3. Fill the Discovery Workbook and write the problem statement.
