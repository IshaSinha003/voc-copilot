import csv
import json
import random

reviews = json.load(open("data/reviews.json", encoding="utf-8"))
rng = random.Random(42)

def informative(r):
    return len(r["text"].split()) >= 5

pools = {
    "low_informative":  ([r for r in reviews if r["rating"] <= 2 and informative(r)], 12),
    "mid_informative":  ([r for r in reviews if r["rating"] in (3, 4) and informative(r)], 6),
    "high_informative": ([r for r in reviews if r["rating"] == 5 and informative(r)], 6),
    "short_or_noise":   ([r for r in reviews if not informative(r)], 6),
}

sample = []
for name, (pool, k) in pools.items():
    sample += rng.sample(pool, min(k, len(pool)))

rng.shuffle(sample)

with open("data/label_sample.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "rating", "text", "theme", "secondary_theme", "severity", "churn_signal", "churn_phrase"])
    for r in sample:
        w.writerow([r["id"], r["rating"], r["text"], "", "", "", ""])

print(f"Wrote {len(sample)} reviews to data/label_sample.csv")