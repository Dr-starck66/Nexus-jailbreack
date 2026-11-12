# ASTRA NEXUS Ω — Wallet Security Evidence Gate v0.1

**Read-only, offline, Python stdlib only · no real wallets or keys · no device exploitation · 0 € infrastructure.**

An auditable evidence-integrity gate for a narrowly scoped, owner-authorized review of iOS wallet data-at-rest protections following the public `worse_query` sandbox-escape disclosure. This is **not** the exploit, an iOS dynamic scanner, a wallet security certification, or proof that any named wallet is vulnerable.

## Provenance and limitations

- Public researcher PoC: <https://github.com/forcequitOS/worse_query>; iOS versions listed in the researcher's README are version claims from that repository, **not** device tests performed by ASTRA.
- Apple's 2026-11-09 advisory: <https://support.apple.com/en-us/149715>. Absence of an explicit `worse_query` fix in that advisory does not prove the absence of a fix.
- OWASP MASVS-STORAGE-1 / STORAGE-2, MASVS-PLATFORM and MASVS-CRYPTO are methodological references: <https://mas.owasp.org/MASVS/05-MASVS-STORAGE/>. This tool is **not** an OWASP-certified assessment.
- `PASS` on evidence means its file matches the submitted SHA-256; it does **not** mean that the assertion in the evidence is authentic, or that the application resists the vulnerability.
- The risk screen is a transparent **indicative triage only**. `LOWER_INDICATIVE_NOT_SAFE_CLAIM` must never be presented as a clean bill of health.

## What it does

1. Requires an explicit synthetic or written-authorized lab scope marker and a matching manifest.
2. Checks five declared, sanitised control facts: secret-storage pattern, backup exclusions, secret logging, shared App Group storage and complete file protection.
3. Refuses relative path traversal, symlink escapes, missing/malformed evidence hashes, oversized files (>128 KiB), unknown schemas, and unauthorized lab scopes.
4. Emits `assessment.json` and `assessment.md` without copying evidence contents, making network calls or touching wallet credentials.
5. Produces reproducible negative controls and always labels iOS-device validation `UNVERIFIED`.

## Reproduce locally (Python 3.10+)

```bash
python3 -m unittest discover -s tests -v
python3 src/audit.py \
  --manifest examples/manifest.synthetic.json \
  --evidence-root examples/evidence \
  --out /tmp/nexus-wallet-demo
sha256sum /tmp/nexus-wallet-demo/assessment.json
```

Exit codes: `0` all five evidence hashes valid; `2` incomplete evidence; `3` invalid scope, integrity or manifest (fail-closed). A hash check cannot establish truth or authenticity; additional manual/device verification is mandatory before client security assertions.

## Minimal controls

| Manifest fact | Purpose | Worst-case indicative exposure |
|---|---|---|
| `secret_storage` | Plaintext file vs encrypted file vs Keychain vs Secure Enclave | Plaintext file: high |
| `backup_exclusion` | Backup propagation | Coverage observation only |
| `secrets_in_logs` | Accidental logging of sensitive data | `true`: high |
| `shared_app_group_secrets` | Cross-app storage exposure | `true`: high |
| `file_protection_complete` | iOS file protection declaration | Not a guarantee against an unlocked-device sandbox escape |

**Authorization:** No testing of third-party apps, live systems, devices, accounts, or wallets without owner approval and a written scope. Never supply seed phrases, private keys, dumps containing credentials, customer data, or company secrets to this tool. Evidence should be pre-sanitized and contain only non-sensitive audit metadata.

## Professional pilot — deliverable boundaries

- **Phase A / existing:** offline evidence gate + source/threat-model notes + SHA-256 audit + risk matrix + negative controls.
- **Phase B / requires partner:** signed scope, test device with OS/build ID, disposable test wallet, isolated app builds, signed access to logs/configuration, controlled iOS reproduction if authorized, independent re-test and remediation review.
- **Deliverables to a partner:** methodology, immutable hashes, precise observations, contradictory evidence and blocked tests, prioritized remediations; no claims of CVE discovery or exploitation of a named wallet.

See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) and [docs/PARTNER_OUTREACH.md](docs/PARTNER_OUTREACH.md). Repository integration is **isolated** from the main NEXUS application; do not merge until reviewed. No GitHub Actions usage is required.