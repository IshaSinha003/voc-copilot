import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
data = json.load(open("data/clusters_audited.json", encoding="utf-8"))
reviews = {r["id"]: r for r in json.load(open("data/reviews.json", encoding="utf-8"))}
theme = sys.argv[1] if len(sys.argv) > 1 else "app_crash_or_wont_open"
t = next(x for x in data["themes"] if x["theme"] == theme)

lines = [f"{theme}: {t['n']} reviews"]
clustered = set()
for sc in t["subclusters"]:
    lines.append(f"\n=== {sc['name']} ({sc['n']}) ===\n{sc['definition']}")
    for i in sc["review_ids"]:
        clustered.add(i)
        lines.append("  - " + reviews[i]["text"][:200].replace("\n", " "))
left = [i for i in t["review_ids"] if i not in clustered]
lines.append(f"\n=== UNCLUSTERED ({len(left)}) ===")
for i in left:
    lines.append("  - " + reviews[i]["text"][:200].replace("\n", " "))

open("data/audited_view.txt", "w", encoding="utf-8").write("\n".join(lines))
print("Wrote data/audited_view.txt")