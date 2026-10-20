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
