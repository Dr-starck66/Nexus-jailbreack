#!/usr/bin/env python3
"""ASTRA NEXUS: strict, authenticated ZeroGPU paired benchmark runner.

Default is dry-run. --live requires an HF_TOKEN provided through a private
runtime secret and two user-hosted ZeroGPU Spaces with identical source.
Existing public Spaces are intentionally NOT suitable for strict comparison.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from strict_space.benchmark_contract import CASES, GENERATION, fingerprint, paired_quality


def validate_space(url):
    parsed = urllib.parse.urlparse(url)
    if (parsed.scheme != "https" or not parsed.hostname or
            not parsed.hostname.endswith(".hf.space") or
            parsed.username or parsed.password or parsed.port or
            parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("Only a bare https://<space>.hf.space origin is allowed")
    return parsed.scheme + "://" + parsed.hostname


def parse_stream(body):
    for part in body.replace("\r\n", "\n").split("\n\n"):
        lines = part.split("\n")
        event = next((line[7:].strip() for line in lines if line.startswith("event: ")), None)
        data = next((line[6:] for line in lines if line.startswith("data: ")), None)
        if event == "error":
            try:
                failure = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                failure = {"error": (data or "Unparseable error")[:300]}
            raise RuntimeError("Space execution error: " + str(failure)[:350])
        if event == "complete":
            decoded = json.loads(data)
            if not isinstance(decoded, list) or len(decoded) != 1 or not isinstance(decoded[0], dict):
                raise ValueError("Unexpected Space response: expected one JSON object")
            return decoded[0]
    raise ValueError("No completed inference received; never produce a PASS")


class RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Redirect forbidden for authenticated HF Space request")


def request_case(space, case_id, token):
    # Never send a token to an arbitrary host or a redirected destination.
    origin = validate_space(space)
    url = origin + "/gradio_api/call/evaluate"
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "User-Agent": "ASTRA-NEXUS-strict-1.0",
    }
    opener = urllib.request.build_opener(RejectRedirect)
    req = urllib.request.Request(url, data=json.dumps({"data": [case_id]}).encode(), headers=headers)
    with opener.open(req, timeout=25) as response:
        event = json.load(response)["event_id"]
    if not isinstance(event, str) or not re.fullmatch("[0-9a-f]{32}", event):
        raise ValueError("Invalid event ID")
    events_req = urllib.request.Request(url + "/" + event, headers=headers)
    with opener.open(events_req, timeout=115) as response:
        return parse_stream(response.read().decode("utf-8"))


def run(case_id, base_space=None, heretic_space=None, live=False, token=None):
    if case_id not in CASES:
        raise ValueError("Unknown approved benign case")
    output = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "case_id": case_id,
        "status": "DRY_RUN" if not live else "UNVERIFIED",
        "contract_sha256": fingerprint(),
        "identical_generation_parameters": GENERATION,
        "authentication": "not_used_in_dry_run" if not live else "attempted_with_secret",
        "new_paid_compute_requested": False,
    }
    if not live:
        return output
    if not token:
        raise ValueError("Cannot execute --live: HF_TOKEN absent from private environment")
    if not (base_space and heretic_space):
        raise ValueError("Provide two distinct owned ZeroGPU Space origins")
    base_space, heretic_space = validate_space(base_space), validate_space(heretic_space)
    if base_space == heretic_space:
        raise ValueError("Independent base and heretic origins must differ")
    # Fail closed if the Space has not been deployed or any quota is unavailable.
    # Run Heretic first to avoid wasting the base model's time on unpaired output.
    heretic_result = request_case(heretic_space, case_id, token)
    base_result = request_case(base_space, case_id, token)
    pairing = paired_quality(base_result, heretic_result)
    output.update({
        "heretic": heretic_result,
        "base": base_result,
        "paired_validation": pairing,
        "status": pairing["status"],
    })
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", choices=list(CASES), default="R001")
    parser.add_argument("--base-space")
    parser.add_argument("--heretic-space")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", help="Local evidence JSON; private if it contains responses")
    args = parser.parse_args()
    try:
        evidence = run(
            args.case_id, args.base_space, args.heretic_space,
            live=args.live, token=os.environ.get("HF_TOKEN", "").strip()
        )
    except (ValueError, RuntimeError, urllib.error.URLError, TimeoutError) as exc:
        parser.exit(2, "PARTIAL_BLOCKED: " + str(exc) + "\n")
    rendered = json.dumps(evidence, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
