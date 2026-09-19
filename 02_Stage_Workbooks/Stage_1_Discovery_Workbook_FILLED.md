# Stage One: Discovery Workbook

*Mirrors the structure of `Stage_1_Discovery_Workbook.pdf`. Figures below are computed directly
from `05_Datasets/development_tickets.json` (n=500), not estimated — see
`evaluation/discovery_stats.py` for the exact computation once written, so this is reproducible.*

## 1. Section one: what the interviews tell you

| Who | What they told you | What they appear not to know | What to verify in the data |
|---|---|---|---|
| Marcus Adeyemi, Head of Support | Underwater on volume (500+/wk, 6 agents); reports response time (8–12hr vs. 2hr SLA) but privately cares more about FCR (42% vs. 65% benchmark); hard failure = a confidently wrong answer sent to a customer; compliance review this autumn requires explainability; enterprise must not silently degrade | His own ticket-type breakdown ("I'd be guessing") | Actual intent/channel/tier distribution |
| Sofia Restrepo, Tier One Agent | Estimates ~70% of tickets are repeats she's answered before; documentation itself is fine but internal search is unusable so she keeps a personal answer file; escalates on low confidence, unknown answers, or security flags; wants a system that hands her a draft + page, not one that replaces her; believes non-fluent-English tickets score worse and thinks nobody has measured it | That this belief about non-fluent tickets may not hold in the data | % answerable from docs; FCR/CSAT split by `language_fluency` |
| Daniel Okonkwo, Tier Two Engineer | Claims ~half of what reaches him was T1-resolvable given more confidence/findability; escalations arrive with zero context (raw forwarded thread); worried automation will "learn" from stale/wrong personal snippet files; security, billing/refund commitments, and data-residency must never be automated | That his estimate is checkable against `answerable_from_docs` × `escalated` | Share of escalated tickets that were `answerable_from_docs = true` |
| Ines Varga, Technical Writer | 29 articles, reviewed on rotation, accurate within cycle; failure is *findability* — internal keyword search doesn't match customer phrasing (example: "my deployment keeps dying" vs. article titled "resolving container health check failures"); wants per-answer citations so a wrong answer can be traced to article-vs-system; confirms feature requests/roadmap/novel incidents have no article to retrieve | Whether her phrasing-mismatch theory is the dominant driver vs. e.g. genuine doc gaps | Cross-check `answerable_from_docs=false` tickets against whether a plausible doc category exists |
| Ravi Menon, Customer | Waiting cost is not uniform — a blocked deployment costs far more than a "how does X work" question, same queue; wants to know when a response is automated so he can calibrate trust; worried the business-vs-enterprise response gap will widen and surface at renewal | That enterprise tier is *already* the worst-performing tier on FCR today | FCR/CSAT by `customer_tier` |

### Where the accounts disagree (resolved with data)

| Disagreement | Who says what | How the data settles it | What follows from the answer |
|---|---|---|---|
| Escalation rate reflects genuine tier-two-only work | Marcus reports 58% escalation as the headline number; Daniel says roughly half of what reaches him didn't need to | **49.1% (138/281) of all escalated tickets were themselves `answerable_from_docs = true`.** Daniel's estimate is almost exactly right. | The escalation problem is substantially a *retrieval/confidence* failure, not a tier-two-expertise shortfall — this should be the system's primary target, not a secondary benefit |
| Whether documentation is the bottleneck | Implicit assumption behind "build a chatbot" is that answers need to be generated; Sofia and Ines independently say the docs are fine, the problem is finding them | 71.4% of tickets are `answerable_from_docs = true` using the existing 29 articles — the knowledge exists | Retrieval quality, not content authorship, is the leverage point; do not scope in rewriting documentation |
| Whether non-fluent-English tickets are under-served today | Sofia believes they score worse and are under-measured | They do **not** score worse in the current human-handled baseline: FCR 45.8% (non-fluent) vs. 43.2% (fluent); CSAT 3.04 vs. 2.95 | Sofia's belief doesn't hold *today*, because agents currently compensate by asking clarifying questions — but this is exactly the failure mode a retrieval-dependent system could introduce that doesn't exist yet, since retrieval depends on phrasing matching the docs. Carry this into the fairness audit as a risk to actively test, not a settled non-issue |
| Whether enterprise customers are protected | Marcus and Ravi both worry about enterprise/business service *becoming* unequal in the future | Enterprise **already has the worst FCR of any tier today**: 37.3% vs. 48.2% (business) vs. 43.1% (standard) | The equity concern is not hypothetical or automation-caused — it predates the project. NFR/success measure should track tier-level FCR explicitly, not just an overall average that would hide this |

### What nobody said

| What was never mentioned | Why you would have expected it | How you will check it |
|---|---|---|
| The actual proportion of tickets with no documented answer at all (28.6%) | Directly determines how often the system must say "I don't know" rather than retrieve — nobody in the interviews quantified this | Confirmed via `answerable_from_docs=false` count; these skew toward feature requests, roadmap questions and novel incidents per Ines |
| That urgency and resolution time don't move together the way you'd expect | You'd expect "high urgency" tickets to be resolved fastest | High-urgency tickets take *longer* on average (478.5 min vs. 390.6 min for low) and have the *lowest* FCR (39.7% vs. 48.4%) — urgency correlates with genuine difficulty, not speed of handling |
| Effort concentration in specific categories | Marcus never broke down where agent time actually goes | `security_incident` and `compliance_request` are 5.2% of volume each but 9.7% and 8.4% of total resolution-time respectively — nearly double their share of effort relative to volume |

## 2. Section two: what the ticket data shows

*Computed from all 500 rows of `development_tickets.json`.*

| What to measure | Your figure | Where the figure came from | What surprised you about it |
|---|---|---|---|
| Total tickets in the sample | 500 | `len(tickets)` | — |
| Split by channel | email 42.4% (212), chat 31.0% (155), docs_comment 15.6% (78), forum 11.0% (55) | `channel` field | Matches the brief's channel description ordering |
| Split by intent | 22 classes, fairly even (top: data_residency 5.8%, data_export 5.8%, rollback_request 5.6%) | `labels.intent` | No single dominant intent — a long, flat tail, not a Pareto-dominated one |
| Split by urgency | medium 45.2%, high 29.2%, low 25.6% | `labels.urgency` | — |
| Proportion marked resolved on first contact | 43.8% (219/500) | `history.first_contact_resolution` | Matches the brief's stated baseline (42%) closely — the dev sample is representative |
| Average satisfaction rating | 2.97 / 5 | `history.csat_rating` | Slightly below the brief's stated 3.2 population baseline — worth noting as a sampling caveat in the report |
| Most frequent single question type | Tied: data_residency and data_export (29 tickets each, 5.8%) | `labels.intent` | Both are answerable-from-docs categories, not obscure edge cases |
| Proportion answerable from existing documentation | **71.4% (357/500)** | `labels.answerable_from_docs` | This is the single most load-bearing number in the whole discovery — confirms the "findability, not knowledge" framing |
| Proportion marked non-fluent, and their outcomes | 24.0% (120/500); FCR 45.8%, CSAT 3.04, escalation 54.2% — all *better* than the fluent segment | `language_fluency` + `history.*` | Contradicts Sofia's stated belief (see disagreements table) |
| Outcomes by customer tier | Enterprise: FCR 37.3%, CSAT 3.05 (n=83). Business: FCR 48.2%, CSAT 2.91 (n=164). Standard: FCR 43.1%, CSAT 2.98 (n=253) | `customer_tier` + `history.*` | Enterprise has the *lowest* FCR despite presumably tighter SLAs |
| Proportion that are repeat contacts | 21.6% (108/500) | `history.repeat_contact` | Over a fifth of tickets are the same issue coming back — a real "false resolution" signal, not just a slow-response problem |

**Two rows that matter more than the rest**, confirmed: the 71.4% answerable-from-docs figure says CloudServe has a delivery problem, not a knowledge problem; and the non-fluent segment, while not currently worse off, is flagged as the segment most likely to develop a fairness gap once retrieval (which depends on phrasing matching the docs) replaces a human who currently asks clarifying questions.

## 3. Section three: where the time actually goes

| Ticket category | Share of volume | Estimated share of effort (resolution-time proxy) | Why the two differ | Evidence for your estimate |
|---|---|---|---|---|
| security_incident | 5.2% | 9.7% | Longer investigation, higher stakes, more back-and-forth (avg 785.9 min vs. overall avg 421.7 min) | `history.resolution_time_minutes` grouped by `labels.intent` |
| compliance_request | 5.2% | 8.4% | Requires evidence-gathering and sign-off, not a quick lookup | Same |
| data_residency | 5.8% | 7.1% | Legal/contractual nuance per customer region | Same |
| feature_request | 4.0% | 6.9% | No documented answer exists (Ines) — agents spend time explaining "not currently possible" and routing to product | Same |
| deployment_failure | 5.4% | 6.2% | Diagnostic, often multi-step | Same |
| rollback_request, billing_query | 5.6%/4.8% | 4.6%/4.5% | Below-average share of effort relative to volume — comparatively quick to resolve (350/393 min avg) | Same |

Effort is not proportional to volume: `security_incident` and `compliance_request` together are 10.4% of volume but 18.1% of total resolution-time — the categories Daniel specifically named as ones that must never be automated are also disproportionately expensive today, which is a reason to route them to a well-briefed human fast (with retrieved context attached) rather than a reason to try to automate them.

### The steps an agent takes on a typical ticket (reconstructed from Sofia's transcript)

| Step | What the agent does | Roughly how long | Could this be automated? |
|---|---|---|---|
| 1 | Sort queue by age, pick the oldest ticket nearing SLA breach | ~1 min | Yes — trivial triage/prioritization, not the bottleneck |
| 2 | Read the ticket and decide if it's "seen before" (≈70% are, per Sofia) | 1–2 min | Partially — this is exactly what intent classification + retrieval replaces |
| 3 | Search for the answer — in practice, search her own personal snippet file rather than the official docs, because internal keyword search fails on phrasing (Ines) | 2–15 min depending on match quality | **Yes — this is the core bottleneck** and the direct target of the retrieval layer |
| 4 | Write out the answer, adapting the snippet to the specific ticket | 2–5 min | Partially — generation with citations replaces this for the confident cases |
| 5 | Decide whether to send or escalate (confidence gut-check, security flag, or unknown) | <1 min, but high-stakes | Yes — this is the routing decision, made explicit and logged instead of implicit and unaudited |

Step 3 is where the minutes accumulate, exactly as flagged in the workbook's own guidance — and it is squarely a retrieval problem, not a generation or classification problem.

## 4. Section four: what the client counts as success

| Measure | Who watches it | Current value | What they would call success | How confident are you in this? |
|---|---|---|---|---|
| First contact resolution | Marcus (privately, more than the SLA metric) | 42–43.8% | 60%+ (industry benchmark he quotes: 65%) | High — stated directly and repeated |
| Average time to first reply | Marcus (reports this to the executive team) | 8–12 hrs | Under 2 hrs (the SLA), ideally under 5 min automated | High — it's the metric in the service agreement |
| Customer satisfaction | Marcus, indirectly via renewal conversations | 3.2/5 (population) / 2.97 (dev sample) | 4.0+ | Medium — no live customer data, proxy only |
| Escalation rate | Marcus (headline), Daniel (disputes what's *inside* it) | 56.2% (dev sample) / 58% (population) | 30% or lower | High for the headline number; the *composition* of escalations (49% avoidable) is the more actionable finding |
| Enterprise tier parity | Marcus, Ravi | Enterprise already has the *worst* FCR (37.3%) | No degradation — arguably needs active repair, not just protection | High — directly computed, not assumed |

### The sentence test

| Prompt | Your answer |
|---|---|
| This project will have been worth doing if, within three months of launch, ... | ...the share of escalations that were answerable from documentation drops from 49% toward single digits, and first-contact resolution rises measurably above 43.8% without an increase in the rate of wrong-answer complaints. |
| We will know it did not work if we see ... | ...escalation composition unchanged (still ~half avoidable), or FCR up but CSAT down (meaning the system is answering more often but worse), or a widening gap between enterprise and other tiers. |
| The measure the client will actually be judged on internally is ... | First contact resolution, per Marcus's own account, despite time-to-first-reply being the metric reported externally. |

## 5. Section five: data, constraints and risk

| Data source | What it contains | Quality and gaps | Access constraints | Private data present? |
|---|---|---|---|---|
| Support tickets (`development_tickets.json`, `validation_tickets.json`) | 500 + 80 tickets, full schema incl. customer identity, channel, labels, historical outcome | Good coverage across channels/tiers; only 500 examples across 22 intent classes means some classes have as few as ~20 examples — precision/recall per class should be reported with sample sizes, not just point estimates | Development/validation sets usable freely and repeatedly per `Dataset_Guide.docx`; the true hidden 120-ticket grading set is never provided | Yes — `customer_id`, `customer_name` present on every ticket; must be excluded from logs/prompts sent to the model provider or explicitly redacted |
| Documentation (`documentation.json`) | 29 markdown articles across 8 categories | Accurate within review cycle per Ines; consistent internal structure (title/symptoms/causes/steps/notes) — informs chunking strategy | Use freely | No |
| Past resolutions (`history.*` block embedded in ticket records) | First-contact flag, resolution time, CSAT, escalation flag, repeat-contact flag | This is the *human baseline to beat*, not a training target — imitating historical CSAT of ~3 would just reproduce the failing baseline | Same as tickets | Indirectly, via linkage to `ticket_id`/`customer_id` |
| Customer records | No separate file — customer attributes (`customer_tier`, `customer_region`, `language_fluency`) are embedded directly in each ticket record rather than provided as a distinct dataset | N/A — confirmed there is no separate customer master file in this pack | N/A | Same PII caveat as tickets |
| Ground truth responses (`ground_truth_responses.json`) | 200 expert answers with `must_mention`/`must_not_claim` arrays | Directly usable for automated hallucination/coverage checks during development | Use freely, do not confuse with the hidden grading set | No |

### Initial risk register

| What could go wrong | How likely | How bad | Who it affects | First thought on preventing it |
|---|---|---|---|---|
| The system answers confidently and incorrectly | Medium — 71.4% of tickets are answerable, but the 28.6% that aren't are exactly where a model is most likely to fabricate | High | Customers, then agents who inherit the complaint | Grounding guardrail blocks unsupported claims; explicit "I don't know" path for `answerable_from_docs=false` |
| Private information appears in a reply | Low likelihood, high impact | High | Customers whose data leaks | PII guardrail scans every outbound response before release; block, never redact-and-send |
| Some customers get consistently worse answers | Medium — already true today for enterprise on FCR, and plausible for non-fluent English once retrieval depends on phrasing | Medium–High | Enterprise customers (retention risk per Ravi), non-fluent-English customers | Segment the fairness audit on tier, region and fluency explicitly; don't rely on an aggregate figure that would hide this |
| The documentation the system relies on goes stale | Low today (Ines reviews on rotation) | Medium | All customers relying on an out-of-date article | Surface `last_reviewed_days_ago` in retrieval results; flag stale sources in escalations |

## 6. Section six: the problem statement

| Element | Your statement | Which section and row supports it |
|---|---|---|
| What the client asked for | An automated chatbot to answer tickets and cut response time | Interview 1 (Marcus) |
| What the evidence suggests they actually need | A way to reliably surface answers that already exist in documentation, with a trustworthy confidence signal, so first-contact resolution rises and escalations only carry genuinely hard work | §1 disagreements table; §2 (71.4% answerable, 49.1% of escalations avoidable) |
| The gap between those two | A chatbot is a delivery mechanism; the actual defect is retrieval/findability plus the absence of a calibrated confidence signal — building a chat UI without fixing retrieval would reproduce the same failure in a new interface | §1 (Ines, Sofia); §2 |
| Who is affected and how | T1 agents (Sofia) redo already-answered work from memory; T2 engineers (Daniel) receive ~half of escalations that needed no specialist; customers (Ravi) wait uniformly regardless of urgency and can't tell what's automated; enterprise customers already receive the worst FCR of any tier | §1; §2; §4 |
| What will change if solved | Escalations drop in volume and arrive with a drafted summary + sources instead of a bare thread; FCR rises without a rise in wrong-answer complaints; the enterprise FCR gap is actively tracked and closed, not just protected from getting worse | §4 sentence test |
| What is explicitly not in scope | Rewriting documentation content (already accurate per Ines); automating the 17.4% of `must_not_auto_respond` intents (security, billing/refund commitments, data residency per Daniel); a conversational chat interface | §1 (Ines, Daniel); Dataset Guide schema |

### The one paragraph version

> CloudServe's support agents already know the answer to most tickets — 71.4% have a correct answer sitting in the existing 29-article documentation — but they can't reliably find it under time pressure, so they either rebuild it from memory using personal, unreviewed notes or pass the ticket to a more senior engineer. Almost half of everything that reaches that senior tier (49.1%) turns out to be something the documentation already covered, and enterprise customers — despite paying for the tightest service commitments — currently get the worst first-contact resolution of any tier. The fix is not a chatbot; it is making the answers CloudServe already has reliably findable, attaching a trustworthy, checked confidence signal to every response, and making sure the tickets that do need a person arrive with the groundwork already done.

### Before you move to stage two

Checked against all five transcripts: Marcus would recognise the FCR framing (he said it directly); Sofia and Ines would recognise the findability framing (they said it independently of each other); Daniel would recognise the "half of escalations were avoidable" framing (his own estimate, now confirmed); Ravi would recognise the "same queue, different urgency cost" and transparency points, though the statement above doesn't explicitly restate his framing — worth adding "urgency-aware handling" as an NFR consideration in the PRD rather than a rewrite of the paragraph itself.
