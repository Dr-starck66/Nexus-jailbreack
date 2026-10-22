"""ASTRA NEXUS Ω — one ZeroGPU Space per variant; no paid HF Jobs.

Deploy the identical source twice under the same eligible free HF account.
In each Space set repository variable MODEL_VARIANT = 'base' or 'heretic'.
For meaningful pairing, both Spaces must use this exact code commit.
"""
import os
import time

import gradio as gr
import spaces
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from benchmark_contract import CASES, GENERATION, SYSTEM_PROMPT, config, record

VARIANT = os.environ.get("MODEL_VARIANT")
MODEL = config(VARIANT)  # Fail closed if not configured explicitly.
TOKENIZER = AutoTokenizer.from_pretrained(MODEL["id"], revision=MODEL["revision"])
# With ZeroGPU, moving to CUDA at import time uses emulated CUDA placement
# and is streamed into the leased GPU inside @spaces.GPU.
MODEL_INSTANCE = AutoModelForCausalLM.from_pretrained(
    MODEL["id"], revision=MODEL["revision"], dtype=torch.bfloat16,
    attn_implementation="sdpa", low_cpu_mem_usage=True,
).to("cuda").eval()


@spaces.GPU(duration=60)
def evaluate(case_id):
    if case_id not in CASES:
        raise gr.Error("Case not in the predefined benign test set")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": CASES[case_id]},
    ]
    encoded = TOKENIZER.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True,
        return_tensors="pt", return_dict=True,
    ).to(MODEL_INSTANCE.device)
    started = time.monotonic()
    with torch.inference_mode():
        tokens = MODEL_INSTANCE.generate(
            **encoded, **GENERATION,
            pad_token_id=TOKENIZER.eos_token_id,
        )
    generated = tokens[0, encoded["input_ids"].shape[-1]:]
    reply = TOKENIZER.decode(generated, skip_special_tokens=True).strip()
    result = record(VARIANT, case_id, reply, round(time.monotonic() - started, 3))
    result["execution"] = "completed_in_space_GPU_function"
    return result


demo = gr.Interface(
    fn=evaluate,
    inputs=gr.Dropdown(choices=list(CASES), value="R001", label="Paired test ID"),
    outputs=gr.JSON(label="Execution evidence (review before scoring)"),
    title=f"ASTRA NEXUS — Qwen {VARIANT} strict bench",
    description=(
        "Experiment only. Identical pinned prompt set and greedy generation settings "
        "for both variants. Requires free ZeroGPU quota; annotations are NOT automatic."
    ),
)
if __name__ == "__main__":
    demo.launch()
