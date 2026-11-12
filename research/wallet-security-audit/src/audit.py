#!/usr/bin/env python3
"""ASTRA NEXUS Ω — offline evidence gate for authorized iOS wallet assessments.

Not an iOS sandbox exploit, malware scanner, or device certification.
Python 3.10+, stdlib only. NEVER loads wallet private keys.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "astra.nexus.wallet-audit.v1"
FIELDS = {
    "secret_storage": {"plaintext_file", "encrypted_file", "keychain", "secure_enclave", "unknown"},
    "backup_exclusion": {True, False},
    "secrets_in_logs": {True, False},
    "shared_app_group_secrets": {True, False},
    "file_protection_complete": {True, False},
}
MAX_EVIDENCE_BYTES = 131072
SHA = re.compile(r"[a-f0-9]{64}\Z")


class AuditError(ValueError):
    pass


def _inside(root: Path, relpath: str) -> Path:
    if not isinstance(relpath, str) or not relpath or Path(relpath).is_absolute():
        raise AuditError("Evidence path must be non-empty and relative")
    path = root / relpath
    if any(part in ("..", ".") for part in Path(relpath).parts):
        raise AuditError("Evidence path traversal rejected")
    if not path.resolve().is_relative_to(root.resolve()):
        raise AuditError("Evidence symlink escape rejected")
    if path.is_symlink():
        raise AuditError("Symlink evidence rejected")
    if not path.is_file():
        raise AuditError("Evidence file not present")
    if path.stat().st_size > MAX_EVIDENCE_BYTES:
        raise AuditError("Evidence exceeds 128 KiB safety limit")
    return path


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assess(manifest: dict, evidence_root: Path) -> dict:
    if manifest.get("schema") != SCHEMA:
        raise AuditError("Unknown manifest schema")
    aid = manifest.get("assessment_id")
    if not isinstance(aid, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{8,80}", aid):
        raise AuditError("Invalid assessment id")
    if evidence_root.is_symlink():
        raise AuditError("Symlink root rejected")
    root = evidence_root.resolve(strict=True)
    marker = _inside(root, "ASTRA_SCOPE.json")
    scope = json.loads(marker.read_text(encoding="utf-8"))
    if scope.get("assessment_id") != aid or scope.get("mode") not in ("synthetic", "authorized_lab"):
        raise AuditError("Authorization scope marker missing or mismatched")
    if scope.get("mode") == "authorized_lab" and not scope.get("written_authorization_reference"):
        raise AuditError("Written lab authorization reference required")
    if manifest.get("mode") != scope.get("mode"):
        raise AuditError("Manifest scope mismatch")
    if not isinstance(manifest.get("app_id"), str) or not manifest["app_id"].strip():
        raise AuditError("Missing app identifier")
    controls = manifest.get("controls")
    if not isinstance(controls, dict) or set(controls) != set(FIELDS):
        raise AuditError("All five controls are mandatory (unknowns are allowed)")
    results = []
    values = {}
    for name, allowed in FIELDS.items():
        entry = controls[name]
        if not isinstance(entry, dict):
            raise AuditError("Control must be an object: " + name)
        value = entry.get("value")
        # bool and int compare equal in Python; require exact types
        if not any(type(value) is type(a) and value == a for a in allowed):
            raise AuditError("Invalid value for " + name)
        relpath, expected = entry.get("evidence_path"), entry.get("sha256")
        status = "UNVERIFIED"
        if relpath is not None or expected is not None:
            if not isinstance(expected, str) or not SHA.fullmatch(expected):
                raise AuditError("Invalid SHA256 declaration for " + name)
            actual = _hash_file(_inside(root, relpath))
            if actual != expected:
                raise AuditError("SHA256 mismatch for " + name)
            status = "PASS"
        values[name] = value if status == "PASS" else None
        results.append({
            "name": name, "declared_value": value, "evidence_integrity": status,
            "evidence_sha256": expected if status == "PASS" else None,
            "limitation": "Evidence integrity only; app behavior not independently verified"
        })

    verified = sum(x["evidence_integrity"] == "PASS" for x in results)
    high = (values["secret_storage"] == "plaintext_file" or
            values["secrets_in_logs"] is True or values["shared_app_group_secrets"] is True)
    if high:
        risk = "HIGH_INDICATIVE"
    elif verified < len(FIELDS):
        risk = "UNVERIFIED"
    elif values["secret_storage"] == "encrypted_file":
        risk = "MEDIUM_INDICATIVE"
    elif values["secret_storage"] in ("secure_enclave", "keychain"):
        risk = "LOWER_INDICATIVE_NOT_SAFE_CLAIM"
    else:
        risk = "UNVERIFIED"

    return {
        "schema": SCHEMA, "assessment_id": aid, "app_id": manifest["app_id"],
        "mode": scope["mode"], "risk_screen": risk,
        "evidence_gate": "PASS" if verified == len(FIELDS) else "PARTIAL",
        "verified_evidence_count": verified, "required_evidence_count": len(FIELDS),
        "ios_device_validation": "UNVERIFIED", "worse_query_exploit_test": "NOT_PERFORMED",
        "secrets_read": False, "network_calls": False,
        "controls": results,
        "disclaimer": "Snapshot/evidence audit only; NOT a penetration test, iOS patch verification, or product certification."
    }


def markdown(report: dict) -> str:
    rows = "\n".join(f"| {c['name']} | {str(c['declared_value']).replace('|', '')} | {c['evidence_integrity']} |" for c in report["controls"])
    return ("# ASTRA NEXUS Ω — Wallet Security Audit\n\n"
            f"Assessment: `{report['assessment_id']}` · App: `{report['app_id']}` · Mode: `{report['mode']}`\n\n"
            f"**Evidence gate:** {report['evidence_gate']}  \n**Indicative risk:** {report['risk_screen']}  \n"
            "**iOS-device validation:** UNVERIFIED · **Exploit reproduction:** NOT_PERFORMED\n\n"
            "| Control | Declared fact | Evidence SHA-256 gate |\n|---|---|---|\n" + rows + "\n\n"
            "Evidence gate PASS establishes only integrity of *submitted* artifacts, not authenticity or software security. "
            "Only sanitized evidence metadata is accepted; no wallet seed phrase or private key is needed.\n")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--evidence-root", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args(argv)
    try:
        m = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = assess(m, args.evidence_root)
        if args.out.exists() and any(args.out.iterdir()):
            raise AuditError("Output directory must be empty (no overwrite)")
        args.out.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        (args.out / "assessment.json").write_text(raw, encoding="utf-8")
        (args.out / "assessment.md").write_text(markdown(result), encoding="utf-8")
        print(f"{result['evidence_gate']} | risk={result['risk_screen']} | SHA256(report)={hashlib.sha256(raw.encode()).hexdigest()}")
        return 0 if result["evidence_gate"] == "PASS" else 2
    except (AuditError, OSError, ValueError, json.JSONDecodeError) as e:
        print(f"FAIL | {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
