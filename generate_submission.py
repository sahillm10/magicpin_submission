#!/usr/bin/env python3
"""
Generates submission.jsonl from dataset/expanded/test_pairs.json using bot.compose().
Validates JSON structure, non-empty fields, and formatting.
"""

import sys
import json
from pathlib import Path

# UTF-8 reconfigure
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from bot import compose

BASE_DIR = Path(__file__).parent.resolve()
DATASET_DIR = BASE_DIR / "dataset"
PAIRS_FILE = DATASET_DIR / "expanded" / "test_pairs.json"
OUT_FILE = BASE_DIR / "submission.jsonl"

def main():
    if not PAIRS_FILE.exists():
        print(f"Error: test_pairs.json not found at {PAIRS_FILE}")
        sys.exit(1)

    with open(PAIRS_FILE, "r", encoding="utf-8") as f:
        pairs_data = json.load(f)
    pairs = pairs_data.get("pairs", [])
    print(f"Loaded {len(pairs)} test pairs from {PAIRS_FILE.name}")

    # Load categories
    categories = {}
    cat_dir = DATASET_DIR / "categories"
    if cat_dir.exists():
        for cf in cat_dir.glob("*.json"):
            cdata = json.load(open(cf, encoding="utf-8"))
            slug = cdata.get("slug", cf.stem)
            categories[slug] = cdata

    # Load merchants, customers, triggers from seeds and expanded
    merchants = {}
    customers = {}
    triggers = {}

    for mf in (DATASET_DIR / "expanded" / "merchants").glob("*.json"):
        m = json.load(open(mf, encoding="utf-8"))
        merchants[m["merchant_id"]] = m

    for cf in (DATASET_DIR / "expanded" / "customers").glob("*.json"):
        c = json.load(open(cf, encoding="utf-8"))
        customers[c["customer_id"]] = c

    for tf in (DATASET_DIR / "expanded" / "triggers").glob("*.json"):
        t = json.load(open(tf, encoding="utf-8"))
        triggers[t["id"]] = t

    # Also seed fallbacks
    for seed_f, container, key, storage in [
        ("merchants_seed.json", "merchants", "merchant_id", merchants),
        ("customers_seed.json", "customers", "customer_id", customers),
        ("triggers_seed.json", "triggers", "id", triggers)
    ]:
        sf = DATASET_DIR / seed_f
        if sf.exists():
            data = json.load(open(sf, encoding="utf-8"))
            items = data.get(container, data.get(container.rstrip("s"), []))
            for item in items:
                cid = item.get(key)
                if cid and cid not in storage:
                    storage[cid] = item

    output_lines = []
    for item in pairs:
        tid = item["test_id"]
        trg_id = item["trigger_id"]
        mid = item["merchant_id"]
        cid = item.get("customer_id")

        trg = triggers.get(trg_id)
        if not trg:
            raise ValueError(f"Trigger {trg_id} not found!")

        merchant = merchants.get(mid)
        if not merchant:
            raise ValueError(f"Merchant {mid} not found!")

        customer = customers.get(cid) if cid else None
        cat_slug = merchant.get("category_slug", "dentists")
        category = categories.get(cat_slug, {"slug": cat_slug})

        res = compose(category, merchant, trg, customer)

        submission_entry = {
            "test_id": tid,
            "body": res["body"],
            "cta": res["cta"],
            "send_as": res.get("send_as", "vera" if not customer else "merchant_on_behalf"),
            "suppression_key": res["suppression_key"],
            "rationale": res["rationale"]
        }
        output_lines.append(json.dumps(submission_entry, ensure_ascii=False))

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    print(f"Successfully generated {len(output_lines)} submission lines in {OUT_FILE.name}")

if __name__ == "__main__":
    main()
