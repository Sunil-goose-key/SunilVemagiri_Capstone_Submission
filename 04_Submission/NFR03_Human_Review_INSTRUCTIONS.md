# NFR-03 human review — instructions

**Completed.** Two independent raters finished this review over all 71 sampled responses:
100% inter-rater agreement, 1.4% hallucination rate, 98.6% citation accuracy — both figures
pass their NFR-03 targets. Full figures and the one flagged ticket's write-up are in
`Report_Draft.md` §7, `Stage_2_PRD_v1.md` NFR-03, and `evaluation/results/
nfr03_human_review_summary.json`. The instructions below are kept as a record of the method
actually followed, per the Evaluation Framework's own requirement to state how a figure was
established, not only what it is.

This was the one item from the Evaluation Framework that genuinely needed two humans, not
automation: *"Sample at least fifty responses, have two people assess them independently, and
report your agreement rate."* The automated LLM-judge pass in `Report_Draft.md` §7 remains
disclosed as supplementary evidence, not a substitute for this.

## What's already done for you

`NFR03_Human_Review_Worksheet.csv` contains all **71** tickets from the final gate run
(`evaluation/results/results.jsonl`) that the system actually auto-answered — above the
minimum sample of fifty, so you don't need to sample down further unless you want to. Each row
already has everything a rater needs to judge without looking anything else up:

- the original ticket (subject + body)
- the system's generated answer
- the full text of every passage the answer cited (not just the "supports" snippet the system
  itself claimed — the whole passage, so a rater can check that claim rather than trust it)

## What you and a second rater need to do

Open the CSV in Excel or Google Sheets. **Two people, working independently** (not discussing
answers until both are done — that's the whole point of an agreement rate), fill in for every
row:

1. **`raterN_hallucination_free_Y_N`** — does the generated answer make any claim *not*
   actually supported by the cited passage text in that row? If every claim is supported,
   mark **Y**. If anything is invented, unsupported, or overstated relative to what the
   passage actually says, mark **N**.
2. **`raterN_citations_support_claims_Y_N`** — for each citation, does the passage it points to
   actually contain the information the answer attaches to it? Mark **N** if a citation is
   present but doesn't really back up what it's attached to (the Evaluation Framework calls
   this out specifically: a citation that doesn't support its claim is worse than no citation).
3. **`raterN_notes`** — a short phrase if you marked N, so the disagreement (if any) is
   explainable later, not just a number.

## After both raters are done

Fill in `agreement_Y_N` per row (did rater 1 and rater 2 agree on both Y/N columns?), then
compute:

- **Hallucination rate** = tickets where either rater marked hallucination_free = N, divided by
  71 (report both raters' individual rates too if they differ).
- **Citation accuracy** = same idea for the citations column.
- **Agreement rate** = rows where both raters agreed on both questions, divided by 71.

These three numbers are exactly what got computed and written into `Report_Draft.md` §7 and
`Stage_2_PRD_v1.md` NFR-03 — see `evaluation/results/nfr03_human_review_summary.json` for the
final, persisted figures.

## Who's the second rater?

This is a solo project, so it has to be someone else — a classmate, a friend, anyone who can
read the ticket and answer and make an honest independent call. They don't need to know the
system to do this; the worksheet gives them everything required.
