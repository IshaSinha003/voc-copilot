import json
import re
import sys
from datetime import date

sys.stdout.reconfigure(encoding="utf-8")

CHURN_BONUS = 5
EXCLUDE_IDS = set()  # review ids to hide completely
REC_FILE = "data/recommendations_frozen_2026-10-22.json"
INVISIBLE = re.compile(r"[\u200b\u200c\u200d\ufeff]")
VERSION_CAVEAT = ("Version concentration seen, but based on fewer than 10 reviews that state a "
                  "version: a question to check, not a finding.")

REDACTIONS = {"4902adc2-6a19-4e2d-9eeb-ae92d9c4f37b": [("Hitesh Patel", "[NAME]")]}
KNOWN_ERRORS = {"1f2efad6-6f82-4370-a9b2-cf8095c67f41":
                "Known tagging error: this review is about a balance screenshot, not a crash."}

# (title contains, field, old text, new text). The title edit must stay last for its recommendation.
HUMAN_EDITS = [
    ("General App Malfunction", "rationale",
     "This prevents distinguishing between crashes, network issues, functional bugs, and other root causes.",
     "This makes it impossible to tell whether the reports are about crashes, network problems, bugs or something else."),
    ("App Crashes on Launch", "rationale",
     "suggesting potentially different root causes that require investigation",
     "which may be different problems that need to be investigated separately"),
    ("Incoming Payment Delays", "proposed_action",
     "Establish whether delays are widespread, isolated to specific transaction types, or correlated with recent app versions.",
     "Establish whether delays are widespread or isolated to specific transaction types."),
    ("Incoming Payment Delays", "user_problem",
     "Users report incoming payments from others are not reflecting promptly or are taking longer than expected to arrive.",
     "Users report payments that fail, arrive late or do not show up. The group mixes different problems: incoming money not reflecting, slow processing of payments made, and one report of other payment methods failing after UPI Lite was added."),
    ("Incoming Payment Delays", "title",
     "Incoming Payment Delays or Non-Receipt",
     "Payment Failures and Delays (mixed group)"),
]

reviews = {r["id"]: r for r in json.load(open("data/reviews.json", encoding="utf-8"))}
tags = json.load(open("data/tags_all.json", encoding="utf-8"))
clusters = json.load(open("data/clusters_corrected.json", encoding="utf-8"))
recs = json.load(open(REC_FILE, encoding="utf-8"))
unit_theme = {u["id"]: u["theme"] for u in recs["units"]}


def clean(s):
    return INVISIBLE.sub("", s)


def priority(n, sev, churn):
    return round(n * sev + (CHURN_BONUS if churn else 0), 1)


sub_of = {i: s["name"] for t in clusters["themes"] for s in t["subclusters"] for i in s["review_ids"]}

shown, problem_reviews = {}, []
for t in clusters["themes"]:
    for i in t["review_ids"]:
        if i in EXCLUDE_IDS:
            continue
        text = clean(reviews[i]["text"])
        for old, new in REDACTIONS.get(i, []):
            text = text.replace(old, new)
        shown[i] = text
        item = {"id": i, "date": reviews[i]["date"], "rating": reviews[i]["rating"], "text": text,
                "theme": t["theme"], "subcluster": sub_of.get(i),
                "severity": tags[i]["severity"], "churn_signal": tags[i]["churn_signal"]}
        if i in KNOWN_ERRORS:
            item["note"] = KNOWN_ERRORS[i]
        problem_reviews.append(item)

dropped = 0


def fix_quotes(quotes):
    global dropped
    out = []
    for q in quotes:
        text = shown.get(q["review_id"])
        quote = re.sub(r"^[^\w]+", "", clean(q["quote"]))
        if text and quote and quote in text:
            out.append({**q, "quote": quote})
        else:
            dropped += 1
    return out


themes = []
for t in clusters["themes"]:
    themes.append({
        "theme": t["theme"], "n": t["n"], "mean_severity": t["mean_severity"],
        "severity3_share": t["severity3_share"], "churn_count": t["churn_count"],
        "priority": priority(t["n"], t["mean_severity"], t["churn_count"]),
        "quotes": fix_quotes(t["quotes"]),
        "subclusters": [{**{k: s[k] for k in ("name", "definition", "n", "mean_severity",
                                              "severity3_share", "churn_count")},
                         "quotes": fix_quotes(s["quotes"]),
                         "priority": priority(s["n"], s["mean_severity"], s["churn_count"])}
                        for s in t["subclusters"]],
    })
themes.sort(key=lambda x: x["priority"], reverse=True)

for r in recs["recommendations"]:
    r["quotes"] = fix_quotes(r["quotes"])
    r["themes"] = sorted({unit_theme[c] for c in r["cited_units"]})
    r["evidence"]["version_notes"] = [VERSION_CAVEAT if "over-represented" in n else n
                                      for n in r["evidence"]["version_notes"]]
    r["human_edits"] = []

edits_applied = 0
for title_part, field, old, new in HUMAN_EDITS:
    hit = False
    for r in recs["recommendations"]:
        if title_part in r["title"] and old in r[field]:
            r[field] = r[field].replace(old, new)
            r["human_edits"].append(field)
            edits_applied += 1
            hit = True
    if not hit:
        print(f"WARNING: edit not applied ({title_part} / {field})")

s = recs["sample"]
out = {
    "meta": {"generated": date.today().isoformat(), "sample": s, "overview": clusters["overview"]},
    "limits": [
        f"Sample of {s['reviews']} Google Play reviews from {s['from']} to {s['to']} (two days): it shows what users complained about in those days, not long-term trends.",
        "Sub-cluster membership varies between runs; the shown clustering was audited and hand-corrected.",
        "Churn signals are rare in this sample, so churn findings are low confidence.",
        "Reviews alone cannot say how many users are affected or why a problem happens.",
    ],
    "reviews": problem_reviews,
    "themes": themes,
    "recommendations": recs["recommendations"],
    "not_recommended": [{**x, "reason": "Eligible, but no recommendation was generated (the model was limited to four per run)."}
                        for x in recs.get("not_recommended", [])],
    "weak_signals": recs["weak_signals"],
}
json.dump(out, open("data/dashboard_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

flag = re.compile(r"name is|\[NUMBER\]|\[ID\]|@|regards|sincerely", re.I)
print(f"Exported {len(problem_reviews)} reviews, {len(themes)} themes, {len(out['recommendations'])} recommendations")
print(f"Quotes dropped by the substring check: {dropped}. Human edits applied: {edits_applied} (expected 5)")
print("\nPersonal-detail check (redacted reviews skipped):")
for r in problem_reviews:
    if r["id"] not in REDACTIONS and flag.search(r["text"]):
        print(f"- {r['id']}: {r['text'][:110]!r}")
print("Saved data/dashboard_data.json")