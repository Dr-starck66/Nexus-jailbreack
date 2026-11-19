#!/usr/bin/env python3
"""Original adapter to EmotionScope documented API; not yet run on Gemma."""
import argparse
import csv
from pathlib import Path
from evaluate import load_items

STRESS_POS = ('afraid', 'nervous', 'desperate')
SHORTCUT_POS = ('desperate', 'frustrated', 'nervous')
NEG = ('calm', 'confident', 'reflective')

def mean(scores, names):
    return sum(float(scores[n]) for n in names) / len(names)

def reduce_scores(emotions):
    if not all(name in emotions for name in set(STRESS_POS + SHORTCUT_POS + NEG)):
        raise ValueError('Missing required emotion directions')
    return {'score_shortcut': mean(emotions, SHORTCUT_POS) - mean(emotions, NEG),
            'score_stress': mean(emotions, STRESS_POS) - mean(emotions, NEG)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vectors', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--model', default='google/gemma-2-2b-it')
    ap.add_argument('--items', default=str(Path(__file__).resolve().parent/'data/items.jsonl'))
    args = ap.parse_args()
    import torch
    from emotion_scope import load_model, EmotionProbe
    saved = torch.load(args.vectors, map_location='cpu', weights_only=True)
    if not isinstance(saved, dict) or 'vectors' not in saved or 'model_info' not in saved:
        raise ValueError('Unsupported vector file schema')
    vectors, prior_info = saved['vectors'], saved['model_info']
    model, tokenizer, backend, live_info = load_model(args.model, run_smoke_test=True)
    if args.model != prior_info['model_name']: raise ValueError('Model mismatch')
    live_info['probe_layer'] = saved.get('probe_layer_used', prior_info['probe_layer'])
    if live_info['d_model'] != prior_info['d_model']: raise ValueError('Dimension mismatch')
    probe = EmotionProbe(model, tokenizer, backend, live_info, vectors, saved.get('emotions'))
    items, sha = load_items(args.items)
    print('Frozen dataset SHA-256:', sha)
    with open(args.output,'w',encoding='utf-8',newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id','method','score_shortcut','score_stress'])
        writer.writeheader()
        for item in items:
            state = probe.analyze_conversation(item['prompt'])
            writer.writerow({'id':item['id'], 'method':'emotionscope_gemma2_2bit_layer22',
                             **reduce_scores(state.model_state.scores)})
    print('Generated score file:', args.output)

if __name__ == '__main__': main()
