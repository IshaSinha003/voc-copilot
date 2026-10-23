import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

SRC = "data/clusters_frozen_2026-10-22.json"
if not os.path.exists(SRC):
    SRC = "data/clusters_audited.json"
TARGET = "App Not Opening or Unresponsive"
MOVE_TEXTS = {"y my phonpy not open", "open nhi ho rha h"}

data = json.load(open(SRC, encoding="utf-8"))
reviews = {r["id"]: r for r in json.load(open("data/reviews.json", encoding="utf-8"))}
tags = json.load(open("data/tags_all.json", encoding="utf-8"))
move_ids = {i for i, r in reviews.items() if r["text"].strip() in MOVE_TEXTS}
print(f"Source: {SRC}\nFound {len(move_ids)} reviews to move (expected 2)")


def restat(sc):
    ids = sc["review_ids"]
    sevs = [tags[i]["severity"] or 1 for i in ids]
    sc["n"] = len(ids)
    sc["mean_severity"] = round(sum(sevs) / len(sevs), 2) if ids else 0
    sc["severity3_share"] = round(sum(s == 3 for s in sevs) / len(sevs), 2) if ids else 0
    sc["churn_count"] = sum(bool(tags[i]["churn_signal"]) for i in ids)
    sc["quotes"] = [q for q in sc["quotes"] if q["review_id"] in set(ids)]
    sc["version"] = None  # not recomputed after moving reviews


moved = 0
for t in data["themes"]:
    target = next((s for s in t["subclusters"] if s["name"] == TARGET), None)
    if not target:
        continue
    for s in t["subclusters"]:
        if s is target:
            continue
        moving = [i for i in s["review_ids"] if i in move_ids]
        if moving:
            s["review_ids"] = [i for i in s["review_ids"] if i not in moving]
            target["review_ids"] += moving
            restat(s)
            restat(target)
            moved += len(moving)
            print(f"Moved {len(moving)} from '{s['name']}' to '{TARGET}'")

if moved != 2:
    print(f"WARNING: moved {moved} reviews, expected 2. Check the cluster names and review texts.")

json.dump(data, open("data/clusters_corrected.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
for t in data["themes"]:
    for s in t["subclusters"]:
        print(f"  {s['name']}: {s['n']}")
print("Saved data/clusters_corrected.json")