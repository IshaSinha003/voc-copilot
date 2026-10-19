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
