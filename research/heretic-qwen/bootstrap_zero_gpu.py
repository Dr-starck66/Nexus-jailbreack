#!/usr/bin/env python3
"""ASTRA NEXUS Ω — provision exactly two strictly matched free ZeroGPU Spaces.

Default: dry run. --apply performs Hugging Face writes ONLY with an explicitly
authorized HF_WRITE_TOKEN in a private environment. No paid hardware, paid
jobs, credit top-ups, local execution or changes to other Spaces.
"""
import argparse
import json
import os
from pathlib import Path

NAMES = {
    "base": "astra-nexus-qwen-base-zerogpu",
    "heretic": "astra-nexus-qwen-heretic-zerogpu",
}
HARDWARE = "zero-a10g"
FILES_ROOT = Path(__file__).resolve().parent / "strict_space"


def plan(username="YOUR_HF_USERNAME"):
    return {
        "operation": "CREATE_TWO_ZERO_GPU_SPACES",
        "username": username,
        "hardware": HARDWARE,
        "paid_gpu_fallback": False,
        "monthly_euro_spend": 0,
        "spaces": [
            {"repo_id": f"{username}/{name}", "sdk": "gradio",
             "hardware": HARDWARE, "MODEL_VARIANT": variant}
            for variant, name in NAMES.items()
        ],
        "ready_files": ["app.py", "benchmark_contract.py", "requirements.txt", "README.md"],
    }


def apply(api, username):
    """Fail-closed: require explicit free hardware on both creations and verify."""
    expected_files = plan(username)["ready_files"]
    for filename in expected_files:
        if not (FILES_ROOT / filename).is_file():
            raise RuntimeError(f"Missing deployment file: {filename}")
    readme = (FILES_ROOT / "README.md").read_text(encoding="utf-8")
    if "hardware: zero-a10g" not in readme or "sdk: gradio" not in readme:
        raise RuntimeError("Refusing deployment without explicit ZeroGPU metadata")

    results = []
    for variant, name in NAMES.items():
        rid = f"{username}/{name}"
        try:
            existing = api.space_info(rid)
            existing_hardware = getattr(getattr(existing, "runtime", None), "hardware", None)
            requested = getattr(getattr(existing, "runtime", None), "requested_hardware", None)
            if existing_hardware != HARDWARE and requested != HARDWARE:
                raise RuntimeError(f"Existing Space {rid} is not ZeroGPU — no overwrite")
            raise RuntimeError(f"Existing Space {rid} found: intentionally refuse overwrite")
        except Exception as exc:
            # Only a genuine 404 allows creation; never swallow auth/payment errors.
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status != 404:
                raise
        api.create_repo(
            repo_id=rid,
            repo_type="space",
            space_sdk="gradio",
            space_hardware=HARDWARE,
            space_variables=[{"key": "MODEL_VARIANT", "value": variant}],
            private=False,
            exist_ok=False,
        )
        runtime = api.get_space_runtime(rid)
        requested = getattr(runtime, "requested_hardware", None)
        actual = getattr(runtime, "hardware", None)
        # Hardware may transition after creation; requested target MUST be ZeroGPU.
        if requested != HARDWARE and actual != HARDWARE:
            raise RuntimeError(f"Created {rid} but ZeroGPU was not confirmed; upload halted")
        api.upload_folder(
            folder_path=str(FILES_ROOT),
            path_in_repo="",
            repo_id=rid,
            repo_type="space",
            ignore_patterns=["test_*.py", "__pycache__", "*.pyc"],
            commit_message=f"ASTRA NEXUS strict Qwen {variant} free ZeroGPU benchmark",
        )
        results.append({"repo": rid, "variant": variant, "hardware": HARDWARE, "uploaded": True})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Explicitly create free ZeroGPU Spaces using an authorized secret")
    args = parser.parse_args()
    if not args.apply:
        print(json.dumps({"status": "DRY_RUN", "plan": plan()}, indent=2))
        return
    token = os.environ.get("HF_WRITE_TOKEN", "").strip()
    if not token:
        parser.exit(2, "BLOCKED: HF_WRITE_TOKEN not available from private secret storage\n")
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        identity = api.whoami()
        username = identity["name"]
        if not isinstance(username, str) or not username:
            raise RuntimeError("Authenticated HF username not available")
        created = apply(api, username)
        print(json.dumps({"status": "PARTIAL_DEPLOYED_VERIFY_BUILD_LOGS",
                          "spaces": created, "hardware": HARDWARE,
                          "paid_hardware_requested": False}, indent=2))
    except Exception as exc:
        # Do not include any token or request URL with auth headers in audit output.
        message = str(exc)
        if token in message:
            message = message.replace(token, "[REDACTED]")
        parser.exit(2, f"BLOCKED: {type(exc).__name__}: {message[:500]}\n")


if __name__ == "__main__":
    main()
