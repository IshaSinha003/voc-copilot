# Run 1
# Eval log: tagging step (30 hand-labelled PhonePe reviews)

| Run | Prompt | What changed | Primary theme | Severity exact | Churn (TP / FP / missed) | Quotes verbatim | Notes |
|---|---|---|---|---|---|---|---|
| 1 | v1 (rules 1-7) | First run, rubric v1 turned into prompt | 27/30 = 90% | 5/14 = 36% | 1 / 0 / 1 | 29/30 = 97% | First-run score, never edited. 3 disagreements: support vs account blocked, "super ha" (praise vs no_signal), cashback vs payment not received. |
| 2 | v2 (adds rules 8-9) | Added rule 8 (short Hinglish praise is praise, not no_signal) and rule 9 (underlying problem is primary, support is secondary) | 28/30 = 93% | 6/14 = 43% | 0 / 0 / 2 | 29/30 = 97% | +1 review fixed ("super ha"). Churn changed with no prompt change touching it, so no temperature=0 yet. |

## Label corrections after run 1 (done by rule, not to match the model)
- (add here once you apply them)



# Run 2
# Eval log: tagging step (30 hand-labelled PhonePe reviews)

| Run | Prompt | What changed | Primary theme | Severity exact | Churn (TP / FP / missed) | Quotes verbatim | Notes |
|---|---|---|---|---|---|---|---|
| 1 | v1 | First run, rubric v1 turned into prompt | 27/30 = 90% | 5/14 = 36% | 1 / 0 / 1 | 29/30 = 97% | First-run score, never edited. |
| 2 | v2 | Added rule 8 (short Hinglish praise is praise, not no_signal) and rule 9 (underlying problem is primary, support is secondary) | 28/30 = 93% | 6/14 = 43% | 0 / 0 / 2 | 29/30 = 97% | +1 review fixed ("super ha"). Churn changed with no prompt change touching it. |

## Label corrections after run 1 (done by rule, not to match the model)
- (add here once you apply them)
