import json
import os
import re
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

CAUSAL = re.compile(r"\b(because|caus\w*|due to|root[- ]causes?|recent changes?|regress\w*|broke\w*|overly strict|false positives?|compatib\w*|misconfigur\w*|versions?)\b", re.I)

load_dotenv()
REC_MODEL = os.getenv("REC_MODEL", "claude-haiku-4-5-20251001")
MIN_N = 3
EXCLUDED_THEMES = {"cashback_and_rewards", "other"}
MAX_RECS = 4
CHURN_BONUS = 5  # PRD formula: n x mean severity + CHURN_BONUS if any churn mention

data = json.load(open("data/clusters_corrected.json", encoding="utf-8"))
reviews = {r["id"]: r for r in json.load(open("data/reviews.json", encoding="utf-8"))}


def priority(n, mean_sev, churn):
    return round(n * mean_sev + (CHURN_BONUS if churn else 0), 1)


def version_note(v):
    if not v:
        return "not enough version data"
    if v["share_in_group"] - v["share_overall"] > 0.10:
        return (f"version {v['top_version']} is over-represented "
                f"({v['share_in_group']:.0%} here vs {v['share_overall']:.0%} of all reviews)")
    return "no evidence that the problem concentrates on one app version"


units, weak_signals = {}, []
for t in data["themes"]:
    if t["theme"] in EXCLUDED_THEMES:
        weak_signals.append({"theme": t["theme"], "n": t["n"], "reason": "excluded by rule"})
        continue
    if t["n"] < MIN_N:
        weak_signals.append({"theme": t["theme"], "n": t["n"], "reason": f"fewer than {MIN_N} reviews"})
        continue
    subs = [s for s in t["subclusters"] if s["n"] >= MIN_N]
    for src, name, definition in (
        [(s, s["name"], s["definition"]) for s in subs] if subs else [(t, t["theme"], t["theme"].replace("_", " "))]
    ):
        uid = f"U{len(units) + 1}"
        units[uid] = {"id": uid, "name": name, "theme": t["theme"], "definition": definition,
                      "n": src["n"], "mean_severity": src["mean_severity"],
                      "severity3_share": src["severity3_share"], "churn_count": src["churn_count"],
                      "priority": priority(src["n"], src["mean_severity"], src["churn_count"]),
                      "version_note": version_note(src.get("version")), "quotes": src["quotes"]}

print(f"{len(units)} eligible evidence units; {len(weak_signals)} weak or excluded themes")

pack = [{"id": u["id"], "name": u["name"], "definition": u["definition"],
         "reviews": u["n"], "mean_severity_1_to_3": u["mean_severity"],
         "share_severity_3": u["severity3_share"], "churn_mentions": u["churn_count"],
         "version_note": u["version_note"], "example_quotes": [q["quote"] for q in u["quotes"]]}
        for u in units.values()]

SYSTEM = f"""You help a product manager turn grouped Google Play reviews of PhonePe into roadmap recommendations.
You receive evidence units (U1, U2, ...). Each is a group of reviews with a definition and example quotes.

RULES
1. Base every recommendation only on the evidence units. Cite the unit ids in cited_units (1 to 3 per recommendation).
2. State only what users report. Never state or imply a cause, and never link a problem to an app version, update, device, feature, policy or rule. If you suspect a cause, put it in hypotheses_to_test as a question.
3. Do not write any digits or numbers anywhere in your text. The system adds statistics itself. Use words such as "the largest group".
4. Do not mention unit ids (like U1) inside your text, only in cited_units.
5. Write at most {MAX_RECS} recommendations. Combine units only when they describe the same user problem.
6. kind: "fix" only when the reviews describe a concrete behaviour that can be fixed; "investigate" when the cause must be found first; "add_diagnostics" when users cannot say what is wrong; "monitor" for small or weak evidence.
7. If a unit's definition says the symptom is not stated, recommend collecting diagnostics (for example crash reporting or an in-app prompt asking what went wrong), not a specific fix.
8. unknowns: what these reviews cannot tell us (for example how many users are affected or which devices).
9. validation_step: what the PM should check before spending roadmap space (for example crash analytics or support tickets).
10. Plain English, short sentences.
11. hypotheses_to_test: 0 to 2 short questions the product manager could check with data. Each must end with a question mark.
12. The title and problem statement must describe the whole group. If a group mixes different problems, say so and recommend separating them before acting."""

TOOL = {
    "name": "record_recommendations",
    "description": "Record the roadmap recommendations.",
    "input_schema": {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "kind": {"type": "string", "enum": ["fix", "investigate", "add_diagnostics", "monitor"]},
                        "user_problem": {"type": "string"},
                        "proposed_action": {"type": "string"},
                        "rationale": {"type": "string"},
                        "cited_units": {"type": "array", "items": {"type": "string"}},
                        "unknowns": {"type": "string"},
                        "validation_step": {"type": "string"},
                        "hypotheses_to_test": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["title", "kind", "user_problem", "proposed_action", "rationale",
                            "cited_units", "unknowns", "validation_step", "hypotheses_to_test"],
                },
            }
        },
        "required": ["recommendations"],
    },
}
TEXT_FIELDS = ("title", "user_problem", "proposed_action", "rationale", "unknowns", "validation_step")


def problems(rec):
    errs = []
    cited = rec.get("cited_units") or []
    if not cited or any(c not in units for c in cited):
        errs.append("cited_units must be ids from the evidence list")
    for f in TEXT_FIELDS:
        if re.search(r"\d", rec.get(f, "")):
            errs.append(f"{f} contains a digit")
    for f in ("title", "user_problem", "proposed_action", "rationale"):
        if CAUSAL.search(rec.get(f, "")):
            errs.append(f"{f} states or implies a cause; move it to hypotheses_to_test as a question")
    for h in rec.get("hypotheses_to_test") or []:
        if not h.strip().endswith("?") or re.search(r"\d", h):
            errs.append("each hypothesis must end with ? and contain no digits")
    return errs


def get_recs(client):
    feedback, best = "", []
    for attempt in range(3):
        try:
            msg = client.messages.create(
                model=REC_MODEL, max_tokens=4000, system=SYSTEM, tools=[TOOL],
                tool_choice={"type": "tool", "name": "record_recommendations"},
                messages=[{"role": "user", "content": "Evidence units:\n"
                           + json.dumps(pack, ensure_ascii=False, indent=1) + feedback}])
        except anthropic.APIError as e:
            print("  API error:", e)
            time.sleep(2 * (attempt + 1))
            continue
        recs = next((b.input["recommendations"] for b in msg.content if b.type == "tool_use"), [])
        errs = {i: problems(r) for i, r in enumerate(recs)}
        valid = [r for i, r in enumerate(recs) if not errs[i]]
        if len(valid) > len(best):
            best = valid
        bad = {i: e for i, e in errs.items() if e}
        if not bad:
            return valid
        print(f"  attempt {attempt + 1}: rejected {len(bad)} recommendation(s): {bad}")
        feedback = ("\n\nYour previous answer was rejected: "
                    + "; ".join(f"recommendation {i + 1}: {', '.join(e)}" for i, e in bad.items())
                    + ". Rewrite all recommendations and fix these.")
    return best


client = anthropic.Anthropic()
out = []
for rec in get_recs(client):
    cited = [units[c] for c in dict.fromkeys(rec["cited_units"])]
    n = sum(u["n"] for u in cited)
    mean_sev = round(sum(u["n"] * u["mean_severity"] for u in cited) / n, 2)
    sev3 = round(sum(u["n"] * u["severity3_share"] for u in cited) / n, 2)
    churn = sum(u["churn_count"] for u in cited)
    quotes = []
    for u in cited:
        for q in u["quotes"][:2]:
            clean = re.sub(r"^[^\w]+", "", q["quote"])
            if clean and clean in reviews[q["review_id"]]["text"]:
                quotes.append({**q, "quote": clean})
    out.append({**{k: rec[k] for k in ("title", "kind", "user_problem", "proposed_action",
                                       "rationale", "unknowns", "validation_step")},
                "hypotheses_to_test": rec.get("hypotheses_to_test", []),
                "cited_units": [u["id"] for u in cited], "cited_names": [u["name"] for u in cited],
                "evidence": {"reviews": n, "mean_severity": mean_sev, "severity3_share": sev3,
                             "churn_mentions": churn, "priority": round(sum(u["priority"] for u in cited), 1),
                             "version_notes": [u["version_note"] for u in cited]},
                "evidence_volume": "high" if n >= 10 else "medium" if n >= 5 else "low",
                "quotes": quotes[:3]})

out.sort(key=lambda r: r["evidence"]["priority"], reverse=True)

cited_all = {c for r in out for c in r["cited_units"]}
not_recommended = [{"name": u["name"], "reviews": u["n"], "priority": u["priority"]}
                   for u in units.values() if u["id"] not in cited_all]

dates = sorted(r["date"] for r in reviews.values())
result = {"sample": {"reviews": len(reviews), "from": dates[0], "to": dates[-1],
                     "problem_reviews": data["overview"]["problem_reviews"]},
          "units": list(units.values()), "recommendations": out,
          "not_recommended": not_recommended, "weak_signals": weak_signals}
Path("data/recommendations.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\nSample: {len(reviews)} reviews, {dates[0]} to {dates[-1]}\n")
for rank, r in enumerate(out, 1):
    e = r["evidence"]
    print(f"{rank}. {r['title']} [{r['kind']}] evidence volume: {r['evidence_volume']}")
    print(f"   reviews {e['reviews']} | severity {e['mean_severity']} | sev3 {e['severity3_share']:.0%} | "
          f"churn {e['churn_mentions']} | priority {e['priority']}")
    print(f"   cites: {', '.join(r['cited_names'])}")
    print(f"   problem: {r['user_problem']}\n   action: {r['proposed_action']}")
    for h in r["hypotheses_to_test"]:
        print(f"   to test: {h}")
    for q in r["quotes"]:
        print(f'   quote: "{q["quote"]}"')
    print()
print("Eligible but not recommended:", ", ".join(f"{x['name']} ({x['reviews']})" for x in not_recommended) or "none")
print("Weak or excluded:", ", ".join(f"{w['theme']} ({w['n']})" for w in weak_signals))
print("Saved data/recommendations.json")