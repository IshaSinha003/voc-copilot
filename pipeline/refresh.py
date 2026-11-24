"""Automatic refresh CANDIDATE. Runs the full pipeline and writes dashboard/dashboard_data.json
plus refresh_report.md. A person must audit it before it goes live (merge the pull request).
Run from the repo root:  python pipeline/refresh.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from google_play_scraper import Sort, reviews as fetch

APP_ID = "com.phonepe.app"
COUNT = int(os.getenv("REFRESH_COUNT", "1500"))
CHURN_BONUS = 5
INV = re.compile(r"[\u200b\u200c\u200d\ufeff]")
PII = re.compile(r"name is|\[NUMBER\]|\[ID\]|@|dear |regards|sincerely|my number|whatsapp", re.I)
CAUSAL = re.compile(r"\b(because|caus\w*|due to|root[- ]causes?|recent changes?|regress\w*|broke\w*|overly strict|"
                    r"false positives?|compatib\w*|misconfigur\w*|versions?)\b", re.I)


PROF = re.compile(r"\b(bastards?|mfs?|f+u+c+k\w*|bitch\w*|bloody fools?|blady|morons?|madarchod|bhenchod|chutiy\w*|gandu|harami\w*)\b", re.I)
SKIP = "--from-recs" in sys.argv  # reuse data/reviews.json, tags and clusters; rerun only recommendations and export


def redact(t):
    t = re.sub(r"\b\d{10,}\b", "[NUMBER]", t)
    return re.sub(r"\b[\w.\-]+@[\w\-]+\b", "[ID]", t)


def run(*a):
    print(">", " ".join(a), flush=True)
    subprocess.run([sys.executable, *a], check=True)


# 1. fetch and clean
Path("data").mkdir(exist_ok=True)
Path("dashboard").mkdir(exist_ok=True)
res, _ = ([], None) if SKIP else fetch(APP_ID, lang="en", country="in", sort=Sort.NEWEST, count=COUNT)
seen, rows = set(), []
for r in res:
    t = redact(INV.sub("", (r["content"] or "").strip()))
    if t and t not in seen:
        seen.add(t)
        rows.append({"id": r["reviewId"], "rating": r["score"], "date": r["at"].strftime("%Y-%m-%d"),
                     "thumbs_up": r["thumbsUpCount"], "app_version": r["reviewCreatedVersion"], "text": t})
if SKIP:
    rows = json.load(open("data/reviews.json", encoding="utf-8"))
else:
    json.dump(rows, open("data/reviews.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"Fetched {len(res)}, kept {len(rows)}")

# 2. existing audited steps, unchanged prompts
if not SKIP:
    run("pipeline/tag_reviews.py", "--set", "all")
    run("pipeline/build_clusters.py")
    shutil.copy("data/clusters.json", "data/clusters_corrected.json")
run("pipeline/build_recommendations.py")

# 3. export with automatic safeguards (no hand edits)
revs = {r["id"]: r for r in rows}
tags = json.load(open("data/tags_all.json", encoding="utf-8"))
cl = json.load(open("data/clusters_corrected.json", encoding="utf-8"))
rec = json.load(open("data/recommendations.json", encoding="utf-8"))
unit_theme = {u["id"]: u["theme"] for u in rec["units"]}
pri = lambda n, s, c: round(n * s + (CHURN_BONUS if c else 0), 1)

all_ids = [i for t in cl["themes"] for i in t["review_ids"]]
shown = {i: revs[i]["text"] for i in all_ids if not PII.search(revs[i]["text"]) and not PROF.search(revs[i]["text"])}
excluded = len(all_ids) - len(shown)
sub_of = {i: s["name"] for t in cl["themes"] for s in t["subclusters"] for i in s["review_ids"]}


def fq(qs):
    out = []
    for q in qs:
        x = re.sub(r"^[^\w]+", "", INV.sub("", q["quote"]))
        if (q["review_id"] in shown and x and x in shown[q["review_id"]]
                and not PROF.search(x) and not PII.search(x)):
            out.append({**q, "quote": x})
    return out


plist = [{"id": i, "date": revs[i]["date"], "rating": revs[i]["rating"], "text": shown[i], "theme": t["theme"],
          "subcluster": sub_of.get(i), "severity": tags[i]["severity"], "churn_signal": tags[i]["churn_signal"]}
         for t in cl["themes"] for i in t["review_ids"] if i in shown]
themes = sorted([{
    "theme": t["theme"], "n": t["n"], "mean_severity": t["mean_severity"], "severity3_share": t["severity3_share"],
    "churn_count": t["churn_count"], "priority": pri(t["n"], t["mean_severity"], t["churn_count"]),
    "quotes": fq(t["quotes"]),
    "subclusters": [{**{k: s[k] for k in ("name", "definition", "n", "mean_severity", "severity3_share", "churn_count")},
                     "priority": pri(s["n"], s["mean_severity"], s["churn_count"]), "quotes": fq(s["quotes"])}
                    for s in t["subclusters"]]} for t in cl["themes"]], key=lambda x: -x["priority"])

flags = []
for r in rec["recommendations"]:
    r["quotes"] = fq(r["quotes"])
    r["themes"] = sorted({unit_theme[c] for c in r["cited_units"]})
    r["evidence"]["version_notes"] = [
        "Version concentration seen, but based on few versioned reviews: a question to check, not a finding."
        if "over-represented" in n else n for n in r["evidence"]["version_notes"]]
    if any(CAUSAL.search(r[f]) for f in ("title", "user_problem", "proposed_action", "rationale")):
        flags.append(r["title"])

dates = sorted(r["date"] for r in rows)
o = cl["overview"]
out = {
    "meta": {"generated": date.today().isoformat(),
             "sample": {"reviews": len(rows), "from": dates[0], "to": dates[-1], "problem_reviews": o["problem_reviews"]},
             "overview": o, "human_review": "pending"},
    "limits": [f"Sample of {len(rows)} Google Play reviews from {dates[0]} to {dates[-1]}: it shows what users complained about in that period, not long-term trends.",
               "Sub-cluster membership varies between runs.",
               "Churn signals are rare, so churn findings are low confidence.",
               "Reviews alone cannot say how many users are affected or why a problem happens."],
    "reviews": plist, "themes": themes, "recommendations": rec["recommendations"],
    "not_recommended": [{**x, "reason": "Eligible, but no recommendation was generated (the model was limited to four per run)."}
                        for x in rec.get("not_recommended", [])],
    "weak_signals": rec.get("weak_signals", []),
}
json.dump(out, open("dashboard/dashboard_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

report = [f"# Refresh candidate {out['meta']['generated']}",
          f"Reviews: {len(rows)} ({dates[0]} to {dates[-1]}). Problem reviews: {o['problem_reviews']}. "
          f"Shown in the list: {len(plist)} ({excluded} left out because they look like personal details or abusive language).", ""]
report += [f"- {t['theme']}: {t['n']} reviews, priority {t['priority']}" for t in themes]
report += ["", "## Automatic checks",
           f"- Recommendations with causal wording: {flags or 'none'}",
           "- Every quote was re-checked as an exact substring of the shown review text.",
           "", "## A person must do these before merging",
           "- [ ] Read the sub-clusters of the largest theme and count misfits",
           "- [ ] Read every recommendation: grounded, no cause claims, actionable",
           "- [ ] Skim all review text in dashboard/dashboard_data.json for names or phone numbers",
           "- [ ] Open the Vercel preview for this branch and click through it",
           '- [ ] Change "human_review": "pending" to today\'s date in dashboard/dashboard_data.json']
Path("refresh_report.md").write_text("\n".join(report), encoding="utf-8")
print("Saved dashboard/dashboard_data.json and refresh_report.md")