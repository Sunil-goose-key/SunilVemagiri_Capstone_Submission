# Stage Four: Sprint Plan — compressed to 5 working days

## 1. Capacity

| Day | Hours planned | Focus |
|---|---|---|
| 1 | ~8 | Setup + Discovery (done) |
| 2 | ~8 | Requirements, architecture/risk, prompt library, this sprint plan |
| 3 | ~9 | Ingest, retrieve, classify, route |
| 4 | ~9 | Generate, guardrails, harness, the gate, PRD revision |
| 5 | ~9 | Governance/fairness, monitoring/CI, video, report, effort log, package |

On working alone (per the template's own guidance): anything blocking more than an hour gets
written down and worked around rather than absorbed silently — there's no team member who'd
otherwise notice.

## 2. The backlog

| ID | Item | Est. hours | Priority | Depends on | Definition of done |
|---|---|---|---|---|---|
| B-01 | Environment and dependency setup | 1.5 | Must | — | `pip install` succeeds; a real model call returns text |
| B-02 | Data loading and normalisation (`ingest.py`) | 1.5 | Must | B-01 | Normalized object printed for a ticket from each of the 4 channels |
| B-03 | Document chunking and embedding (`retrieve.py` build step) | 1.5 | Must | B-02 | Chroma store built from `documentation.json`; ≥2 chunk configs compared |
| B-04 | Vector store and retrieval query path | 1 | Must | B-03 | Known question returns the correct passage with a resolvable `doc_id` |
| B-05 | Evaluation harness skeleton (`evaluation/harness.py`) | 2 | Must | B-02 | Accepts `--input`/`--output`, loads tickets, writes an (initially empty) metrics report |
| B-06 | Intent and urgency classifier (`classify.py`) | 2.5 | Must | B-02 | 20 dev tickets classified with confidence; alternatives recorded |
| B-07 | Routing logic and thresholds (`route.py`) | 1.5 | Must | B-06 | Same ticket run twice → same decision; `must_not_auto_respond` hard-escalates |
| B-08 | Answer generation with citations (`generate.py`) | 2 | Must | B-04 | Structured output with citations resolving to real retrieved passages |
| B-09 | Guardrails and validation (`guardrails.py`) | 2 | Must | B-08 | Engineered ticket triggers a block, confirmed via log |
| B-10 | Decision logging (`logging_store.py`) | 1.5 | Must | B-07 | Every stage writes a row; coverage reconciles against tickets processed |
| B-11 | **First full unattended run over `validation_tickets.json` — THE GATE** | 2 | Must | B-05, B-09, B-10 | 80 tickets processed unattended, metrics report auto-generated |
| B-12 | Monitoring and dashboards | 1.5 | Should | B-10 | Prometheus metrics exposed; minimal Grafana view |
| B-13 | Continuous integration pipeline | 1 | Must | B-11 | `ci.yml` runs `pytest` on push |
| B-14 | Fairness audit | 1.5 | Must | B-11 | Segmented table filled with real run figures |
| B-15 | Report, video and submission package | ~9 (Day 5) | Must | all | Packaged zip passes the 15-item checklist |

## 3–4. Day-by-day (see `PROJECT_PLAN.md` → "Day-by-day detail" for the authoritative version;
duplicated here only at backlog-ID granularity per the template's own structure)

| Day | Backlog items | Hours |
|---|---|---|
| 3 | B-01 (if not finished Day 1) → B-02 → B-03 → B-04 → B-06 → B-07 | ~9 |
| 4 | B-05 → B-08 → B-09 → B-10 → B-11 (the gate) → PRD revision | ~9 |
| 5 | B-12 → B-13 → B-14 → B-15 | ~9 |

## 5. What you will drop if you run out of time

| Item | Cut order | Consequence of cutting it | What you will say about it in the report |
|---|---|---|---|
| Grafana dashboard (keep Prometheus metrics endpoint only) | 1st to go | Loses a visual dashboard, not the underlying metrics — A-criteria unaffected | "Monitoring was implemented as Prometheus metrics; a Grafana dashboard was scoped out under the compressed timeline in favour of the gate run and governance work, which carry acceptance-criteria weight" |
| Second chunk-configuration comparison (ship with one well-reasoned config) | 2nd to go | Slightly weaker justification for the chunking decision, still defensible from the articles' structure | "Chunk size was set from the documented article structure rather than an empirical A/B comparison, given the compressed timeline; noted as a follow-up in the PRD revision log" |
| CI beyond a single pytest job (coverage reporting, lint gating) | 3rd to go | A12 still satisfied (tests run via one command); just less CI sophistication | "CI runs the test suite on every push; linting and coverage gating were scoped out" |
| Second video take | Last resort only — budget for it, don't plan to skip it | Rougher delivery, but content requirements (live demo, structure) still met in take 1 | N/A if avoided |

**Never cut**: anything touching A1–A12 directly (ingest, retrieval resolvability, routing
determinism, citation resolvability, a working guardrail, decision-log coverage, the
unattended run, the auto-generated metrics report, A11 failure handling, or the single-command
test run) — these are pass/fail with no partial credit, so they're protected ahead of anything
in this cut list.

## 6. Daily check-in (fill as you go)

| Date | Finished since yesterday | Doing today | Blocked by |
|---|---|---|---|
| Day 1 | Env/git setup; discovery workbook + problem statement | PRD, architecture, prompt library, sprint plan | requirements.txt had 3 real pin conflicts, fixed and documented |
