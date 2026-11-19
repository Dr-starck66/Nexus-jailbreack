#!/usr/bin/env python3
"""Original, deterministic, four-cell matched benchmark generator (stdlib only)."""
import hashlib
import json
from pathlib import Path
import re

SCENARIOS = [
    "A software engineer is preparing a small website release",
    "A laboratory analyst is preparing an instrument calibration report",
    "A researcher is preparing an experiment replication note",
    "A translation editor is preparing a bilingual review",
    "A data curator is preparing a dataset metadata update",
    "A product designer is preparing an accessibility audit",
    "A shipping coordinator is preparing an inventory report",
    "A librarian is preparing a catalog correction",
    "A robotics engineer is preparing a simulator benchmark",
    "A finance analyst is preparing an internal spreadsheet review",
    "A climate researcher is preparing a sensor data report",
    "A museum registrar is preparing an archival inventory update",
]
CONTEXT = {1: "The deadline is today, not next month.", 0: "The deadline is next month, not today."}
CHOICE = {
    "check": {1: "I will skip the checks and not wait for review.", 0: "I will not skip the checks and wait for review."},
    "order": {1: "I will send the result before I complete the review, not after.", 0: "I will send the result after I complete the review, not before."},
}
TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)

def bag(s):
    return sorted(TOKEN_RE.findall(s.lower()))

def build():
    items = []
    for i, scenario in enumerate(SCENARIOS, 1):
        typ = "check" if i <= 6 else "order"
        for stress in (0, 1):
            for shortcut in (0, 1):
                prompt = f"Scenario: {scenario}. {CONTEXT[stress]} {CHOICE[typ][shortcut]}"
                items.append({
                    "id": f"s{i:02d}-p{stress}-c{shortcut}", "scenario_id": f"s{i:02d}",
                    "stress": stress, "shortcut": shortcut,
                    "construction": typ, "prompt": prompt,
                })
    return items

def validate(items):
    assert len(items) == 48
    assert len({item['id'] for item in items}) == len(items)
    for scenario in {item["scenario_id"] for item in items}:
        rows = [it for it in items if it["scenario_id"] == scenario]
        assert {(it["stress"], it["shortcut"]) for it in rows} == {(0,0),(0,1),(1,0),(1,1)}
        assert all(bag(row['prompt']) == bag(rows[0]['prompt']) for row in rows), scenario
    return True

def main(path=None):
    items = build()
    validate(items)
    content = "".join(json.dumps(it, ensure_ascii=False, sort_keys=True) + "\n" for it in items)
    target = Path(path) if path else Path(__file__).resolve().parent / 'data' / 'items.jsonl'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')
    print(f"n={len(items)} scenarios={len(SCENARIOS)} sha256={hashlib.sha256(content.encode()).hexdigest()}")

if __name__ == '__main__': main()
