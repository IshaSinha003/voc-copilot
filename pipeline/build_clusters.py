import json
import os
import time
import re
from collections import Counter, defaultdict
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()
CLUSTER_MODEL = os.getenv("CLUSTER_MODEL", "claude-sonnet-5-5")
MIN_FOR_SUBCLUSTERS = 8
NON_PROBLEM = {"praise", "no_signal"}

# PM JUDGMENT: you must be able to defend these weights in the PRD.
# priority = (number of reviews x mean severity) + CHURN_BONUS per explicit churn signal
CHURN_BONUS = 5

reviews = {r["id"]: r for r in json.load(open("data/reviews.json", encoding="utf-8"))}
tags = json.load(open("data/tags_all.json", encoding="utf-8"))

missing = [i for i in reviews if i not in tags]
if missing:
    print(f"WARNING: {len(missing)} reviews have no tags and are excluded")

ver_all = Counter(r["app_version"] for r in reviews.values() if r["app_version"])
total_versioned = sum(ver_all.values())

SUB_SYSTEM = """You group PhonePe app reviews that were already assigned to one theme into 2-5 sub-clusters that a product manager could act on separately.
Rules:
- Group by the specific problem described, not by tone.
- Use only the review ids given. Each id may appear in at most one sub-cluster. Leave out reviews that fit no sub-cluster.
- Name = 3 to 6 words. Definition = one sentence on what the reviews have in common.
- Do not guess root causes. Describe what users report.
- A sub-cluster needs at least 3 reviews; otherwise leave those reviews out.
- Leave out any review that does not describe the theme's actual problem (for example, a feature complaint filed under a crash theme).
- If several reviews only say the app "is not working" without naming a symptom, group them as "Not working (symptom not stated)".
- A sub-cluster must describe one specific symptom. Never create a catch-all sub-cluster."""

SUB_TOOL = {
    "name": "record_subclusters",
    "description": "Record the sub-clusters for this theme.",
    "input_schema": {
        "type": "object",
        "properties": {
            "subclusters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "definition": {"type": "string"},
                        "review_ids": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["name", "definition", "review_ids"],
                },
            }
        },
        "required": ["subclusters"],
    },
}


def subcluster(client, theme, ids):
    payload = json.dumps([{"id": i, "text": reviews[i]["text"]} for i in ids], ensure_ascii=False)
    for attempt in range(3):
        try:
            msg = client.messages.create(
                model=CLUSTER_MODEL,
                max_tokens=4000,
                system=SUB_SYSTEM,
                tools=[SUB_TOOL],
                tool_choice={"type": "tool", "name": "record_subclusters"},
                messages=[{"role": "user", "content": f"Theme: {theme}\nReviews:\n{payload}"}],
            )
            for block in msg.content:
                if block.type == "tool_use":
                    return block.input["subclusters"]
        except anthropic.APIError as e:
            print("  API error:", e)
        time.sleep(2 * (attempt + 1))
    return []


def version_info(ids):
    vers = Counter(reviews[i]["app_version"] for i in ids if reviews[i]["app_version"])
    n = sum(vers.values())
    if n < 5:
        return None
    v, c = vers.most_common(1)[0]
    return {"top_version": v, "share_in_group": round(c / n, 2),
            "share_overall": round(ver_all[v] / total_versioned, 2), "versioned_reviews": n}


def expand_quote(text, quote, min_words=8, max_words=40):
    start = text.find(quote)
    if start < 0:
        return None
    end = start + len(quote)
    bounds = [0] + [m.end() for m in re.finditer(r"[.!?।\n]+\s*", text)] + [len(text)]
    s = max(b for b in bounds if b <= start)
    e = min(b for b in bounds if b >= end)
    span = text[s:e].strip()
    if len(span.split()) < min_words and s > 0:
        s2 = max(b for b in bounds if b < s)
        span = text[s2:e].strip()
    if len(span.split()) > max_words:
        return quote
    return span


def pick_quotes(ids, k=3):
    cands = []
    for i in ids:
        q = tags[i].get("evidence_quote")
        text = reviews[i]["text"]
        if not q or q not in text:
            continue
        span = expand_quote(text, q)
        if not span or span not in text:
            continue
        if len(span.split()) < 5 or "my name is" in span.lower():
            continue
        cands.append((tags[i]["severity"] or 0, len(span.split()), i, span))
    cands.sort(reverse=True)
    out, seen = [], set()
    for _, _, i, span in cands:
        if span.lower() in seen:
            continue
        seen.add(span.lower())
        out.append({"review_id": i, "quote": span, "date": reviews[i]["date"]})
        if len(out) == k:
            break
    return out


def stats(ids):
    sevs = [tags[i]["severity"] or 1 for i in ids]
    churn = [i for i in ids if tags[i]["churn_signal"]]
    mean_sev = sum(sevs) / len(sevs)
    return {
        "n": len(ids),
        "mean_severity": round(mean_sev, 2),
        "severity3_share": round(sum(s == 3 for s in sevs) / len(sevs), 2),
        "churn_count": len(churn),
        "priority": round(len(ids) * mean_sev + (CHURN_BONUS if churn else 0), 1),
        "version": version_info(ids),
        "quotes": pick_quotes(ids),
    }


problem_ids = [i for i, t in tags.items() if i in reviews and t["theme"] not in NON_PROBLEM]
by_theme = defaultdict(list)
for i in problem_ids:
    by_theme[tags[i]["theme"]].append(i)

client = anthropic.Anthropic()
themes = []
for theme, ids in by_theme.items():
    entry = {"theme": theme, **stats(ids), "share_of_problem_reviews": round(len(ids) / len(problem_ids), 2),
             "review_ids": ids, "subclusters": []}
    if len(ids) >= MIN_FOR_SUBCLUSTERS:
        print(f"Sub-clustering {theme} ({len(ids)} reviews) with {CLUSTER_MODEL}")
        used = set()
        for sc in subcluster(client, theme, ids):
            valid = [i for i in sc["review_ids"] if i in ids and i not in used]
            if len(valid) < 3:
                continue
            used.update(valid)
            entry["subclusters"].append({"name": sc["name"], "definition": sc["definition"],
                                         "review_ids": valid, **stats(valid)})
        entry["unclustered"] = len(ids) - len(used)
    themes.append(entry)

themes.sort(key=lambda t: t["priority"], reverse=True)

counts = Counter(t["theme"] for t in tags.values())
overview = {"total_reviews": len(reviews), "problem_reviews": len(problem_ids),
            "praise": counts["praise"], "no_signal": counts["no_signal"]}
Path("data/clusters.json").write_text(
    json.dumps({"overview": overview, "themes": themes}, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n{overview}\n")
print(f"{'theme':32}{'n':>4}{'%prob':>7}{'sev':>6}{'sev3':>6}{'churn':>6}{'prio':>7}")
for t in themes:
    print(f"{t['theme']:32}{t['n']:>4}{t['share_of_problem_reviews'] * 100:>6.0f}%{t['mean_severity']:>6}"
          f"{t['severity3_share'] * 100:>5.0f}%{t['churn_count']:>6}{t['priority']:>7}")
    for s in t["subclusters"]:
        print(f"    - {s['name']} ({s['n']})")
        if s["version"]:
            v = s["version"]
            print(f"      version {v['top_version']}: {v['share_in_group'] * 100:.0f}% of this group "
                  f"vs {v['share_overall'] * 100:.0f}% of all reviews")
print("\nSaved data/clusters.json")