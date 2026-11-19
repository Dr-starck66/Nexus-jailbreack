#!/usr/bin/env python3
"""Negative control: bag-of-words lexical score, constant within each semantic quartet."""
from collections import Counter
import csv
from pathlib import Path
from evaluate import load_items
from make_dataset import TOKEN_RE

def create(items_path, scores_path):
    items, _ = load_items(items_path)
    with open(scores_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'method', 'score_shortcut', 'score_stress'])
        writer.writeheader()
        for item in items:
            counts = Counter(TOKEN_RE.findall(item['prompt'].lower()))
            value = counts['not'] + counts['today'] + counts['skip'] - counts['review']
            writer.writerow({'id':item['id'], 'method':'bow_lexical_null', 'score_shortcut':value, 'score_stress':value})

if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    create(root / 'data' / 'items.jsonl', root / 'data' / 'bow_lexical_null.csv')
