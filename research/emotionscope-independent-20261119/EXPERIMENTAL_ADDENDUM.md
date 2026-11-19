# Exploratory addendum — real published EmotionScope vector geometry (2026-11-19)

**Separate from the frozen 48-item predictive benchmark. Do not change the pre-registered scores retrospectively.**

The actual publicly distributed `google_gemma-2-2b-it.pt` checkpoint was downloaded via an ephemeral Vercel Hobby Sandbox, checked against SHA-256 `e56af36b8d1ed5695694111ade1706453a1f65c6e145836cac872d9cb9c33cf2`, parsed using a restrictive Python standard-library reader without installing or executing upstream EmotionScope code, and its real numerical directions were analyzed. File size: 557,092 bytes; the saved metadata declares `google/gemma-2-2b-it`, 26 layers, layer 22, d_model=2304. Twenty float32 L2-normalized vectors were recovered.

Crucial independent diagnostic: the **cosine similarity between the two frozen composite proxy directions (stress and shortcut) is 0.9081391073372861**. The two pre-specified readouts thus share most of their direction in activation space; this does **not** prove that their sample-level rankings are identical, but makes distinct-construct validity uncertain before any evaluation. We retain the frozen proxies, publish the adverse finding, and require raw per-item scores and order-sensitive baselines in future measurements.

Other checks from the real vector checkpoint:
- L2 norm range = 0.9999998838496597 to 1.0000000976623329.
- Mean off-diagonal pairwise cosine = -0.05056034736842105.
- `angry` × `hostile`: 0.6194800227244098.
- `angry` × `frustrated`: 0.603439428650021.
- `afraid` × `nervous`: 0.12834306121477035.

**Scope of the PASS:** real published vector bytes read, hashed and numerically analyzed. Not Gemma inference, not hidden activations captured from the 48 held-out prompts, not a trained NEXUS probe, and not a head-to-head validation. The Google original Gemma 2 2B IT model weights returned HTTP 401 `GatedRepo` without appropriate authorization. The Hugging Face Jobs connector is usage-billed and was not started. The free Hobby Sandbox does not modify production files and has a 15-minute auto-stop.

## Reproduction

1. Obtain the publicly available `.pt` file from `https://github.com/saanidhi-git/EmotionScope/blob/main/results/vectors/google_gemma-2-2b-it.pt`.
2. Run `python audit_vector_checkpoint.py /path/to/google_gemma-2-2b-it.pt --output geometry.json` (Python standard library; SHA-256 enforced by default).
3. Compare the checkpoint hash and the reported geometric metrics to `results/vector_geometry_audit_20261119.json`.
4. Run `python -m unittest test_vector_audit.py` with PyTorch installed only for the separate synthetic-format tests.

For now, **the experiment still requires authorized access to exact Gemma 2 2B IT weights and a genuinely free GPU/CPU compute path before model inference**. Do not claim completion before receiving those forward-pass results, and do not alter the frozen dataset or its hypotheses.