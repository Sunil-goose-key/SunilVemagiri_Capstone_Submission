# Effort Log

## 1. Your details

| Field | Value |
|---|---|
| Full name | Sunil Vemagiri |
| Project start date | 1 September |
| Target submission date | 20 September |
| Hours available per week | Compressed to a 5-working-day schedule per project constraint |

## 2. Summary of hours by stage

| Stage | Planned hours (5-day plan) | Actual hours | Difference | Why the difference |
|---|---|---|---|---|
| 1. Discovery | ~8 | 2 | -6 | Data-driven discovery (cross-tabs against real ticket data) was faster than a manual/interview-only pass would have been, since the analysis itself surfaced the answers directly |
| 2. Requirements | ~4 (part of Day 2's 8) | 2 | -2 | Bundled with prompt library and sprint plan into one 6 September session — PRD writing was fast once discovery was solid |
| 3. Prompt library | ~2 | 0 | -2 | Produced in the same 6 September session as Requirements — not separately tracked, no additional hours beyond that session |
| 4. Sprint plan | ~2 | 0 | -2 | Same session as above — backlog structure was largely predetermined by the Build Spec's own component list, so it added no real extra time |
| 5. Build and revision | ~18 (Days 3-4) | 22 | +4 | Includes environment setup, both build sessions, the two Day-4 bug-fix/revision sessions, the NFR-03 evaluation gap closure, the FR-16 governance fix, and the retrieve.py telemetry fix (evaluation/governance work folds into this row — the template has no separate line for it). Three real defects were found and fixed here, each needing root-causing time the original estimate didn't budget for |
| 6. Report, video, packaging | ~9 | 11 | +2 | Video recording, report expansion to full length, the NFR-03 human-review worksheet and archive assembly, and final review — slightly over plan, mostly from re-recording the video and the report's substantial expansion |
| **Total** | ~43 | **37** | -6 | Discovery and the requirements/prompts/sprint-plan cluster came in well under plan; build, evaluation and packaging ran slightly over — net six hours under the original estimate |

*Note on this log's honesty*: the enrolment window runs 1–20 September, but hands-on work did
not start until 6 September — that five-day gap is real and is not backfilled with invented
activity. Within the working period, several days were executed as continuous, tool-assisted
sessions rather than strictly separated calendar days; "hours" are approximate effort, not
precise wall-clock time, and are marked `[fill in]` wherever this log genuinely needs your own
number rather than an invented one. The point of this log is an honest account, not a
plausible-looking one.

## 3. Week one: daily entries (1–7 September)

No activity 1–5 September (enrolment window open, work not yet started). Hands-on work began
6 September.

| Date | Task | Stage | Hours | What it produced | Blocked by anything? |
|---|---|---|---|---|---|
| 6 Sept | Repo/env setup; fixed 2 dependency pin conflicts found immediately (openai, pydantic) | Setup | 2 | Working venv, verified model access pending key | No API key yet — proceeded with local-only work (embeddings, ingest) until provided |
| 6 Sept | Discovery: computed real stats from `development_tickets.json`, resolved 3 flagged interview disagreements against data, wrote problem statement | Discovery | 2| `Stage_1_Discovery_Workbook_FILLED.md` | None |
| 6 Sept | PRD v1, architecture doc, governance risk register draft, prompt library (3 prompts + register), sprint plan | Requirements/Prompts/Sprint plan |2| `Stage_2_PRD_v1.md`, `docs/architecture.md`, `Governance_Framework_DRAFT.md`, `prompts/`, `Stage_4_Sprint_Plan_v1.md` | Found 3 more dependency conflicts (langchain family, sentence-transformers, chromadb) — all fixed same session |
| 6–7 Sept | Built `src/` end to end (ingest, models, config, logging, llm_client, retrieve, classify, route, generate, guardrails, pipeline, api, metrics), `evaluation/harness.py`, tests, CI | Build |2| Working pipeline, 21 tests passing before live-key testing | None |
| 7 Sept | Got real API key, verified live access, ran 20-ticket classify+route checkpoint | Build | 3| Confirmed pipeline works live; README finalized | Found and fixed: wrong must-escalate intent list (interview-based guess vs. verified data), retrieval threshold miscalibration, a real A5 determinism bug (non-deterministic classification), a classifier confusion (feature_request vs. billing_query) |

## 4. Week two: daily entries (8–14 September)

No activity 8–10, 12, or 14 September — work this week was two short, separated sessions (11th
and 13th), not continuous.

| Date | Task | Stage | Hours | What it produced | Blocked by anything? |
|---|---|---|---|---|---|
| 11 Sept | Live-tested generation+guardrails, ran the full 80-ticket gate twice as real bugs were found and fixed | Build/Evaluation |2| Metrics reports, fairness audit | Found and fixed: a routing bug sending blank auto-responses (9/80 tickets), a generation over-caution bug (7 tickets declining despite correct retrieval) |
| 11 Sept | Wrote PRD revision log with real before/after entries for every fix above | Revision | 2| `Stage_5_PRD_Revision_Log_v1.md` | None |
| 13 Sept | Found `ground_truth_responses.json` (200 expert reference answers) was provided but never wired into any evaluation; built `evaluation/ground_truth_check.py` and a new judge prompt (PR-04) to close the gap | Evaluation | 4| `evaluation/results/ground_truth_check_20260913T162426Z.json` | A 3-ticket sanity check first caught a real judge-prompt bug (echoing the full forbidden-claims list regardless of its own reasoning); rewrote the prompt before running the full 200-ticket set |

## 5. Week three: daily entries (15–20 September)

| Date | Task | Stage | Hours | What it produced | Blocked by anything? |
|---|---|---|---|---|---|
| 15 Sept | Live-tested the system while rehearsing the demonstration video; found a governance-critical defect — a misclassified compliance ticket bypassing the hard-escalate check entirely — not caught by any of the four prior gate runs | Build/Governance |1| FR-16: an independent, intent-agnostic safety-keyword check in `src/route.py`; re-ran the full gate, confirmed 0 missed must-escalate tickets (was 1) | Found live by watching real output, not by any automated test |
| 15 Sept | Recorded the demonstration video | Video |3| `SunilVemagiri_Capstone_Video.mp4` (19:06) | — |
| 16–17 Sept | Updated the governance framework and PRD revision log with the FR-16 finding; investigated and fixed a chromadb/posthog telemetry logging issue in `src/retrieve.py` (cosmetic, unrelated to retrieval correctness — verified before and after) | Governance/Build | 4| `Governance_Framework_DRAFT.md` risk R-09; corrected `src/retrieve.py` | First attempted fix broke retrieval silently (an untested `client_settings` change downgraded the vector store to in-memory) — caught by re-testing before accepting the fix, reverted to a safer logging-level fix |
| 17 Sept | Re-verified the fairness audit after finding the standard-tier "gap" was being reported without controlling for tickets that always must escalate; recomputed on a like-for-like basis | Evaluation/Governance | 2| Corrected fairness figures across the report, PRD and governance doc: raw 69.0% vs. 93.3%, but 93.5% vs. 100% once restricted to eligible tickets | Also caught and fixed a stale metrics-file citation from an earlier, overwritten harness run |
| 18 Sept | Expanded the report from ~7 to the required 20–30 pages in full prose, with numbered tables/figures; built PDF conversion tooling for the report and all workbooks; created the Stage Three Prompt Library workbook (previously only a blank template existed) | Report/Packaging | 3| `Report_Draft.md` (20-page PDF), `Stage_3_Prompt_Library_v1.md`, five workbook PDFs | Caught two fabricated test-file names while writing the traceability table — corrected to cite real coverage |
| 19 Sept | Assembled and verified the final submission archive (video, report, workbooks, source code); built the NFR-03 human-review worksheet from real gate-run output; two independent raters completed the review | Packaging/Evaluation |4| `SunilVemagiri_Capstone_Submission.zip`; `NFR03_Human_Review_Worksheet.csv`; hallucination rate 1.4%, citation accuracy 98.6%, 100% inter-rater agreement (71 responses) | Declined to fill in one rater's columns myself when asked, since that would have made the "two-rater" review one AI pass and one human pass — found a second real rater instead |
| 19 Sept | Reviewed all four submission parts (video, report, workbooks and effort log, source code) against the Submission Guide's own requirements for each, and checked the generated output for each part against that checklist | Review/Submission |1| Confirmed all four parts meet the guide's stated requirements | — |

## 6. Estimates against reality (5 largest items)

| Item | Estimated hours | Actual | Why the difference |
|---|---|---|---|
| B-11: first full unattended gate run | 2 | ~4 (across 3 runs) | Found two real, non-trivial bugs that needed root-causing and fixing between runs — exactly the scenario the Build Spec warns "always exposes problems that never appear one ticket at a time" |
| Environment setup (B-01) | 1.5 | ~2 | 5 separate dependency-pin conflicts in the pack's own `requirements.txt`, each needing individual diagnosis |
| Discovery (Stage 1) | 8 (original 3-week plan) | ~3 | Data-driven cross-tabs resolved the flagged disagreements faster than expected |
| Classification (B-06) | 2.5 | ~3.5 | Needed a second pass after finding the determinism bug and the feature_request/billing_query confusion |
| Generation (B-08) | 2 | ~3 | Needed a second pass after finding the over-caution bug via the gate run |

## 7. Where the time went unexpectedly

| Question | Your answer |
|---|---|
| Which task took far longer than you expected, and why? | Getting a working Python environment. Five separate, genuine version-pin conflicts in the pack's own `requirements.txt` (not anything self-inflicted) had to be diagnosed and fixed one at a time, since fixing one often revealed the next. |
| Which task was easier than you expected, and why? | Discovery. Once the ticket data was loaded, most of the "verify the interview claims" work was a few lines of aggregation — the hard part was knowing which claims to check, not computing the answers. |
| What would you allocate differently if you started again on Monday? | Run the full gate on day one of the build phase with a trivial pass-through pipeline (everything auto-escalates), just to prove the harness itself works end to end, before investing in the classify/generate logic. Would have caught the routing/generation defects even earlier. |
| What did you spend time on that turned out not to matter? | Comparing a second chunk-size configuration for retrieval — the 96.2% hit rate achieved with the first, structurally-reasoned configuration made a second comparison low-value relative to the time it would have cost, so it was deliberately scoped out (see sprint plan cut-order). |

## 8. Declaration

Sign to confirm that this record is an accurate account of your own work on this project.

| Full name | Signature | Date | Total hours recorded |
|---|---|---|---|
| Sunil Vemagiri |Sunil Vemagiri|19 Sep| 37hrs|
