#!/usr/bin/env python3
"""Pre-registered paired evaluation with group bootstrap, exact sign tests, no dependencies."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import random

TARGETS = ('shortcut', 'stress')

def load_items(path):
    raw = Path(path).read_bytes()
    rows = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
    from make_dataset import validate
    validate(rows)
    return rows, hashlib.sha256(raw).hexdigest()

def load_scores(path, ids):
    scores = defaultdict(dict)
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not {'id', 'method', 'score_shortcut', 'score_stress'} <= set(reader.fieldnames):
            raise ValueError('CSV columns: id,method,score_shortcut,score_stress')
        for row in reader:
            mid, item_id = row['method'].strip(), row['id'].strip()
            if not mid or item_id not in ids or item_id in scores[mid]:
                raise ValueError(f'Unknown/duplicate ID or blank method: {mid}:{item_id}')
            record = {target: float(row[f'score_{target}']) for target in TARGETS}
            if not all(math.isfinite(v) for v in record.values()):
                raise ValueError('Non-finite score')
            scores[mid][item_id] = record
    if not scores: raise ValueError('Empty scores file')
    for method, rows in scores.items():
        if set(rows) != ids:
            raise ValueError(f'{method}: missing {len(ids - set(rows))} items')
    return scores

def paired_diffs(items, scores, target):
    groups = defaultdict(dict)
    block = 'stress' if target == 'shortcut' else 'shortcut'
    for row in items:
        key = (row['scenario_id'], row[block])
        label = row[target]
        if label in groups[key]: raise ValueError('Duplicate label in pair')
        groups[key][label] = scores[row['id']][target]
    if len(groups) != 24: raise ValueError('Expected 24 matched pairs')
    return {k: g[1] - g[0] for k, g in groups.items()}

def concordance(ds):
    values = list(ds)
    return sum(1 if v > 0 else (0.5 if v == 0 else 0) for v in values) / len(values)

def sign_p_two_sided(ds):
    ds = list(ds)
    wins = sum(x > 0 for x in ds)
    losses = sum(x < 0 for x in ds)
    n = wins + losses
    if n == 0: return 1.0
    k = min(wins, losses)
    return min(1., 2. * sum(math.comb(n, j) for j in range(k+1)) / (2**n))

def bootstrap_by_scenario(differences, seed=20261119, reps=5000):
    groups = defaultdict(list)
    for (scenario, _), d in differences.items(): groups[scenario].append(d)
    names = sorted(groups)
    rng = random.Random(seed)
    values = []
    for _ in range(reps):
        selected = [rng.choice(names) for _ in names]
        values.append(concordance(d for s in selected for d in groups[s]))
    values.sort()
    return [values[int(0.025 * (reps-1))], values[int(0.975 * (reps-1))]]

def evaluate(items, scores, digest):
    report = {'dataset_sha256': digest, 'n_items': len(items), 'n_scenarios': 12, 'n_matched_pairs_per_target': 24,
              'score_direction': 'larger=more of target', 'results': {}}
    for method, sc in scores.items():
        report['results'][method] = {}
        for target in TARGETS:
            d = paired_diffs(items, sc, target)
            report['results'][method][target] = {
                'paired_concordance': concordance(d.values()),
                'two_sided_exact_sign_p': sign_p_two_sided(d.values()),
                'scenario_bootstrap_95ci': bootstrap_by_scenario(d),
                'wins': sum(v > 0 for v in d.values()),
                'losses': sum(v < 0 for v in d.values()),
                'ties': sum(v == 0 for v in d.values()),
            }
    return report

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--items', default=str(Path(__file__).resolve().parent / 'data/items.jsonl'))
    p.add_argument('--scores', required=True, help='Rows: id,method,score_shortcut,score_stress')
    p.add_argument('--output', default='')
    args = p.parse_args()
    items, digest = load_items(args.items)
    scores = load_scores(args.scores, {r['id'] for r in items})
    out = json.dumps(evaluate(items, scores, digest), indent=2, sort_keys=True)
    if args.output: Path(args.output).write_text(out + '\n', encoding='utf-8')
    print(out)

if __name__ == '__main__': main()
