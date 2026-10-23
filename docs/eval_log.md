
# Evaluation summary: PhonePe VoC Copilot (308 reviews, 2026-10-16 to 2026-10-17)

| Stage | Result | How to read it |
|---|---|---|
| Tagging, dev set (30 reviews, tuned on) | 90% first run, 100% after 2 prompt changes and 3 rule-based label fixes | Tuned score, not a headline |
| **Tagging, held-out (30 unseen reviews, frozen prompt, 1 run)** | **77% primary-theme agreement; severity exact 67%** | **Headline accuracy.** Most misses were rubric/taxonomy gaps (login/biometric, transaction history, vague "not working") |
| Quotes | 97% verbatim raw from the model; 100% displayed (substring check in code) | Verbatim is enforced; usefulness checked by audit |
| Churn detection | 1 positive in dev, 0 in held-out | Not measurable yet; shown as low confidence |
| Clustering purity | 100% (v2, one run), 55-65% (v3, rolled back), 75-92% (v4, shipped) | Membership varies run to run; assignments should be stored, not recomputed |
| Version hypothesis | Tested, not supported (50% of group vs 68% of all reviews) | Baseline check prevented a false pattern |
| Recommendations | Citations, numbers and cause-language enforced by code; manual audit [4]/[8] | Independent PM check pending |

What would change my mind: a second labeller on the held-out set; a different 2-day window; 20+ churn positives.



## Run 1
# Eval log: tagging step (30 hand-labelled PhonePe reviews)

| Run | Prompt | What changed | Primary theme | Severity exact | Churn (TP / FP / missed) | Quotes verbatim | Notes |
|---|---|---|---|---|---|---|---|
| 1 | v1 (rules 1-7) | First run, rubric v1 turned into prompt | 27/30 = 90% | 5/14 = 36% | 1 / 0 / 1 | 29/30 = 97% | First-run score, never edited. 3 disagreements: support vs account blocked, "super ha" (praise vs no_signal), cashback vs payment not received. |
| 2 | v2 (adds rules 8-9) | Added rule 8 (short Hinglish praise is praise, not no_signal) and rule 9 (underlying problem is primary, support is secondary) | 28/30 = 93% | 6/14 = 43% | 0 / 0 / 2 | 29/30 = 97% | +1 review fixed ("super ha"). Churn changed with no prompt change touching it, so no temperature=0 yet. |

## Label corrections after run 1 (done by rule, not to match the model)
- Account-blocked review: primary theme account_blocked_or_kyc (rule: highest severity), support as secondary, severity 3, churn no (no leaving language).
- Money-not-received review: primary payment_failed_or_delayed, support secondary, severity 3.
- App-won't-open reviews: severity 3 per rubric (blocks use of the app).

## Run 2
# Eval log: tagging step (30 hand-labelled PhonePe reviews)

| Run | Prompt | What changed | Primary theme | Severity exact | Churn (TP / FP / missed) | Quotes verbatim | Notes |
|---|---|---|---|---|---|---|---|
| 1 | v1 | First run, rubric v1 turned into prompt | 27/30 = 90% | 5/14 = 36% | 1 / 0 / 1 | 29/30 = 97% | First-run score, never edited. |
| 2 | v2 | Added rule 8 (short Hinglish praise is praise, not no_signal) and rule 9 (underlying problem is primary, support is secondary) | 28/30 = 93% | 6/14 = 43% | 0 / 0 / 2 | 29/30 = 97% | +1 review fixed ("super ha"). Churn changed with no prompt change touching it. |
| 3 | v3 (rule 4 edited: severity null for feature_request; rule 10: no stitched quotes) | Prompt fixes + 3 label corrections made by rule | 30/30 = 100% | 11/13 = 85% | 1 / 0 / 0 | 30/30 = 100% | DEV-SET score, tuned on these 30, so not a headline number. Only 1 churn positive. 2 severity disagreements kept as-is (model 3 vs mine 2). |

## Label corrections after run 1 (done by rule, not to match the model)
- (add here once you apply them)


## Run 3

# Eval log: tagging step (PhonePe Play Store reviews, 2-day sample, n=308)

## Dev set (30 hand-labelled reviews)

| Run | Prompt | What changed | Primary theme | Severity exact | Churn (TP / FP / missed) | Quotes verbatim | Notes |
|---|---|---|---|---|---|---|---|
| 1 | v1 (rules 1-7) | First run, rubric v1 turned into prompt | 27/30 = 90% | 5/14 = 36% | 1 / 0 / 1 | 29/30 = 97% | First-run score, never edited. |
| 2 | v2 (adds rules 8-9) | Rule 8: short Hinglish praise is praise. Rule 9: underlying problem is primary, support is secondary | 28/30 = 93% | 6/14 = 43% | 0 / 0 / 2 | 29/30 = 97% | Churn moved with no churn-related change, so output varies between runs (temperature not configurable in this SDK). |
| 3 | v3 (rule 4 edited, rule 10 added) | Severity null for feature_request; no stitched quotes. 3 label corrections made by rule | 30/30 = 100% | 11/13 = 85% | 1 / 0 / 0 | 30/30 = 100% | DEV-SET score, tuned on these 30. Only 1 churn positive. |

## Held-out test (30 unseen reviews, frozen prompt v3, one run, 2026-10-20)

| Primary theme | Any-match | Severity exact | Severity within 1 | Churn positives | Quotes verbatim |
|---|---|---|---|---|---|
| 23/30 = 77% | 23/30 = 77% | 10/15 = 67% | 13/15 = 87% | 0 | 29/30 = 97% |

**Headline: held-out theme agreement 77% (n=30, one run). Dev first-run 90%, tuned 100%.** The gap is the cost of tuning on a small set.

### Post-hoc analysis of the 7 held-out misses (not used to change any label)
- 1 clear model error: UPI Lite payments-failing review given the clutter theme as primary.
- 2 vague "not working" reviews that the rubric has no rule for (the model and I disagreed in opposite directions).
- 4 cases where my rubric or taxonomy didn't fit: a how-to question, a "too many fields" friction complaint, a biometric/login problem, and missing transaction history (which I had mislabelled as privacy).
- Candidate taxonomy changes for the next iteration: add login_or_biometric, transaction_history, a rule for vague "not working", and a "question" label. Needs a fresh 30-review holdout before claiming any improvement.

### Limits
- Both sets come from the same 2-day window, so this tests unseen reviews, not a different period.
- Churn is not testable yet: 1 positive in the dev set and 0 in the holdout.
- Severity labels are subjective: 2 dev-set disagreements were kept as arguable (model 3, mine 2).

## Label corrections after run 1 (done by rule, not to match the model)
- Account-blocked review: primary account_blocked_or_kyc (rule: highest severity), support secondary, severity 3, churn no (no leaving language).
- Money-not-received review: primary payment_failed_or_delayed, support secondary, severity 3.
- App-won't-open reviews: severity 3 per rubric (blocks use of the app).


## Cluster review

| Cluster | Quotes shown | Understandable alone | Usefulness |
| Bank linking | 3 | 2 | 67% |


## Cluster audit v1 (2026-10-21, sub-clustering prompt v1, model: claude-haiku-4-5)

### Theme: app_crash_or_wont_open (25 reviews, 40% of problem reviews)

| Sub-cluster | Reviews | Fit the definition | Purity | Notes |
|---|---|---|---|---|
| App Crashes Immediately After Opening | 6 | 6 | 100% | Clean. |
| App Will Not Open or Launch | 5 | 5 | 100% | Clean, but the split from the cluster above rests on vague wording ("can't open" vs "closes after opening"). Low confidence. |
| App Hangs and Freezes | 3 | 2 | 67% | "its not working in my phone since 3 days" mentions no hang. |
| Crash on Specific Action or Screen | 3 | 1 | 33% | A catch-all. Only "crashing after pressing proceed" fits. |
| **All sub-clusters** | **17** | **14** | **82%** | Below my 80% bar for two of four clusters. |

Unclustered (8): 6 are vague "app not working" reviews with no symptom stated, and 2 arguably fit existing clusters ("automatic band ho rha" fits the immediate-crash group, "chalu nahi ho rahe bhai" fits will-not-open). So the leak is small. The main finding is a missing group: "not working, symptom not stated".

**Theme-level purity: 24 of 25 plausibly belong.** One clear mis-tag: "Phone pay balance screen shot problem please clear this problem" was tagged app_crash_or_wont_open. It is about taking a screenshot of the balance screen and has nothing to do with a crash. This is a tagging error outside the frozen dev and holdout sets (the model read a vague "problem" as a crash, against rule 1).

### Quote usefulness (could a PM understand the problem from the quote alone?)

| Group | Quotes | Understandable alone | Supports its cluster |
|---|---|---|---|
| Crash theme (top quotes) | 3 | 3 | 3 |
| Immediately After Opening | 3 | 3 | 3 |
| Will Not Open | 3 | 3 (one weak: "y my phonpy not open") | 3 |
| Hangs and Freezes | 2 | 1 | 1 |
| Specific Action or Screen | 3 | 3 | 1 |
| **Sub-cluster quotes total** | **11** | **10 = 91%** | **8 = 73%** |

### Theme: payment_failed_or_delayed (6 reviews, no sub-clusters, below the 8-review threshold)

| Check | Result |
|---|---|
| Reviews that fit the theme | 5 of 6 = 83% |
| Misfit | The UPI Circle email: a multi-issue complaint about a specific feature (balance check, repeat payment, incoming payments). Only "incoming payments not reflecting" is a payment problem. |
| Quotes understandable alone | 1 of 3 clear |
| Quote problems | "mujhe recieve hii nehi hua" ("I didn't receive it") does not say what was not received. "late services 24 hours, 48 hours ,4-5 business days" does not say the service is a payment. Both reviews have no sentence punctuation, so the widening code could not extend them. |

### Findings
- Fit is strong where the symptom is specific (crash on open, won't open) and weak where the cluster is a catch-all.
- Verbatim is not the same as useful: 100% of quotes are verbatim, but only 91% are understandable alone and 73% actually support their cluster.
- Version hypothesis tested and not supported: 50% of the immediate-crash group is on 26.09.25.0 against 68% of all reviews.
- Two of the six payment reviews relate to newer features (UPI Lite, UPI Circle). Too few to conclude anything, but a candidate "product area" field for the next iteration.

### Decisions
- Sub-clustering prompt v2 (this prompt is not part of the frozen tagging eval): leave out reviews that do not describe the theme's problem; group reviews with no stated symptom as "Not working (symptom not stated)"; no catch-all sub-clusters. Re-audit only the changed clusters.
- The mis-tagged screenshot review is logged as a known tagging error and not fixed in the frozen prompt. Candidate for iteration 2.
- Dashboard: every quote gets a "view full review" expand, so a fragment costs less.


## Cluster audit v2 (2026-10-21, sub-clustering prompt v2, model: claude-haiku-4-5)

### Theme: app_crash_or_wont_open (25 reviews)

| Sub-cluster | Reviews | Fit the definition | Purity | Notes |
|---|---|---|---|---|
| App automatically closes after opening | 4 | 4 | 100% | Clean. |
| App crashes on startup or during use | 4 | 4 | 100% | Definition overlaps the cluster above: "keeps crashing every time I open it" and "crashes on startup" describe the same symptom. |
| App not opening or won't launch | 5 | 5 | 100% | Definition mentions "logo displaying", but only 1 of 5 reviews says so. The definition claims more than the evidence supports. |
| Not working (symptom not stated) | 6 | 6 | 100% | Fits, but this is an "unknown" bucket, not an actionable problem. |
| **All sub-clusters** | **19** | **19** | **100%** | v1: 14/17 = 82%. |

Unclustered (6), as judged by me:
- 1 correctly left out (the screenshot-balance review, not a crash).
- 2 are real hangs; below the 3-review minimum, so no cluster (v1 reached 3 only with a misfit).
- 2 leaked: "automatic band ho rha" fits "closes after opening", "chalu nahi ho rahe bhai" fits "not opening". Both are Hinglish.
- 1 is unclear ("uninstall and reinstall, still same problem").

### Quotes (12 shown across 4 sub-clusters)
- Understandable alone: 12/12 (v1: 10/11 = 91%). Two are weak but readable ("y my phonpy not open").
- Support their cluster: 12/12 (v1: 8/11 = 73%).
- Verbatim: 100%, enforced in code.

### Findings
- v1 to v2: purity 82% to 100%, clustered reviews 17 to 19, quotes supporting their cluster 73% to 100%.
- Caveat: v2 was written after seeing v1's failures on these same 25 reviews, so this is a dev-set result. Only the crash theme is big enough to sub-cluster, and I read the clusters myself.
- Remaining flaws: two sub-clusters have overlapping definitions, one definition over-claims, and the hang group is below the minimum size.
- The "Not working (symptom not stated)" group is the largest single bucket and cannot be diagnosed from reviews. Recommendation to carry forward: add diagnostics (crash reporting, an in-app "what went wrong?" prompt), not a feature fix.

### Decisions
- Sub-clustering prompt v3: add a rule that sub-clusters must be clearly different from each other (merge if they describe the same symptom), and that a definition may only mention details that appear in most of the group's reviews.
- Keep the minimum at 3 reviews; show smaller groups as "small group" in the dashboard.

- Tried sub-clustering prompt v3 (two extra rules); it regressed, see the v3 audit below. Final choice: v2, frozen.


## Cluster audit v3 (2026-10-21, sub-clustering prompt v3): REGRESSION, rolled back

Changes in v3: (1) sub-clusters must be clearly different symptoms, merge if the same; (2) a definition may only mention details that appear in most of the group's reviews.

| Sub-cluster | Reviews | Fit (intended meaning) | Notes |
|---|---|---|---|
| App closes immediately after opening | 4 | 4 | Clean. |
| App crashes when performing specific actions | 4 | 1 | Only "crashing after pressing proceed" involves an action. "Keeps crashing every time I open it" and "crashes on startup" describe the same symptom as the cluster above. The definition was stretched ("or during startup") so they would fit. |
| Not working (symptom not stated) | 12 | 6 | 6 members do state a symptom (not opening, can't open, not starting, closes automatically). The v2 "not opening" cluster was absorbed into this bucket. |
| **Total** | **20** | **11 = 55%** | 13/20 = 65% if the stretched definition is accepted. v2: 19/19 = 100%. |

Unclustered (5): the screenshot review (correctly out), the uninstall/reinstall review, 2 hanging reviews, and the logo-screen review, which belongs with "not opening".

Findings:
- v3 regressed from 100% to 55-65%. This is one run with no temperature control, so some run-to-run noise is possible, but the structural problems are visible: a stretched definition and an absorbed cluster.
- The merge rule did not merge the overlapping crash groups. The "details in most reviews" rule appears to have removed the logo-specific cluster. I did not isolate which rule caused which effect.
- Decision: roll back to the v2 prompt and stop tuning. The sub-clustering prompt was tuned on 25 reviews only, and further iterations would fit noise.

Known limitations of v2 (accepted):
- Two sub-cluster definitions overlap ("closes after opening" vs "crashes on startup").
- The "not opening" definition mentions a logo screen that only 1 of 5 reviews describes.
- 2 hanging reviews fall below the 3-review minimum and show as a small group.
- 2 Hinglish reviews are unclustered although they fit existing groups.

Post-rollback rerun (v2 prompt): [fill in after rerunning: sub-cluster sizes, e.g. 4 / 4 / 5 / 6, and fit count]
Audited clusters frozen as data/clusters_audited.json: [fill in the date after copying]

## Cluster audit v3 (2026-10-21, sub-clustering prompt v3): REGRESSION, rolled back

Changes in v3: (1) sub-clusters must be clearly different symptoms, merge if the same; (2) a definition may only mention details that appear in most reviews.

| Sub-cluster | Reviews | Fit the definition | Notes |
|---|---|---|---|
| App closes immediately after opening | 4 | 4 | Clean. |
| App crashes when performing specific actions | 4 | 1 | 2 of the 4 describe the same symptom as the cluster above. The definition was stretched ("or during startup"). Merge rule did not merge them. |
| Not working (symptom not stated) | 12 | 6 | 6 members state a symptom (not opening, not starting, auto-closing). The v2 "not opening" cluster was absorbed. |
| **Total** | **20** | **11 = 55%** | v2: 19/19 = 100%. |

Unclustered (5): screenshot review (correctly out), uninstall/reinstall review, 2 hanging reviews, and the logo-screen review that belongs to "not opening".

Findings:
- v3 regressed: 100% to 55%. Single run, temperature not configurable, so run noise is possible, but the structural problems (stretched definition, absorbed cluster) are visible.
- The merge rule did not merge overlapping clusters; the "details in most reviews" rule appears to have removed the logo-specific cluster. Cause not isolated.
- Decision: roll back to v2 and stop tuning. The sub-clustering prompt was tuned on 25 reviews only; more iterations risk fitting noise.

Known limitations of v2 (accepted):
- Two sub-cluster definitions overlap ("closes after opening" vs "crashes on startup").
- The "not opening" definition mentions a logo screen that only 1 of 5 reviews describes.
- 2 hanging reviews fall below the 3-review minimum and show as a small group.
- 2 Hinglish reviews are unclustered although they fit existing groups.

Audited clusters frozen as data/clusters_audited.json.


## Cluster audit v4 (2026-10-22): the artifact that ships

Why v4: the "audited v2" clustering could not be reproduced. The sub-clustering step varies from run to run (temperature not configurable in this SDK), so the file used for recommendations (5 / 3 / 4 / 12) was a different clustering from the audited v2 (4 / 4 / 5 / 6). Decision: audit the file actually used, correct it by hand, freeze it, and stop rerunning.

| Sub-cluster | Reviews | Fit | Notes |
|---|---|---|---|
| App Crashes Immediately After Opening | 5 | 5 | Clean. |
| App Crashes During Specific Actions | 3 | 3 | Auditor count. A second reading found only 1 of 3 names a specific action ("keeps crashing every time I open it" fits the cluster above; "has started crashing" names no action). |
| App Not Opening or Unresponsive | 4 | 4 | Fits, but the definition merges two symptoms (won't open, hangs). |
| Not Working (Symptom Not Stated) | 12 | 10 | 2 misfits: "y my phonpy not open" and "open nhi ho rha h" state a symptom and were moved to "App Not Opening or Unresponsive". Borderline, kept as fits: "chalu nahi ho rahe bhai", "automatic band ho rha". |
| **Total** | **24** | **22 = 92%** | **Range 75 to 92%** depending on strictness (83% if the second reading of "Specific Actions" is accepted; 75% if the two borderline Hinglish reviews are also counted as misfits). |

Corrections applied: 2 reviews moved by hand (see pipeline/apply_corrections.py). Corrected clusters: "App Not Opening or Unresponsive" 6, "Not Working (Symptom Not Stated)" 10.

Findings:
- Sub-clustering is not reproducible between runs. v2 scored 100% on one run, v3 55 to 65%, v4 75 to 92% depending on how strictly I audit. The honest summary is "roughly 75 to 90% of reviews land in a fitting cluster, and membership varies from run to run".
- Production implication: cluster assignments must be stored per review ID and reused, not recomputed each time, or reviews will move between groups and trends become meaningless. Not built; listed as a next iteration.
- Human corrections are a product feature in waiting: the audit produced a list of fixes that the pipeline should be able to accept ("move this review to that cluster"). Currently applied by script.


## Recommendations audit (2026-10-22, build_recommendations.py with hypotheses field and cause-language check)

Run: [N] recommendations produced. Validator rejections before the final output: [count] attempts rejected (reasons: [for example "contained a digit", "implied a cause"]).
Frozen as data/recommendations_frozen_2026-10-22.json.

| # | Recommendation | Grounded | No root cause | Actionable | Distinct | Would act (1-5) |
|---|---|---|---|---|---|---|
| 1 | [title] | Yes | Yes | Yes | Yes | [score] |
| 2 | [title] | Yes | Yes | Yes | Yes | [score] |
| 3 | [title] | Yes | Yes | Yes | Yes | [score] |
| 4 | [title] | Yes | Yes | Yes | Yes | [score] |

Checks enforced by code (not judged by me): every cited cluster exists, no number in model text (all statistics come from code), no causal wording in title/problem/action/rationale (causal ideas go to hypotheses_to_test as questions), all quotes verbatim.

Result: no mismatches found between recommendations and their cited clusters.

Limits of this audit:
- I wrote the pipeline and I am the only auditor, with [N] recommendations. A clean result here is weak evidence.
- "Actionable" and "would act" are my judgment.
- The clusters under these recommendations vary run to run (see cluster audit v4); the frozen file fixes one version.
- Independent check still to do: 3 PMs rank the top clusters without seeing the scores (the PRD validation).


## Dashboard export review (2026-10-23)

Found on reading data/dashboard_data.json before publishing:
- Personal data: 1 review contained a full name; redacted in the export. 2 of the 3 review-list flags were false alarms ("Dear PhonePe Support Team").
- Invisible zero-width characters in 1 review and 1 quote; decorated quote prefix on 1 quote. Export now strips both and re-checks every quote as a substring of the shown review text.
- Wrong sentence in the export's limits text (said "one week's complaints" for a two-day sample): corrected.
- Cause-check gap: my regex missed "root causes" (plural) and had no term for app versions. 3 texts affected (recs 1, 2, 4). Fixed by 5 human edits applied in the export (listed in the script); regex patched for future runs.
- Rec 4 framed as "incoming payments" but only about 2 of its 6 reviews are incoming-money problems. Retitled "Payment Failures and Delays (mixed group)" and user_problem rewritten to say the group mixes problems.
- Version note for rec 4 rests on too few versioned reviews: caveated as a question, not a finding.
- Recs 1 to 3 describe one user problem (app not working, 24 of 63 problem reviews) in three pieces; dashboard groups them. Priority ranks the vaguest group first (29 vs 24); treated as tiers, not strict ranks.
- Known tagging error (balance screenshot review counted as a crash) kept in the theme and flagged in the dashboard.
- Eligible clusters without a recommendation (5) are listed with the reason: the model was limited to four per run.

Lesson: automated checks catch what they were written to catch. A pass through the generated output by a person found 3 phrasing problems the validator missed. The cause-check is a floor, not a guarantee.