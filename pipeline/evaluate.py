import json

from labels import load_labels

import sys
SET = sys.argv[1] if len(sys.argv) > 1 else "eval"
pattern = "data/label*.csv" if SET == "eval" else "data/holdout_labelled*.csv"
labels = load_labels(pattern)
tags = json.load(open(f"data/tags_{SET}.json", encoding="utf-8"))
ids = [i for i in labels if i in tags]


def pct(a, b):
    return f"{a}/{b} = {100 * a / b:.0f}%" if b else "n/a"


primary = sum(tags[i]["theme"] == labels[i]["theme"] for i in ids)
any_match = sum(tags[i]["theme"] in {labels[i]["theme"], labels[i]["secondary"]} for i in ids)
print(f"\nReviews scored: {len(ids)}")
print("Primary-theme agreement:", pct(primary, len(ids)))
print("Any-match agreement:   ", pct(any_match, len(ids)))

problems = [i for i in ids if labels[i]["severity"] and labels[i]["theme"] not in ("praise", "no_signal")]
exact = sum(tags[i]["severity"] == labels[i]["severity"] for i in problems)
near = sum(tags[i]["severity"] is not None and abs(tags[i]["severity"] - labels[i]["severity"]) <= 1 for i in problems)
print("Severity exact:        ", pct(exact, len(problems)))
print("Severity within 1:     ", pct(near, len(problems)))

tp = sum(tags[i]["churn_signal"] and labels[i]["churn"] for i in ids)
fp = sum(tags[i]["churn_signal"] and not labels[i]["churn"] for i in ids)
fn = sum((not tags[i]["churn_signal"]) and labels[i]["churn"] for i in ids)
print(f"Churn: true positives {tp}, false positives {fp}, missed {fn}")
if tp + fp:
    print("  precision:", f"{100 * tp / (tp + fp):.0f}%")
if tp + fn:
    print("  recall:   ", f"{100 * tp / (tp + fn):.0f}%")

print("Evidence quotes verbatim:", pct(sum(tags[i]["quote_ok"] for i in ids), len(ids)))
print("Churn phrases verbatim: ", pct(sum(tags[i]["churn_phrase_ok"] for i in ids), len(ids)))

print("\nDISAGREEMENTS (primary theme)")
for i in ids:
    if tags[i]["theme"] != labels[i]["theme"]:
        print(f"- {labels[i]['text'][:90]!r}")
        print(f"    you: {labels[i]['theme']} | model: {tags[i]['theme']}")

print("\nSEVERITY MISMATCHES")
for i in problems:
    if tags[i]["severity"] != labels[i]["severity"]:
        print(f"- you {labels[i]['severity']} | model {tags[i]['severity']} | {labels[i]['theme']} | {labels[i]['text'][:70]!r}")

print("\nQUOTE FAILURES")
for i in ids:
    if not tags[i]["quote_ok"]:
        print("- quote: ", repr(tags[i]["evidence_quote"] or tags[i].get("rejected_quote")))
        print("  review:", repr(labels[i]["text"][:150]))

print("\nCHURN MISMATCHES")
for i in ids:
    if tags[i]["churn_signal"] != labels[i]["churn"]:
        print(f"- you {labels[i]['churn']} | model {tags[i]['churn_signal']} | {labels[i]['text'][:100]!r}")