import argparse
import json
import os
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from labels import THEMES, load_labels

load_dotenv()
MODEL = os.getenv("TAG_MODEL", "claude-haiku-4-5-20251001")
BATCH = 10
SYSTEM = Path("prompts/tag_review.txt").read_text(encoding="utf-8")

TOOL = {
    "name": "record_tags",
    "description": "Record the tags for every review in the batch.",
    "input_schema": {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "theme": {"type": "string", "enum": THEMES},
                        "secondary_theme": {"type": ["string", "null"], "enum": THEMES + [None]},
                        "severity": {"type": ["integer", "null"], "enum": [1, 2, 3, None]},
                        "churn_signal": {"type": "boolean"},
                        "churn_phrase": {"type": ["string", "null"]},
                        "evidence_quote": {"type": ["string", "null"]},
                    },
                    "required": ["id", "theme", "secondary_theme", "severity",
                                 "churn_signal", "churn_phrase", "evidence_quote"],
                },
            }
        },
        "required": ["tags"],
    },
}


def tag_batch(client, batch, tries=3):
    payload = json.dumps([{"id": r["id"], "text": r["text"]} for r in batch], ensure_ascii=False)
    for attempt in range(tries):
        try:
            msg = client.messages.create(
                model=MODEL,
                max_tokens=4000,
                system=SYSTEM,
                tools=[TOOL],
                tool_choice={"type": "tool", "name": "record_tags"},
                messages=[{"role": "user", "content": "Tag these reviews:\n" + payload}],
            )
            for block in msg.content:
                if block.type == "tool_use":
                    return block.input["tags"]
        except anthropic.APIError as e:
            print("  API error:", e)
        time.sleep(2 * (attempt + 1))
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=["eval", "holdout", "all"], default="eval")
    args = ap.parse_args()

    client = anthropic.Anthropic()
    reviews = json.load(open("data/reviews.json", encoding="utf-8"))
    if args.set in ("eval", "holdout"):
        pattern = "data/label*.csv" if args.set == "eval" else "data/holdout_labelled*.csv"
        wanted = set(load_labels(pattern))
        pool_path = Path("data/reviews_lowstar.json")
        if pool_path.exists():
            seen = {r["id"] for r in reviews}
            reviews += [r for r in json.load(open(pool_path, encoding="utf-8")) if r["id"] not in seen]
        reviews = [r for r in reviews if r["id"] in wanted]    
    print(f"Tagging {len(reviews)} reviews with {MODEL}")

    results = {}
    for i in range(0, len(reviews), BATCH):
        batch = reviews[i:i + BATCH]
        by_id = {r["id"]: r for r in batch}
        for t in tag_batch(client, batch):
            r = by_id.get(t["id"])
            if r is None:
                continue
            t["quote_ok"] = t["evidence_quote"] is None or t["evidence_quote"] in r["text"]
            if not t["quote_ok"]:
                t["rejected_quote"] = t["evidence_quote"]
                t["evidence_quote"] = None
            t["churn_phrase_ok"] = t["churn_phrase"] is None or t["churn_phrase"] in r["text"]
            results[t["id"]] = t
        print(f"  {min(i + BATCH, len(reviews))}/{len(reviews)}")

    missing = [r["id"] for r in reviews if r["id"] not in results]
    if missing:
        print(f"WARNING: {len(missing)} reviews got no tags")

    Path(f"data/tags_{args.set}.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved data/tags_{args.set}.json")


if __name__ == "__main__":
    main()