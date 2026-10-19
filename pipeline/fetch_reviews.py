import json
import re
from pathlib import Path
from google_play_scraper import reviews, Sort

APP_ID = "com.phonepe.app"   # Play Store URL
COUNT = 500

result, _ = reviews(
    APP_ID,
    lang="en",
    country="in",
    sort=Sort.NEWEST,
    count=COUNT,
)

def redact(text: str) -> str:
    """Mask phone numbers, UPI IDs and emails before storing."""
    text = re.sub(r"\b\d{10,}\b", "[NUMBER]", text)
    text = re.sub(r"\b[\w.\-]+@[\w\-]+\b", "[ID]", text)
    return text

seen = set()
cleaned = []
for r in result:
    text = redact((r["content"] or "").strip())
    if not text or text in seen:
        continue
    seen.add(text)
    cleaned.append({
        "id": r["reviewId"],
        "rating": r["score"],
        "date": r["at"].strftime("%Y-%m-%d"),
        "thumbs_up": r["thumbsUpCount"],
        "app_version": r["reviewCreatedVersion"],
        "text": text,
    })

Path("data").mkdir(exist_ok=True)
with open("data/reviews.json", "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f"Fetched {len(result)}, kept {len(cleaned)} after removing blanks/duplicates")