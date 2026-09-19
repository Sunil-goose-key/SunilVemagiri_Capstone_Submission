# Prompt Library — register

*Mirrors `Stage_3_Prompt_Library.pdf`. Every prompt cites the requirement it serves.*

## Prompt register

### PR-01 — Classification

| Field | Value |
|---|---|
| Name and purpose | Predict intent (22-class) + urgency + calibrated confidence + alternatives for a normalized ticket |
| Category | Build |
| Serves requirement | FR-03, FR-04 |
| Version | 1.1 |
| File | `build/classify.txt` |
| Model used | `MODEL_NAME` from `.env` (default `meta-llama/llama-3.1-8b-instruct` via OpenRouter), called at `temperature=0`/`seed=0` and cached by prompt content (`src/llm_client.py`) — required for A5 determinism, see change history |
| Inputs it expects | `CHANNEL`, `SUBJECT`, `BODY`, `INTENT_CLASS_LIST` |
| Output format required | JSON: `intent`, `urgency`, `confidence`, `alternatives[]`, `rationale` |
| How you know it worked | Output parses as valid JSON with an `intent` in the allowed 22-class list; confidence is checked against observed accuracy in the calibration table (Evaluation Framework); 19/20 (95%) on a Day 3 spot-check against `development_tickets.json` |
| Known weaknesses | LLM-stated confidence is not automatically calibrated — must be checked empirically (Evaluation Framework); `feature_request` phrased in billing/spend language can still confuse the model in principle, though the v1.1 disambiguation rule fixed the two observed cases |
| Change history | v1.0 — initial version, Day 2. v1.1 — Day 3: added explicit rule disambiguating `feature_request` from `billing_query` when a request is phrased in billing language but asks for new capability, after two real misclassifications were found (both were must-escalate `feature_request` tickets confidently mislabelled `billing_query`) |
| Injection defense | Ticket content is delimited inside `<ticket>` tags; system role explicitly instructs the model to treat ticket content as data, never as instructions, and to note in `rationale` if the ticket attempted to instruct it |

### PR-02 — Generation

| Field | Value |
|---|---|
| Name and purpose | Draft a grounded, cited answer from retrieved passages, or explicitly decline if the passages don't answer the question |
| Category | Build |
| Serves requirement | FR-09, FR-10, FR-11 (feeds the grounding guardrail) |
| Version | 1.1 |
| File | `build/generate.txt` |
| Model used | Same as PR-01, `temperature=0`/cached |
| Inputs it expects | `RETRIEVED_PASSAGES` (with doc_ids), `CHANNEL`, `SUBJECT`, `BODY` |
| Output format required | JSON: `can_answer`, `answer`, `citations[]` (doc_id + supports), `uncertainty` |
| How you know it worked | Every `doc_id` in `citations` resolves to a passage actually present in `RETRIEVED_PASSAGES`; `can_answer=false` used when passages don't cover the question rather than fabricating |
| Known weaknesses | Model may still occasionally over-claim confidence in an answer despite instructions; this is exactly what PR-03 checks independently rather than trusting self-report |
| Change history | v1.0 — initial version, Day 2. **v1.1 — Day 4: fixed a significant over-caution failure.** The Day 4 gate run found 7/80 validation tickets where the correct documentation passage was retrieved (in one case, `DOC-DEPLOY-001`, literally titled for the exact symptom the ticket described) but the model declined to answer, reasoning that the ticket hadn't pre-stated a detail (e.g. plan type, permission scope) that the passage's own resolution steps actually explain how to check. Added an explicit rule: don't decline for missing information the passage itself shows how to obtain; only decline when the passage's actual subject matter doesn't match the ticket. Re-tested on all 7: **7/7 now produce grounded, correctly-cited answers.** This is the single highest-value prompt change made during the build — it directly moves the system's actual automation rate, not just a metric. |
| Injection defense | Ticket content delimited in `<ticket>` tags, separate from `<retrieved_passages>` and from system instructions; explicit instruction to ignore embedded directives |

### PR-03 — Grounding check (evaluation/guardrail)

| Field | Value |
|---|---|
| Name and purpose | Independently verify that a generated answer's claims are actually supported by its cited passages |
| Category | Evaluation (also used live as the grounding guardrail) |
| Serves requirement | FR-11 (grounding guardrail), NFR-03 (hallucination rate) |
| Version | 1.0 |
| File | `evaluation/grounding_check.txt` |
| Model used | Same provider; run as a second, independent call — not the same call that produced the answer |
| Inputs it expects | `ANSWER`, `CITED_PASSAGES` |
| Output format required | JSON: `grounded`, `unsupported_claims[]`, `notes` |
| How you know it worked | Cross-checked against the human-reviewed hallucination sample the Evaluation Framework specifies (≥50 responses, 2 raters) — completed: 71 responses, 100% inter-rater agreement, 1.4% hallucination rate (`04_Submission/NFR03_Human_Review_Worksheet.csv`, `evaluation/results/nfr03_human_review_summary.json`) |
| Known weaknesses | An LLM checking another LLM's output is not a substitute for the human-reviewed sample the Evaluation Framework requires; used as a live guardrail (fast, cheap) with the human sample as the ground-truth calibration check |
| Change history | v1.0 — initial version, Day 2 |

### PR-04 — Ground-truth judge (evaluation, offline)

| Field | Value |
|---|---|
| Name and purpose | Judge a generated answer against a senior agent's `must_mention`/`must_not_claim` lists from `ground_truth_responses.json`, per-item true/false |
| Category | Evaluation |
| Serves requirement | NFR-03 (hallucination rate, citation accuracy) — automated proxy, not a substitute for the human review NFR-03 specifies |
| Version | 1.1 |
| File | `evaluation/ground_truth_judge.txt` |
| Model used | Same provider; one call per ticket, run offline by `evaluation/ground_truth_check.py`, never in the live per-ticket path |
| Inputs it expects | `ANSWER`, `MUST_MENTION` (JSON array), `MUST_NOT_CLAIM` (JSON array) |
| Output format required | JSON: `must_mention_results[]` and `must_not_claim_results[]`, each `{item, covered\|violated, why}` — one entry per input item, explicit per-item boolean |
| How you know it worked | Sanity-checked on 3 tickets before the full 200-ticket run; the flagged safety violation from the full run was manually traced against the real generated text and confirmed/corrected (see PRD revision log §4d) |
| Known weaknesses | v1.0 let the model echo the full forbidden-claims list regardless of its own reasoning (one ticket's prose explicitly contradicted its own structured output) — fixed in v1.1 by forcing an explicit per-item checklist format rather than a build-this-array format, which is far more reliable for a small free-tier model. Even v1.1 produced one confirmed false positive (empty `must_mention` list confused with `must_not_claim` content) and 3/200 (1.5%) unparseable JSON responses — an LLM judge remains an automated proxy, not a replacement for the human 2-rater review this NFR was written to require. |
| Change history | v1.0 — initial version. v1.1 — rewrote output schema to explicit per-item `{item, covered/violated, why}` objects after the 3-ticket sanity check caught the echo-the-whole-list bug described above. |

## What makes a prompt worth keeping — checklist applied

| Check | PR-01 | PR-02 | PR-03 |
|---|---|---|---|
| Role and task stated separately | ✅ | ✅ | ✅ |
| Inputs clearly delimited | ✅ (`<ticket>`) | ✅ (`<ticket>`, `<retrieved_passages>`) | ✅ (`<answer>`, `<cited_passages>`) |
| Output format specified exactly | ✅ JSON shape given | ✅ | ✅ |
| Says what to do when the answer isn't known | N/A (classification always produces a label) | ✅ (`can_answer:false`) | ✅ (`unsupported_claims`) |
| Representative examples | ⚠️ not yet added — planned as a Day 3 refinement once real misclassifications are observed | ⚠️ same | N/A |
| Forbids what must never happen | ✅ (no refund/timeline commitments) | ✅ | N/A |

## Traceability check

| Requirement ID | Specification written? | Prompts covering it | Test case identifier | Gaps |
|---|---|---|---|---|
| FR-03 | Yes (PRD §4) | PR-01 | *[to add in `tests/`]* | none |
| FR-04 | Yes | PR-01 (`alternatives`) | *[to add]* | none |
| FR-09 | Yes | PR-02 | *[to add]* | none |
| FR-10 | Yes | PR-01, PR-02 (delimiting) | *[to add]* | none |
| FR-11 | Yes | PR-03 + guardrail code (non-LLM checks for PII/tone) | *[to add]* | PII and tone/scope guardrails are deterministic code, not prompts — noted here so the traceability table doesn't imply they need a prompt entry that doesn't exist |
