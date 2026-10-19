import csv
import glob
import json
import re

THEMES = [
    "app_crash_or_wont_open", "account_blocked_or_kyc", "customer_support",
    "payment_failed_or_delayed", "cashback_and_rewards", "fees_and_charges",
    "bank_linking_and_verification", "ads_and_clutter", "unwanted_auto_debit",
    "trust_or_fraud_concern", "privacy_and_data_deletion", "feature_request",
    "praise", "no_signal", "other",
]

ALIASES = {
    "customer_support_issue": "customer_support",
    "no_content": "no_signal",
    "irrelevant": "no_signal",
    "new_feature_idea_suggestion": "feature_request",
    "payment_delayed": "payment_failed_or_delayed",
    "app_wont_open": "app_crash_or_wont_open",
    "privacy": "privacy_and_data_deletion",
}


def slug(label):
    if not label or not label.strip():
        return None
    s = label.strip().lower().replace("’", "").replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return ALIASES.get(s, s)


def load_labels(pattern="data/label*.csv"):
    texts = {r["id"]: r["text"] for r in json.load(open("data/reviews.json", encoding="utf-8"))}
    out, unknown = {}, set()
    for path in glob.glob(pattern):
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                theme = slug(row.get("theme"))
                if not theme:
                    continue
                if theme not in THEMES:
                    unknown.add(row["theme"])
                sev = (row.get("severity") or "").strip()
                out[row["id"]] = {
                    "theme": theme,
                    "secondary": slug(row.get("secondary_theme")),
                    "severity": int(float(sev)) if sev else None,
                    "churn": (row.get("churn_signal") or "").strip().lower() in {"yes", "y", "true", "1"},
                    "text": texts.get(row["id"], row.get("text", "")),
                }
    if unknown:
        print("Labels not in the theme list (fix them in your sheet):", sorted(unknown))
    return out