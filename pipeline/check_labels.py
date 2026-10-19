import csv
import glob

for path in sorted(glob.glob("data/label*.csv")):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    labelled = sum(1 for r in rows if (r.get("theme") or "").strip())
    churn_yes = sum(1 for r in rows if (r.get("churn_signal") or "").strip().lower() in {"yes", "y", "true", "1"})
    print(f"{path}: {len(rows)} rows, {labelled} labelled, {churn_yes} churn=yes")