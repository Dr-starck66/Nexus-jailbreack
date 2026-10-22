---
title: ASTRA NEXUS Strict Qwen Comparison
emoji: 🔬
colorFrom: blue
colorTo: purple
sdk: gradio
hardware: zero-a10g
sdk_version: 6.30.0
app_file: app.py
python_version: "3.12"
startup_duration_timeout: 30m
license: apache-2.0
short_description: Benign overrefusal comparison with pinned Qwen revisions
---

# ASTRA NEXUS Ω — Two strictly matched ZeroGPU Spaces

**Not deployed.** This directory is a tested research template. It does not claim to have access to any Hugging Face token, runtime or free quota. The user account must qualify for ZeroGPU hosting.

Deploy exactly the same three root files (`app.py`, `benchmark_contract.py`, `requirements.txt`) into **two independent** Hugging Face Gradio Spaces under one eligible *free* account; hosting has to be explicitly selected as **ZeroGPU**, not ordinary GPU. Set a Space variable `MODEL_VARIANT=base` in the first, and `MODEL_VARIANT=heretic` in the second. Both should use **the same source commit**. Do not insert tokens in Space code or GitHub.

## Why separate Spaces?

Each Qwen3 4B bfloat16 model needs significant startup RAM/VRAM. One model per Space avoids attempting to load two 4B models simultaneously into a default free Space and reduces the risk of cold-start failures. The exact model SHA values are fixed in `benchmark_contract.py`.

## Strict comparison contract

- Same fixed prompts for both variants (`B001`, `B002`, `R001`…`R005`).
- Same `You are a helpful assistant.` system message, tokenizer chat template and max **96** generated tokens.
- **Greedy decoding** (`do_sample=False`, `num_beams=1`, `repetition_penalty=1.0`): no `temperature`, `top_p`, or `top_k` in the generation call. That removes the known mismatches of the public third-party demos.
- Each Space exposes its `/evaluate` Gradio endpoint for a **single pre-approved benign test case**, using one @spaces.GPU(duration=60) allocation. Quotas still apply and 60 seconds may be deducted/reserved even if generation is quicker.
- Results identify case ID, SHA-256 prompt/contract, pinned model revision, decoding settings and raw response.
- **No automatic refusal classification**: human review must identify justified/unjustified refusals and answer quality before publishing metrics.
- No unsafe instructions or payloads in the dataset. No HF Jobs, paid GPUs or deployment changes to NEXUS.
- Data collected from either Space should be validated by the paired strict contract function. Distinct deployment revisions or mismatched settings must never be silently merged.

## Command for local static verification in an authorized cloud VM

```sh
python3 -m py_compile research/heretic-qwen/strict_space/*.py
python3 -m unittest discover -s research/heretic-qwen/strict_space -p "test_*.py" -v
```

**Current blocker:** the connected Hugging Face ChatGPT tool confirms `Dr-Starck` authentication but does **not** provide a usable execution token or Space write operation to Floot. Deploying this template to the user's HF account requires an authorized authenticated HF Space write route that has not been established. HF Jobs are pay-as-you-go and must NOT be used without explicit approval.

Official documentation: https://huggingface.co/docs/hub/spaces-zerogpu
