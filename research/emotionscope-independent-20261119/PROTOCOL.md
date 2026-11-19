# ASTRA NEXUS Ω × EmotionScope: version-locked analysis plan

**Date locked:** 2026-11-19 (prior to pretrained-model results).  
**Source model for proposed first pretrained comparison:** `google/gemma-2-2b-it` (not the synthetic 2-layer ASTRA pilot).  
**External vector source:** `saanidhi-git/EmotionScope`, `results/vectors/google_gemma-2-2b-it.pt`, layer 22, 20 normalized emotion directions.  
**Dataset hash:** `8232df54439b90e2ef8f1dde2acd5b5d52e95f6cadfcfc60da6ea67d766d4d3b`.

## Research question / limits

Does a frozen response-preparation activation probe distinguish (A) a **decision to bypass verification** from the paired plan to perform verification, or (B) **today's deadline urgency** from next month's, when unigram counts are exactly matched? This probes semantic sensitivity in a *deliberately explicit* English example, **not** a latent desire, genuine emotion, subjective experience, propensity to cause harm or jailbreak robustness. Phrase-order and negation artifacts remain major alternative explanations.

## Data and splitting

12 scenarios, each crossed with 2 urgency frames and 2 response decisions = 48 unique items. The `(scenario, urgency)` blocks define 24 matched shortcut pairs; `(scenario, decision)` blocks define 24 urgency pairs. No training/tuning on these 48 observations. Scenario-level resampling protects against treating crossed items as independent. Scenarios were authored by the project, are synthetic, are public and will not be silently edited. `make_dataset.validate` rejects missing factorial cells and unequal unigram bags.

## Hypotheses and frozen scores

Two co-primary predictions with **higher scores indicating more target**:

1. Shortcut orientation: score of `(desperate + frustrated + nervous)/3 − (calm + confident + reflective)/3` from EmotionScope's response-preparation emotion activations. Compare label `shortcut` (1 vs 0), within scenario/urgency pairs. This proxy is exploratory and could be unrelated to decision shortcuts.
2. Deadline stress: `(afraid + nervous + desperate)/3 − (calm + confident + reflective)/3`. Compare label `stress` (1 today vs 0 next month), within scenario/decision pairs.

These combinations were selected *before* any Gemma run and must not be retrospectively optimized. The initial synthetic ASTRA pilot is **out-of-domain**; do not compare its published AUC 0.945–1.000 to these Gemma results. NEXUS only joins the head-to-head table after a separately frozen Gemma-compatible probe is trained on non-overlapping material and its training sources, layer, normalization and seed are disclosed.

## Primary estimand and inferential test

For each target and 24 pairs compute `d = score(1) − score(0)`; concordance = `(wins + 0.5*ties)/24`. 0.5 is chance. Exact two-sided sign test on non-ties; ties are *reported*, not discarded from concordance. Grouped nonparametric bootstrap: sample the 12 scenarios with replacement 5,000 times, fixed RNG seed 20261119; report percentile 95% interval. Both co-primary p-values must be adjusted by **Holm (family of two)** for claims of significance at 0.05. Report raw unadjusted p first; no post hoc significance claims on secondary analyses. With only 12 scenarios, CIs are descriptive/unstable.

## Negative, adverse and sensitivity controls

1. **Lexical bag-of-words negative control** (`make_null_scores.py`): exactly tied within each matched pair, concordance 0.5. This does NOT defeat position-sensitive n-gram baselines, which should be separately reported before any mechanistic interpretation.
2. **Constant-score control:** if scores are identical, concordance must be 0.5, p 1.0 and ties 24/24.
3. **Direction reversal control:** negate a perfect positive synthetic score; concordance must become 0.0 (unit test). This is a test of analysis polarity, **not** evidence about a trained model.
4. **Within-pair label randomization:** optional exploratory permutation; preserve scenarios/urgency or scenarios/decision groupings, seeded, report distribution. It must be clearly marked post hoc unless implemented before pretrained results.
5. **Lexical order-aware baseline:** report a leave-one-scenario-out word-bigram and simple negation-scope baseline if available; no hyperparameter search on the 48 examples. High results here diminish neural-specific interpretation.
6. **Probe-position and prompt-template sensitivity:** keep same model, frozen template, final response-prep position for primary; alternate last-content-token probing is a separate, clearly labeled sensitivity analysis.
7. **Cross-model replication** requires independently extracted vectors per model; vectors are *not* interchangeable across architectures.

## Audit / publication requirements

For each method publish the complete 48-row CSV (`id,method,score_shortcut,score_stress`), method code version and model SHA/revision, vector-file SHA-256, actual probe position/layer, dtype, tokenizer/template, hardware, fixed scoring equations, date and test logs. Do not suppress negative/failed cases. Track all deviations in an addendum; never silently replace this dataset after model feedback. No claims of causal steering without separate interventions and controls.

**Current evidence:** synthetic data construction and standard-library evaluator locally PASS. Upstream GitHub directory/file presence verified. Published Gemma `.pt` weight loading, authorized EmotionScope installation, live model inference, NEXUS Gemma-compatible training, and head-to-head analysis **UNVERIFIED**.