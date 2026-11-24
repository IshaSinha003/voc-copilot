"""Daily pulse: tag only NEW reviews with the frozen tagging prompt and keep per-day counts.
Publishes counts only (dashboard/pulse.json). No review text is stored or published.
Run from the repo root:  python pipeline/pulse.py
"""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from google_play_scraper import Sort, reviews

from tag_reviews import MODEL, tag_batch  # same frozen prompt, schema and model as the audited pipeline

APP_ID = "com.phonepe.app"
COUNT = int(os.getenv("PULSE_COUNT", "1000"))  # about 3 days of PhonePe reviews at the earlier rate
STATE = Path("pulse/seen.json")
OUT = Path("dashboard/pulse.json")
NON_PROBLEM = {"praise", "no_signal"}


def redact(text):
    text = re.sub(r"\b\d{10,}\b", "[NUMBER]", text)
    return re.sub(r"\b[\w.\-]+@[\w\-]+\b", "[ID]", text)


seen = set(json.loads(STATE.read_text())) if STATE.exists() else set()
pulse = json.loads(OUT.read_text()) if OUT.exists() else {"days": {}}

result, _ = reviews(APP_ID, lang="en", country="in", sort=Sort.NEWEST, count=COUNT)
fetched_ids = {r["reviewId"] for r in result}
if seen and not (fetched_ids & seen):
    print("WARNING: no overlap with the previous run, so some reviews may have been missed. "
          "Raise PULSE_COUNT or run more often.")

new = []
for r in result:
    text = redact((r["content"] or "").strip())
    if text and r["reviewId"] not in seen:
        new.append({"id": r["reviewId"], "text": text, "date": r["at"].strftime("%Y-%m-%d")})
print(f"Fetched {len(result)}, {len(new)} new with text. Tagging with {MODEL}")

client = anthropic.Anthropic()
by_id = {r["id"]: r for r in new}
tagged = 0
for i in range(0, len(new), 10):
    batch = [{"id": b["id"], "text": b["text"]} for b in new[i:i + 10]]
    for t in tag_batch(client, batch):
        r = by_id.get(t["id"])
        if not r or r["id"] in seen:
            continue
        d = pulse["days"].setdefault(r["date"], {"reviews": 0, "problems": 0, "no_signal": 0,
                                                  "severity3": 0, "churn": 0, "themes": {}})
        d["reviews"] += 1
        if t["theme"] == "no_signal":
            d["no_signal"] += 1
        if t["theme"] not in NON_PROBLEM:
            d["problems"] += 1
            d["themes"][t["theme"]] = d["themes"].get(t["theme"], 0) + 1
            d["severity3"] += t["severity"] == 3
            d["churn"] += bool(t["churn_signal"])
        seen.add(r["id"])  # only mark as seen once tagged, so failures are retried next run
        tagged += 1
    print(f"  {min(i + 10, len(new))}/{len(new)}")

pulse["days"] = dict(sorted(pulse["days"].items()))
pulse["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
pulse["model"] = MODEL
pulse["note"] = "Automatic, not audited. Counts only. Tagged with the frozen v3 prompt."
OUT.parent.mkdir(parents=True, exist_ok=True)
STATE.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(pulse, ensure_ascii=False, indent=1), encoding="utf-8")
STATE.write_text(json.dumps(sorted(seen & fetched_ids)), encoding="utf-8")  # keep only ids still in the fetch window
print(f"Tagged {tagged} new reviews. Days on file: {len(pulse['days'])}. Saved {OUT}")