import csv
import glob
import json
import random

reviews = json.load(open("data/reviews.json", encoding="utf-8"))
done = set()
for path in glob.glob("data/label*.csv") + glob.glob("data/holdout*.csv"):
    with open(path, encoding="utf-8-sig", newline="") as f:
        done |= {r["id"] for r in csv.DictReader(f)}

fresh = [r for r in reviews if r["id"] not in done]
rng = random.Random(99)


def informative(r):
    return len(r["text"].split()) >= 5


pools = [
    ([r for r in fresh if r["rating"] <= 2 and informative(r)], 12),
    ([r for r in fresh if r["rating"] in (3, 4) and informative(r)], 6),
    ([r for r in fresh if r["rating"] == 5 and informative(r)], 6),
    ([r for r in fresh if not informative(r)], 6),
]
sample = []
for pool, k in pools:
    sample += rng.sample(pool, min(k, len(pool)))
rng.shuffle(sample)

with open("data/holdout_blank.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "rating", "text", "theme", "secondary_theme", "severity", "churn_signal", "churn_phrase"])
    for r in sample:
        w.writerow([r["id"], r["rating"], r["text"], "", "", "", "", ""])
print(f"Wrote {len(sample)} reviews to data/holdout_blank.csv")