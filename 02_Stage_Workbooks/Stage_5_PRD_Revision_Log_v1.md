# Stage Five: Revision Log — v2.0

## 1. Revision summary

| Field | Value |
|---|---|
| New version number | 2.0 |
| Date of revision | Day 3–4 of the compressed build |
| Who carried out the revision | You (solo) |
| Who reviewed and agreed it | You (solo project) |
| Number of requirements changed | 1 (FR-07) |
| Number of requirements added | 0 (existing NFRs/FRs covered the new findings; thresholds tuned within existing requirements) |
| Number of requirements removed | 0 |

## 2. The changes

| Requirement ID | What it said in v1 | What it says now | What prompted the change | Agreed by |
|---|---|---|---|---|
| FR-07 | "Tickets whose intent is flagged `must_not_auto_respond` (security, billing/refund commitments, data residency) shall always escalate" — based on Daniel's interview | "Tickets whose predicted intent is one of `security_incident`, `compliance_request`, `feature_request`, or `unclear_request` shall always escalate" | Checked the interview-derived guess against the labelled `must_not_auto_respond` field in `development_tickets.json` directly: these four classes account for a 100% must-escalate rate and all 87/500 (17.4%) flagged tickets. Billing and data-residency, which the interview specifically named, are *not* separately flagged in this dataset. | You |
| (config, not a numbered FR) `CONFIDENCE_THRESHOLD` / `RETRIEVAL_RELEVANCE_FLOOR` defaults | Threshold 0.80 (unexamined default); relevance floor 0.35 (unexamined guess) | Relevance floor recalibrated to 0.05 based on real score distributions (irrelevant queries score -0.35 to -0.40; relevant ones score +0.09 to +0.61 with this embedding/chromadb combination) | The 0.35 default was empirically filtering out correct retrieval results — a real query's correct passage scored only 0.23. | You |

## 3. Assumptions that turned out to be wrong

| Assumption from v1 | Did it hold? | What you found instead | What you changed because of it |
|---|---|---|---|
| The interview's named categories (billing/refund, data residency) are the right proxy for `must_not_auto_respond` | **No** | The dataset's actual labelling ties the flag deterministically to 4 different intent classes, including one not mentioned in any interview (`unclear_request` — i.e. if the classifier itself can't confidently name the intent, that alone is grounds to hard-escalate) | Rewrote FR-07 against the verified data rather than the interview alone; treated the interview as a hypothesis to check, not a specification |
| A single LLM call at default settings is adequate for a routing-critical classification step | **No** | Default-temperature sampling produced different predictions run-to-run on an identical 20-ticket re-test — which would fail A5's literal "run the same ticket twice" test if triggered during grading, since routing depends on classification output | Added `temperature=0`/`seed=0` and a disk-backed response cache keyed on exact prompt content to `src/llm_client.py`; verified two full runs now produce byte-identical output |
| A default relevance floor "in the middle of the range" (0.35, out of an assumed 0-1 scale) is a safe starting point | **No** | This embedding/chromadb combination's relevance scores aren't a 0-1 cosine scale — real relevant matches scored as low as 0.09 and irrelevant ones scored strongly negative. 0.35 silently discarded correct retrieval results. | Recalibrated empirically against probe queries before building anything downstream of retrieval, rather than tuning against the harness after the fact |
| Documentation phrasing mismatches (Ines's finding) are the main source of classifier/retrieval error | **Partially** | Confirmed for retrieval (fixed by semantic embeddings). For classification specifically, found a *different* failure mode: surface-level topic overlap between `feature_request` and `billing_query` when a feature request is phrased using billing/spend vocabulary | Added an explicit disambiguation rule to the classification prompt (PR-01 v1.1) rather than assuming semantic retrieval alone would generalize to classification |

## 4. What you decided not to change

| What looked wrong | Why you left it | What it would have cost to change | Revisit when? |
|---|---|---|---|
| Chunk size 800/overlap 120 (single configuration, not A/B compared against a second config) | The 29 articles' consistent title/symptoms/causes/steps/notes structure made 800/120 a defensible choice on structural grounds alone, and the compressed 5-day timeline prioritized the gate run and governance work over a second empirical comparison | ~1-2 hours to build and compare a second index, time better spent on Day 4/5 acceptance-criteria work per the sprint plan's own cut-order | If retrieval hit-rate from the full gate run looks weak, before submission |
| Confidence threshold left at 0.80 rather than re-derived from a full precision/recall sweep | A 20-ticket spot check (95% accuracy after the classification fix) didn't reveal enough signal to justify moving it, and the full validation-set run's classification report is the actual evidence to threshold against | A proper threshold sweep needs the full run's per-class precision/recall, not a 20-ticket sample | After the Day 4 gate run's classification report is in — see the metrics report for the final figure used |

## 4b. Two build-time defects found by the gate run itself (Day 4)

Not PRD changes, but exactly the kind of finding this log exists to capture — both were found
by *running the full set*, not by inspecting code, which is the whole point of A9.

| What was found | How it was found | Fix | Verified |
|---|---|---|---|
| **Blank auto-responses**: 9/80 (11.25%) tickets routed to `auto_respond` with an empty answer, because routing checked only whether retrieval returned *any* passage, never whether generation actually produced a grounded answer | Full 80-ticket gate run — invisible at the single-ticket scale tested through Day 3 | `route.decide()` now escalates whenever `generation.can_answer` is false, regardless of confidence or retrieval non-emptiness | Re-ran the full gate: 0/80 blank responses; regression test added |
| **Generation over-caution**: 7 tickets declined to answer despite the *correct* documentation passage being retrieved (in one case, the passage's title was an exact match for the ticket's symptom), because the model treated a missing precondition the passage itself explains how to check as grounds to decline | Manual inspection of the "escalated but answerable_from_docs=true" subset after the routing fix — the count didn't drop as much as the routing fix alone should have produced | Added an explicit prompt rule: don't decline for information the passage's own resolution steps explain how to obtain; only decline when the passage's subject matter doesn't match | Re-tested the affected 7 tickets: 7/7 now answer correctly with valid citations; full re-run confirmed system-wide effect (avoidable-escalation share dropped from 49.1%→28.6%, real miss rate 7.1%) |

## 4c. A third build-time defect, found live during video-prep testing (Day 5)

| What was found | How it was found | Fix | Verified |
|---|---|---|---|
| **A misclassified must-escalate intent bypassed the hard-escalate check entirely.** `classification.must_not_auto_respond` and the `intent in MUST_ESCALATE_INTENTS` check are both derived from the *same single* classified `intent` value — neither is an independent signal. Ticket `VAL-0009`/`DEV-0003` ("Retention period question" / an auditor asking about access-record retention, true intent `compliance_request`, `must_not_auto_respond=true`) was classified as `configuration_help`/`data_export` at 0.90-0.95 confidence, so the hard-escalate lookup never fired and the ticket was auto-answered when it should have escalated. | Found while running the pipeline live on real tickets to prepare for the video — not by inspecting code or reading the metrics report, by watching an actual ticket go the wrong way | Added an independent, intent-agnostic safety check: a deterministic keyword scan (`route._mentions_safety_sensitive_topic`) over the ticket's own text for audit/compliance/legal/security-incident terms, escalating regardless of what intent was predicted. This is deliberately *not* another classifier call — it reads the raw ticket text directly, so it doesn't share the same failure mode as the thing it's meant to catch. | Re-ran the full gate: **0 tickets with true `must_not_auto_respond=true` are now missed** (was 1 missed before this fix). Two tickets in the 80-ticket set are caught by the new check; one (`VAL-0037`) is a disclosed false-positive-for-efficiency — its true label didn't strictly require escalation, but the keyword ("compliance") fired anyway. This is an accepted, stated trade-off: erring toward an unnecessary escalation is a cost in automation rate, not a safety failure, and is preferable to the alternative found in the same ticket class. |

This is also a direct, concrete illustration of why the Governance Framework's own declaration
(§6: *"the most likely way it could still cause harm is the classifier mislabels an intent that
should be must_not_auto_respond as something else"*) was written as a real risk to design
against rather than a checkbox — it happened, on real data, and the mitigation had to be a
genuinely independent second signal, not a second read of the same classifier output.

## 4d. Closing a disclosed evaluation gap: `ground_truth_responses.json` (post-Day-5)

| What was found | How it was found | Fix | Verified |
|---|---|---|---|
| `ground_truth_responses.json` (200 entries, `must_mention`/`must_not_claim`/`expected_doc_ids` per ticket) was unused anywhere in the codebase — confirmed by grep, not assumed. NFR-03's stated verification method (human review, ≥50 samples, 2 raters) also hadn't happened. | User asked directly whether both dataset files fed the metrics report, which surfaced that a third file (this one) had never been wired in at all. | Built `evaluation/ground_truth_check.py` + a new judge prompt (PR-04, `prompts/evaluation/ground_truth_judge.txt`) that runs all 200 `DEV-*` ground-truth tickets through the real pipeline and judges each generated answer against its `must_mention`/`must_not_claim` lists, plus a citation-hit check against `expected_doc_ids`. | A 3-ticket sanity check first caught a real prompt bug (the judge was echoing the full forbidden-claims list into its output regardless of its own reasoning — one ticket's notes said "implies none of these claims" while the structured field still flagged all three). Rewrote the prompt to force explicit per-item true/false judgments; re-verified as internally consistent. Full 200-ticket run then found 1 raw safety flag, which was itself checked against the actual generated text and confirmed a judge false positive (not a real violation) — final, human-verified figure: **0 genuine `must_not_claim` violations across 195 judged tickets**, 94.5% citation-hit rate, 47.9% `must_mention` coverage (likely an underestimate — see report §7 for spot-checked examples). |

This is worth keeping in the log for what it demonstrates as much as for the numbers: an
automated LLM-judge check found something, and the correct response was to verify the flagged
case against ground truth before reporting it — not to publish the raw number. That discipline
is the same one this whole revision log has tried to apply to every number in this project.

## 4e. Closing the last disclosed gap: the human 2-rater review NFR-03 actually specifies

| What was found | How it was found | Fix | Verified |
|---|---|---|---|
| Every previous entry in this log disclosed the same open item: NFR-03's stated verification method is a human review of at least fifty sampled responses by two independent raters, and the automated LLM-judge pass (§4d) was explicitly labelled a proxy for this, not a substitute — the human review itself had not happened. | Asked directly what still needed doing before submission. | Built a review worksheet (`04_Submission/NFR03_Human_Review_Worksheet.csv`) from the final gate run's own output: all 71 tickets the system actually answered, each row pre-populated with the ticket, the generated answer, and the full text of every cited passage — so a rater checks the real source, not the system's own claimed justification. Two independent people rated every ticket for hallucination and citation accuracy. | The two raters agreed on every single ticket: **100% agreement (71/71)**. One ticket, `VAL-0063`, was flagged by both — checked against its cited passage directly before being accepted: the answer's cause diagnosis was genuinely grounded, but its specific instructed action ("go to project settings") did not match the passage's actual resolution step ("check the effective permissions view"), a real finding, not a rater error. Final figures: **hallucination rate 1.4% (1/71)** against the 5% target, **citation accuracy 98.6% (70/71)** against the 95% target — both pass. Computed summary: `evaluation/results/nfr03_human_review_summary.json`. |

An important, deliberate refusal recorded here rather than smoothed over: when first asked to
fill in one of the two rater columns directly, that request was declined, because doing so would
have made the "human 2-rater review" actually one AI pass and one human pass — silently
collapsing the exact distinction this entire log has maintained since §4d, between automated
proxy evidence and the human review NFR-03 was actually written to require. The review only
counts as complete because both raters were real people working independently, which is the
whole reason the resulting agreement rate means anything.

## 5. The reflection

| Question | Your answer |
|---|---|
| What did you most misunderstand about the problem when you wrote version one? | That the interview transcripts, while genuinely useful for framing *why* the problem exists, were not reliable as a source of precise categorical rules (like which intents must hard-escalate) — those needed checking against the labelled data directly, not paraphrasing from what a stakeholder said in conversation. |
| Which piece of discovery work would have caught it earlier? | Cross-tabulating `labels.intent` against `labels.must_not_auto_respond` during Stage 1 discovery itself, rather than deferring that specific check to when the routing logic was actually being written in Stage 2/3. |
| What would you do differently if you started this project again on Monday? | Run every categorical claim from the interviews through the labelled dataset as a cross-tab *during* discovery, before writing the PRD, rather than treating "verify against data" as a Stage 2 activity that happens to catch some of these. |
| What is still uncertain, and what would you need to resolve it? | Three things. First, the standard-tier fairness gap turned out to be mostly explained, not open — the 69.0% vs. 93.3% raw gap (n=42) is largely standard tier submitting always-escalate ticket categories at 2-4x the rate of other tiers; restricted to tickets eligible for auto-answer, the real gap is 93.5% vs. 100%, accounted for by one retrieval miss and one disclosed trade-off. What's genuinely still open is narrower: is that one retrieval miss (`VAL-0029`) a one-off or a pattern specific to how standard-tier tickets are phrased — would need more than n=1 to tell, and the current harness doesn't break out retrieval hit rate by `customer_tier` to check at scale. Second, whether the 81.25% weighted classification accuracy holds up on the true hidden set, given several classes here have single-digit support and their 0% precision/recall figures may just reflect too little data rather than a real weakness — resolved only by the actual graded run. Third, found while finalizing this submission: `results.jsonl` has no per-run filename, so the fairness audit's *segment-level* breakdown (unlike the stable aggregate FCR/escalation figures) drifts slightly across reruns of the same harness — the qualitative finding reproduces, but the exact percentages don't, which would need the harness to persist a per-run results file to fully resolve. |
| What would you flag as the single most valuable thing the full gate run did that no amount of single-ticket testing would have caught? | Two real, materially different defects were found only by running all 80 tickets unattended: a routing bug that would have sent blank responses to 11.25% of customers, and a generation over-caution pattern that was suppressing correct answers on tickets where the right documentation was already found. Both were invisible in every single-ticket and 20-ticket test run through Day 3, and both directly moved the headline numbers once fixed (avoidable-escalation share: 49.1%→28.6%). This is the strongest first-hand evidence for why the Build Specification treats the full unattended run as the gate rather than a formality. |
