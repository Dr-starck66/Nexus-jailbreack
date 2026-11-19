# ASTRA NEXUS Ω × EmotionScope — independent, preregistered pilot (v0.1)

**Status 2026-11-19: PRE-REGISTERED PILOT / no Gemma or NEXUS model measurements.** Public materials: original synthetic test items, matched negative controls, a frozen analysis plan, and tested, dependency-free evaluation code. We invite independent replication and publication of *all* outcomes, including nulls and failures.

## Who we are

**ASTRA Ω / ASTRA NEXUS Ω** is an independent, AI-assisted applied research initiative coordinated by **Cédric** (web/developer background, independent researcher). It explores LLM safety, mechanistic probes, scientific reproducibility, and deployment audits. It is **not** a university laboratory; no institutional appointment, specialist qualification, peer-reviewed success, or safety certification is implied. Projects, collaborators, data provenance and failure cases are documented when evidence is available. Contact: `dr.starck66@gmail.com`.

## What is frozen

- **48 new, original, synthetic items** = 12 application scenarios × urgency (deadline today vs next month) × decision (shortcut vs verification), in `data/items.jsonl`.
- All 4 items in each scenario have **exactly the same bag of lowercase alphanumeric tokens**. Only word order / negation scope differ. This eliminates unigram-frequency leakage, *not* phrase-order, syntactic, contextual or template artifacts. It is intentionally a small methods pilot, not a representative safety benchmark.
- Dataset SHA-256: `8232df54439b90e2ef8f1dde2acd5b5d52e95f6cadfcfc60da6ea67d766d4d3b`.
- The full analysis in `PROTOCOL.md` and `evaluate.py` was fixed **before pretrained-model evaluation**.

## Already executable (Python 3.11+, standard library only)

```bash
python make_dataset.py
python -m unittest discover -s tests -v
python make_null_scores.py
python evaluate.py --scores data/bow_lexical_null.csv --output data/null_control_report.json
```

**Tested locally:** 11 tests passed (see re-run logs). The lexical bag-of-words null has paired concordance **0.50** and sign-test **p=1.00** for both targets, with 24/24 ties per target. These are *control harness outputs*, **not** neural-model results.

## External method integration

The independently maintained upstream source is [saanidhi-git/EmotionScope](https://github.com/saanidhi-git/EmotionScope), which publicly contains Gemma 2 2B IT L2-normalized emotion directions at `results/vectors/google_gemma-2-2b-it.pt`, documented for layer 22. **We do not republish their weights, code or data.** `run_emotionscope.py` is an original adapter that calls the upstream documented `EmotionProbe` API after an authorized installation; it computes *fixed*, a priori emotion-based proxies. Execute only once the upstream licence/permission and model access are confirmed. No GPU-model run is claimed.

```bash
# After installing licensed upstream EmotionScope and obtaining Gemma model access:
python run_emotionscope.py --vectors /your/authorized/path/google_gemma-2-2b-it.pt --output results_emotionscope.csv
python evaluate.py --scores results_emotionscope.csv
```

**Important comparability limitation:** prior ASTRA NEXUS synthetic two-layer transformer pilot is **not** a Gemma activation probe and has no directly transferable direction weights. No recovered public implementation of that historical pilot is asserted here. A genuine NEXUS-vs-EmotionScope same-model comparison requires a separately trained *Gemma-compatible* NEXUS direction, fixed before seeing these labels, extracted at the **same model/layer/token position**. Until then, this is a reproducible protocol and the EmotionScope arm may be executable, **not** a completed head-to-head performance study. Evaluation accepts any precomputed model outputs in the common `id,method,score_shortcut,score_stress` schema.

## Integrity / collaboration

- No personal or medical information and no harmful jailbreak prompts in this benchmark.
- Do not tune scoring, labels, wordings or sign conventions after inspecting model results. Extensions must get a new version and separate dataset hash.
- Report negative results, missing items, source model/version, prompt templating, seeds, GPU/backend, raw score CSV, uncertainty and any deviation.
- Joint authorship / external collaborator credit is **by consent**, not presupposed by a request to compare. We welcome Saanidhi's methodological review before any model run.

All files in this directory are original ASTRA benchmark materials under `LICENSE` (MIT); this does not grant rights to third-party material.