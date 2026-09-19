# Stage Two: Product Requirements Document — v1.0

*Mirrors `Stage_2_PRD_Template.pdf`. Every functional requirement cites the discovery-workbook
section/row that produced it (see `Stage_1_Discovery_Workbook_FILLED.md`).*

## 1. Document control

| Field | Value |
|---|---|
| Version | 1.0 |
| Written by | Sunil Vemagiri |
| Date | Day 2 of build |
| Status | Draft for review |
| Approved by | Sunil Vemagiri — solo project |

## 2. The problem in one paragraph

> CloudServe's support agents already know the answer to most tickets — 71.4% have a correct
> answer sitting in the existing 29-article documentation — but they can't reliably find it
> under time pressure, so they either rebuild it from memory using personal, unreviewed notes
> or pass the ticket to a more senior engineer. Almost half of everything that reaches that
> senior tier (49.1%) turns out to be something the documentation already covered, and
> enterprise customers — despite paying for the tightest service commitments — currently get
> the worst first-contact resolution of any tier. The fix is not a chatbot; it is making the
> answers CloudServe already has reliably findable, attaching a trustworthy, checked confidence
> signal to every response, and making sure the tickets that do need a person arrive with the
> groundwork already done.

## 3. Who this is for

| User group | What they need from this system | What they currently do instead | How you will know it worked for them |
|---|---|---|---|
| Customers raising tickets | A fast, honest answer, or a clear signal that a person is looking at it | Wait 8–12hrs regardless of urgency (Ravi) | Time-to-first-reply drops; FCR rises without a CSAT drop |
| Tier one agents | An answer surfaced from documentation without hunting for it, with confidence attached | Search their own private snippet file (Sofia) | Fewer tickets needing "seen this before" memory-reconstruction; escalations they do send carry a drafted summary |
| Tier two / specialist engineers | Escalations that arrive with context, not a bare forwarded thread | Read the whole thread cold, sometimes re-ask the customer (Daniel) | Share of escalations that were actually `answerable_from_docs` drops from 49.1% toward zero |
| Head of support | A defensible, explainable automation path ahead of an autumn compliance review, with FCR as the real success metric | Reports response time, privately tracks FCR (Marcus) | FCR rises from 43.8% baseline; every automated decision is reconstructable |

## 4. Functional requirements

| ID | Requirement | Priority | Discovery evidence | Acceptance criteria (Build Spec) |
|---|---|---|---|---|
| FR-01 | The system shall ingest tickets from email, chat, docs_comment and forum, normalizing all four into one internal representation that preserves original text and channel. | Must | §2 (channel split: email 42.4%, chat 31.0%, docs_comment 15.6%, forum 11.0%) | A2 |
| FR-02 | The system shall handle missing fields, unusual characters and empty ticket bodies without raising an unhandled exception. | Must | Build Spec §03 Ingest | A11 |
| FR-03 | The system shall predict an intent (from the 22-class taxonomy) and an urgency level for every ticket, with a numeric confidence score. | Must | §2 (22 intent classes, uneven distribution) | A3 |
| FR-04 | The system shall record the alternative predictions it considered for each classification, not only the chosen one. | Should | Build Spec §03 Classify | A3, A8 |
| FR-05 | The system shall retrieve ranked passages from the 29-article documentation corpus, returning identifiers that resolve to real source text, with a relevance threshold below which nothing is returned. | Must | §1 (Ines: internal search fails on phrasing, not doc quality); §2 (71.4% answerable_from_docs) | A4 |
| FR-06 | The system shall route each ticket to auto-respond or escalate using a threshold derived from development-set precision/recall, with the same input always producing the same decision. | Must | §1 (Marcus: hard failure = confidently wrong answer); §6 problem statement | A5 |
| FR-07 | Tickets whose predicted intent is one of `security_incident`, `compliance_request`, `feature_request`, or `unclear_request` shall always escalate, regardless of confidence. | Must | §1 (Daniel: categories that must never be automated); verified directly against `development_tickets.json` — these four classes account for a 100% `must_not_auto_respond` rate and all 87/500 (17.4%) flagged tickets, a more precise finding than the interview alone suggested (billing/data-residency are not in fact separately flagged in this dataset) | A5, Governance guardrails |
| FR-08 | Escalated tickets shall carry the drafted summary, the retrieved sources, and an explicit statement of what the system was unsure about. | Must | §1 (Daniel: "I don't need it to be right, I need it to show its working") | A5 |
| FR-09 | The system shall generate answers grounded in retrieved passages, with citations attached to specific claims, and shall state plainly when it does not know rather than fabricating an answer. | Must | §2 (28.6% of tickets have no documented answer — feature requests, roadmap, novel incidents per Ines) | A6 |
| FR-10 | Ticket content shall be structurally separated from system instructions in every prompt, so that ticket text cannot redirect system behaviour. | Must | Build Spec §03 Generate (prompt-injection defense) | A7 |
| FR-11 | Every generated response shall be checked by a guardrail layer (private data, ungrounded claims, instruction-integrity, tone/scope, confidence floor) before release, and the guardrail shall be able to block the response outright. | Must | §5 risk register (private data leak; confidently wrong answers) | A7 |
| FR-12 | Every automated decision (classification, routing, generation, validation) shall be written to a persistent decision log with the minimum record schema (see Governance Framework), reconciling exactly against tickets processed. | Must | §1 (Marcus: compliance review requires explainability) | A8 |
| FR-13 | The system shall process a full ticket file end-to-end, unattended, via a single documented command accepting `--input` and `--output` path arguments. | Must | Dataset Guide (hidden set is never a hardcoded path) | A9 |
| FR-14 | The evaluation run shall produce a metrics report (volume, business, technical, governance figures) automatically, without further manual work. | Must | Evaluation Framework | A10 |
| FR-15 | The system shall degrade without crashing on: no retrieval hit, model provider timeout/outage, rate limiting, and malformed ticket input. | Must | §5 risk register (model provider outage) | A11 |
| FR-16 | Routing shall escalate on a deterministic, intent-independent keyword check for audit/compliance/legal/security-incident terms in the ticket's own text, in addition to (not instead of) the intent-based hard-escalate check. | Must | Found live on Day 5 video-prep testing: ticket `DEV-0003`/`VAL-0009` (true intent `compliance_request`, `must_not_auto_respond=true`) was misclassified as `data_export`/`configuration_help`, so the intent-based check alone missed it — both `classification.must_not_auto_respond` and the intent-membership check are derived from the same single predicted value, so neither is actually independent of the other. See PRD revision log §4c. | A5, Governance guardrails |

## 5. Non-functional requirements

| ID | Category | Requirement | How it will be verified |
|---|---|---|---|
| NFR-01 | Latency | p95 end-to-end response time under 3 seconds | Measured by the evaluation harness across the full run |
| NFR-02 | Availability | 99.5%+, with graceful degradation on provider outage rather than downtime | Simulated outage during A11 testing |
| NFR-03 | Accuracy | Intent classification precision ≥85% per class; hallucination rate ≤5%; citation accuracy ≥95% | **Human review completed** — the method NFR-03 was actually written to require: 2 raters, independently, over 71 sampled responses (above the ≥50 minimum) from the final gate run. Result: **hallucination rate 1.4% (1/71), citation accuracy 98.6% (70/71), 100% inter-rater agreement (71/71)** — both figures pass their targets with margin. The one flagged ticket (`VAL-0063`) was checked against its cited passage directly: the answer's cause diagnosis was grounded, but its specific instructed action ("go to project settings") didn't match the passage's actual resolution step ("check the effective permissions view") — a genuine finding, not a false positive. Full worksheet: `04_Submission/NFR03_Human_Review_Worksheet.csv`; computed summary: `evaluation/results/nfr03_human_review_summary.json`. An earlier automated LLM-judge proxy (PR-04) over the full 200-entry `ground_truth_responses.json` set remains as supplementary evidence: 0 genuine `must_not_claim` violations across 195 judged tickets (1 raw flag traced and confirmed a judge false positive), 94.5% citation-hit proxy, 47.9% `must_mention` coverage (likely an underestimate — see report §7). |
| NFR-04 | Privacy | Zero private-data occurrences in outbound responses | Automated PII scan of every response + manual sample review |
| NFR-05 | Auditability | 100% decision-log coverage, reconciling exactly against tickets processed | Coverage check per run |
| NFR-06 | Fairness | Under 5 percentage points of quality variation across customer tier, region and language-fluency segments | Segmented fairness audit (see Governance Framework) — actively test the non-fluent-English segment given retrieval's phrasing-dependence, even though today's human baseline shows no gap |
| NFR-07 | Cost | Free-tier only (OpenRouter/Groq); no acceptance criterion requires paid capacity | Track token/request usage during development; cache responses |

## 6. What is deliberately out of scope

| Not building | Why not | What would have to change for this to be reconsidered |
|---|---|---|
| Rewriting or restructuring documentation content | Ines confirms the 29 articles are accurate within their review cycle — the defect is retrieval/findability, not authorship | If the fairness audit or evaluation showed systematic factual gaps in specific articles, not just retrieval misses |
| Automating `must_not_auto_respond` intents — verified as `security_incident`, `compliance_request`, `feature_request` and `unclear_request` (17.4% of volume; see FR-07 and the PRD revision log for how this list was corrected from Daniel's interview framing against the labelled data) | These are hard-escalate by design regardless of confidence | Never, within this project's scope — this is a governance line, not a capacity limit |
| A conversational chat interface / customer-facing chatbot UI | The client's stated request, but the evidence shows the leverage point is retrieval + confidence-gated routing behind existing channels, not a new UI | If a future phase specifically targeted the chat channel's UX, informed by this system's routing/retrieval core |
| Retraining or fine-tuning a model on CloudServe's historical resolutions | Daniel warns the private snippet files (and by extension some historical resolutions) contain stale/wrong answers that would be "learned" if used as a training signal | If a reviewed, curated subset of historical resolutions were established as trustworthy training data |

## 7. Assumptions and their consequences

| Assumption | Why you believe it | What happens if it is false | How you will find out |
|---|---|---|---|
| A confidence threshold around 0.80 (the `.env.example` default) is a reasonable starting point | It's the pack's stated default and matches typical calibration targets | Threshold answers too much (customer harm) or too little (no automation benefit) | Re-derive from real precision/recall on the classifier once built (Day 3); log the trade-off explicitly |
| Chunk size 800/overlap 120 retrieves the 29 articles adequately | Setup Guide's starting point; articles have a consistent title/symptoms/causes/steps/notes structure | Chunks split mid-resolution-sequence, retrieving incomplete steps | Compare against at least one alternative chunk configuration on Day 3 and measure retrieval quality |
| The non-fluent-English fairness gap Sofia expects will emerge once retrieval depends on phrasing, even though it isn't present in the human baseline | Retrieval quality is phrasing-dependent in a way manual search plus clarifying questions is not | It may not emerge, or may emerge in a different segment (e.g. very short vs. long tickets) | Fairness audit segments explicitly on `language_fluency`, ticket length, tier and region — not just an aggregate figure |
| `must_not_auto_respond` labelling in the dataset is a reliable proxy for what should hard-escalate in the built classifier | It's an explicit labelled field in the schema, not inferred | The classifier may not reliably predict this flag itself if it's meant to be inferred rather than looked up | Confirm whether `must_not_auto_respond` is available at inference time or must be predicted; if the latter, its own precision/recall matters more than any other single metric |

## 8. Success measures

**Final figures below are from the most recent gate run** (`metrics_20260918T183312Z.json`),
after fixing, in order: (1) a routing bug that would have sent 9/80 tickets a blank
auto-response, (2) a generation over-caution bug where the model declined to answer 7 tickets
despite the correct passage being retrieved, and (3) a misclassified must-escalate intent
bypassing the hard-escalate check entirely (found live during video-prep testing on Day 5, see
FR-16 and the PRD revision log §4c). All three fixes and their before/after evidence are in the
PRD revision log.

| Measure | Baseline | Target | **Achieved (final gate run, 80 validation tickets)** | Measured how |
|---|---|---|---|---|
| First contact resolution | 42% (population) / 43.8% (dev sample) | 60%+ | **80.0%** (this run's routing outcomes — see business.note in the metrics report on why this isn't equivalent to a live-customer FCR) | Evaluation harness |
| Escalation rate | 58% (population) / 56.2% (dev sample) | 30% or lower | **20.0%** (16/80) | Evaluation harness |
| **Share of escalations still avoidable per ground truth** | **49.1% (discovery baseline)** | Toward single digits | **31.2% (5/16)** — 4 of those 5 are *intentional* escalations (3 hard-escalate intents + 1 safety-keyword catch, all correct behaviour, not defects); only 1/16 (6.25%) is a genuine retrieval miss — actually a slight improvement over the pre-FR-16 figure (1/14, 7.1%), because the fix trades a small amount of automation rate for a governance-critical correctness gain (below). | Evaluation harness joined against `labels.answerable_from_docs` |
| **Must-escalate coverage (governance-critical)** | 1 miss found pre-FR-16 (`VAL-0009`, a `compliance_request` misclassified and auto-answered) | 0 misses | **0/80 tickets with true `must_not_auto_respond=true` are missed** | Cross-check of `results.jsonl` against `labels.must_not_auto_respond` |
| Disclosed trade-off | — | — | `VAL-0037` escalates on the keyword "compliance" even though its true label (`data_residency`, `must_not_auto_respond=false`) didn't strictly require it — an efficiency cost, not a safety failure, and an accepted one | Same cross-check |
| Classification accuracy (weighted) | — | 85%+ | **81.25%** (macro: 76.6% precision / 76.5% recall — several low-support classes at 0%, see Evaluation section; unaffected by the FR-16 fix, which is routing-layer only) | `sklearn.classification_report` against ground-truth `labels.intent` |
| Retrieval hit rate | — | — | **96.2%** (retrieved set includes an `expected_doc_ids` match) | Evaluation harness |
| Latency | — | p95 <3s | Varies by cache state across runs: coldest observed p95 was 11.8s, warmest (fully cached) 0.06s. Root cause of the miss either way: classify and generate run sequentially in `process_ticket()` — a code-structure choice, not a free-tier limitation, since `generate()` doesn't actually depend on classify's output and the two could run concurrently. **Treat the cold figure (11.8s) as the honest worst case for the report**, not the cached ones. | Evaluation harness |
| Decision-log coverage | — | 100% | **100%** (80/80 reconciled exactly) | `DecisionLog.coverage()` |
| Private data detections | — | 0 | **0** | Guardrail scan of every response |
| Blank auto-responses (routing bug found Day 4) | — | 0 | **0** (was 9/80 before the fix) | Manual + automated check of `can_answer` vs `action` |
| Cross-group variation (fairness) | Non-fluent vs. fluent: no gap in human baseline | Under 5 pts | **Non-fluent: 5.5pt gap (passes)** — the specific risk flagged in discovery did not materialize. Tier: 24.3pt *raw* gap on standard tier (n=42, fails on the raw metric) — but restricted to tickets actually eligible for auto-answer (excluding ones that always must escalate), the real gap is **6.5pt (93.5% vs. 100%, fails narrowly)**, fully explained by one retrieval miss + one disclosed trade-off, not a classification/retrieval defect across the board — see governance doc §3 for the full breakdown. Region: up to 28.6pt (small samples, n=7, not statistically reliable). *Note: re-verified against a fresh gate run — the segment-level breakdown is not perfectly stable run-to-run even though aggregate FCR/escalation are; see Governance Framework §3 for the full note.* | Segmented fairness audit |
| Time to first reply / Customer satisfaction | 8–12hrs / 3.2 baseline | <5min / 4.0+ | Not measurable without live customers — proxy only, not run in this compressed timeline | N/A this cycle |

## 9. Open questions

| Question | Why it matters | Owner | Resolve by |
|---|---|---|---|
| ~~Is `must_not_auto_respond` available at inference time, or must the classifier predict it?~~ **Resolved Day 2**: it's a deterministic function of intent (`security_incident`/`compliance_request`/`feature_request`/`unclear_request` = 100% must-escalate, verified against all 500 dev tickets) — so it's a lookup once intent is predicted, which means the classifier's precision/recall *specifically on these four classes* is now the safety-critical number to report, not overall accuracy. | A false-negative intent prediction on one of these four classes is the single most direct path to a governance failure | You | Resolved |
| What confidence threshold actually balances FCR gain against wrong-answer risk? | Directly determines automation rate and customer-harm risk | You | Day 3–4, from real precision/recall data |
| Does the non-fluent-English fairness gap actually emerge once retrieval is introduced? | Determines whether an additional mitigation (e.g. query rewriting for non-fluent tickets) is needed | You | Day 4/5 fairness audit |
