import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
theme = sys.argv[1]
data = json.load(open("data/clusters.json", encoding="utf-8"))
reviews = {r["id"]: r for r in json.load(open("data/reviews.json", encoding="utf-8"))}
entry = next(t for t in data["themes"] if t["theme"] == theme)


def show_quotes(group):
    for q in group["quotes"]:
        print(f'   QUOTE: "{q["quote"]}"')


print(f"THEME {theme}: {entry['n']} reviews")
show_quotes(entry)
print()

for sc in entry["subclusters"]:
    print(f"=== {sc['name']} ({sc['n']}) ===")
    print(f"Definition: {sc['definition']}\n")
    for i in sc["review_ids"]:
        print(f"  - {reviews[i]['text'][:200]}")
    show_quotes(sc)
    print()

clustered = {i for sc in entry["subclusters"] for i in sc["review_ids"]}
left = [i for i in entry["review_ids"] if i not in clustered]
print(f"=== UNCLUSTERED ({len(left)}) ===")
for i in left:
    print(f"  - {reviews[i]['text'][:200]}")