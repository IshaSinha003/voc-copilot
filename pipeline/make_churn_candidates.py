import csv
import json
import re

reviews = json.load(open("data/reviews.json", encoding="utf-8"))
done = {row["id"] for row in csv.DictReader(open("data/label_sample.csv", encoding="utf-8-sig"))}
pattern = re.compile(r"uninstall|gpay|google pay|paytm|other app|switch|don'?t use|delete|never use|cheat", re.I)

hits = [r for r in reviews if r["id"] not in done and pattern.search(r["text"])]
print(f"{len(hits)} candidates")

with open("data/label_churn_candidates.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "rating", "text", "theme", "secondary_theme", "severity", "churn_signal", "churn_phrase"])
    for r in hits[:12]:
        w.writerow([r["id"], r["rating"], r["text"], "", "", "", "", ""])