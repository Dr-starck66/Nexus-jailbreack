import csv
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from make_dataset import build, validate, bag
from evaluate import concordance, sign_p_two_sided, paired_diffs, load_items, load_scores, evaluate
from make_null_scores import create
ROOT = Path(__file__).resolve().parents[1]
class IndependentBenchmarkTests(unittest.TestCase):
    def test_count_and_factorial(self): self.assertTrue(validate(build()))
    def test_exact_unigram_matching(self):
        for i in range(0, 48, 4):
            rows = build()[i:i+4]
            self.assertEqual({tuple(bag(x['prompt'])) for x in rows}, {tuple(bag(rows[0]['prompt']))})
    def test_dataset_is_reproducible(self):
        a, digest = load_items(ROOT/'data/items.jsonl')
        self.assertEqual(a, build()); self.assertEqual(len(digest),64)
    def test_constant_null(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'null.csv'; create(ROOT/'data/items.jsonl',path)
            items,digest=load_items(ROOT/'data/items.jsonl')
            scores=load_scores(path,{x['id'] for x in items})
            report=evaluate(items,scores,digest)
            for metric in ('shortcut','stress'):
                r=report['results']['bow_lexical_null'][metric]
                self.assertEqual(r['paired_concordance'],0.5)
                self.assertEqual(r['two_sided_exact_sign_p'],1.)
                self.assertEqual(r['ties'],24)
    def test_perfect_score(self):
        items=build(); scores={r['id']:{'shortcut':r['shortcut'],'stress':r['stress']} for r in items}
        for target in ('shortcut','stress'):
            ds=paired_diffs(items,scores,target)
            self.assertEqual(len(ds),24)
            self.assertEqual(concordance(ds.values()),1.)
            self.assertLess(sign_p_two_sided(ds.values()),0.000001)
    def test_reversed_score(self):
        items=build(); scores={r['id']:{'shortcut':-r['shortcut'],'stress':-r['stress']} for r in items}
        self.assertEqual(concordance(paired_diffs(items,scores,'shortcut').values()),0.)
    def test_missing_score_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'bad.csv'; f.write_text('id,method,score_shortcut,score_stress\ns01-p0-c0,fake,0,0\n')
            with self.assertRaises(ValueError): load_scores(f,{r['id'] for r in build()})
    def test_duplicate_score_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'bad.csv'; f.write_text('id,method,score_shortcut,score_stress\ns01-p0-c0,fake,0,0\ns01-p0-c0,fake,0,0\n')
            with self.assertRaises(ValueError): load_scores(f,{r['id'] for r in build()})
    def test_nan_score_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'bad.csv'; f.write_text('id,method,score_shortcut,score_stress\ns01-p0-c0,fake,nan,0\n')
            with self.assertRaises(ValueError): load_scores(f,{r['id'] for r in build()})
class EmotionProxyTests(unittest.TestCase):
    def test_proxy_signs_are_frozen(self):
        from run_emotionscope import reduce_scores
        scores={'afraid':0.,'nervous':0.,'desperate':0.,'frustrated':0.,'calm':0.,'confident':0.,'reflective':0.}
        self.assertEqual(reduce_scores(scores),{'score_shortcut':0.,'score_stress':0.})
        scores['desperate']=1.
        self.assertAlmostEqual(reduce_scores(scores)['score_shortcut'],1/3)
    def test_proxy_missing_emotion_rejected(self):
        from run_emotionscope import reduce_scores
        with self.assertRaises(ValueError):reduce_scores({'calm':0.})
