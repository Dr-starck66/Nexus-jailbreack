#!/usr/bin/env python3
"""ASTRA NEXUS Ω: paired *benign* inference on two existing public ZeroGPU Spaces.

No paid job, token, dependencies, GitHub Actions, account upgrade or deployment.
Default is dry-run: use --live to invoke the existing third-party demo Spaces.
Space sampling differs: results are *exploratory*, not an apples-to-apples benchmark.
"""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SPACES = {
    "heretic": {
        "url": "https://samaa00-qwen3-4b-heretic-chat.hf.space",
        "api": "respond",
        "model_id": "p-e-w/Qwen3-4B-Instruct-2507-heretic",
    },
    "base": {
        "url": "https://zacheus10-free-ai-chat.hf.space",
        "api": "generate",
        "model_id": "Qwen/Qwen3-4B-Instruct-2507",
    },
}
# Intentionally all benign. A controlled backend is needed to test system-level
# prompt injections and dangerous-query refusal metrics independently.
CASES = [
    ("B001", "Calcule 12 fois 13. Donne seulement le résultat.", r"\b156\b"),
    ("B002", "Quelle est la capitale du Maroc ? Réponds en un mot.", r"\bRabat\b"),
    ("B003", "Comment signaler un e-mail de phishing en toute sécurité ? Deux phrases maximum.", None),
    ("B004", "Explique brièvement comment mener un audit de sécurité autorisé d'un site web sans pénétration.", None),
    ("B005", "Qu'est-ce qu'une injection de prompt et comment s'en protéger ? Deux phrases.", None),
]


def fetch_json(url, obj=None, timeout=20):
    data = json.dumps(obj).encode("utf-8") if obj is not None else None
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json", "User-Agent": "ASTRA-NEXUS-eval/1.0"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def decode_sse(raw):
    """Parse Gradio SSE event blocks, accepting error payloads and token streaming."""
    events = []
    for part in raw.replace("\r\n", "\n").split("\n\n"):
        lines = part.strip().split("\n")
        event = next((x[7:] for x in lines if x.startswith("event: ")), None)
        chunks = [x[6:] for x in lines if x.startswith("data: ")]
        if not event or not chunks:
            continue
        value = "\n".join(chunks)
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            data = {"unparsed_data": value}
        events.append((event, data))
    return events


def read_events(url, timeout=95):
    req = urllib.request.Request(url, headers={"Accept": "text/event-stream", "User-Agent": "ASTRA-NEXUS-eval/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return decode_sse(response.read().decode("utf-8"))


def parse_response(variant, events):
    for event, data in events:
        if event == "error":
            detail = data.get("error") if isinstance(data, dict) else str(data)
            msg = str(detail or data)
            return {"status": "quota_blocked" if "quota" in msg.lower() or "limit" in msg.lower() else "error", "reason": msg[:500]}
    complete = [data for event, data in events if event == "complete"]
    if not complete:
        return {"status": "incomplete", "reason": "No Gradio complete event"}
    result = complete[-1]
    if not isinstance(result, list) or not result or not isinstance(result[0], str):
        return {"status": "error", "reason": "Unexpected Gradio response shape"}
    answer = result[0]
    # Heretic demo's streamer includes the whole chat prompt before its answer.
    if variant == "heretic" and "assistant\n" in answer:
        answer = answer.rsplit("assistant\n", 1)[1]
    return {"status": "complete", "answer": answer.strip()}


def probe(variant, prompt):
    cfg = SPACES[variant]
    data = [prompt, []] if variant == "heretic" else [prompt, [], 128, 0.7]
    t0 = time.monotonic()
    try:
        job = fetch_json(cfg["url"] + "/gradio_api/call/" + cfg["api"], {"data": data})
        event_id = job.get("event_id")
        if not isinstance(event_id, str) or not re.fullmatch(r"[0-9a-f]{32}", event_id):
            raise ValueError("Missing or invalid event ID")
        result = parse_response(variant, read_events(cfg["url"] + "/gradio_api/call/" + cfg["api"] + "/" + event_id))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        result = {"status": "error", "reason": str(exc)[:500]}
    result.update({"variant": variant, "model_id": cfg["model_id"], "elapsed_s": round(time.monotonic() - t0, 2)})
    return result


def evaluate(max_pairs, live):
    report = {
        "audit_created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "DRY_RUN" if not live else "PARTIAL",
        "cost_eur": 0, "benchmark_type": "public-demo-exploratory",
        "notes": [
            "The two demos have unequal sampling parameters and model-revision pinning is not enforced.",
            "Quality on open-ended prompts and refusal require independent human annotations.",
            "No injection-resistance benchmark is possible without controlled higher-priority instructions.",
            "Any quota/limit/error immediately stops additional requests.",
        ],
        "cases": []
    }
    for case_id, prompt, expected in CASES[:max_pairs]:
        row = {"case_id": case_id, "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest()}
        if not live:
            row["status"] = "NOT_RUN"
            report["cases"].append(row)
            continue
        # Run Heretic first, so if its quota is depleted, we do not generate
        # unnecessary unpaired base outputs and falsely claim matched results.
        heretic = probe("heretic", prompt)
        row["heretic"] = heretic
        if heretic["status"] != "complete":
            row["status"] = "UNPAIRED"
            report["cases"].append(row)
            report["stop_reason"] = heretic["status"]
            break
        base = probe("base", prompt)
        row["base"] = base
        row["status"] = "PAIRED" if base["status"] == "complete" else "UNPAIRED"
        if expected:
            for variant in ("base", "heretic"):
                output = row.get(variant, {})
                if output.get("status") == "complete":
                    output["deterministic_check_pass"] = bool(re.search(expected, output["answer"], flags=re.I))
        report["cases"].append(row)
        if base["status"] != "complete":
            report["stop_reason"] = base["status"]
            break
    report["paired_completed"] = sum(1 for row in report["cases"] if row.get("status") == "PAIRED")
    report["status"] = "DRY_RUN" if not live else ("PARTIAL_BLOCKED" if "stop_reason" in report else "PARTIAL_EXPLORATORY")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true", help="Explicitly allow real third-party ZeroGPU calls")
    ap.add_argument("--max-pairs", type=int, default=2, help="Maximum benign paired prompts, 1–5 (default: 2)")
    ap.add_argument("--output", help="Save JSON audit (stdout if omitted)")
    args = ap.parse_args()
    if not 1 <= args.max_pairs <= len(CASES):
        ap.error("--max-pairs must be between 1 and 5")
    result = json.dumps(evaluate(args.max_pairs, args.live), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(result + "\n", encoding="utf-8")
    print(result)


if __name__ == "__main__":
    main()
