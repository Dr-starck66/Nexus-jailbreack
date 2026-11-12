# Threat model · `worse_query` · 12 November 2026

## Evidence classification

| Statement | Grade | Reason |
|---|---|---|
| `forcequitOS/worse_query` describes inter-app container access on iOS 26/27 | PUBLIC SOURCE | https://github.com/forcequitOS/worse_query |
| Binance warned on 10 Nov about wallet secrets stored in readable files | REPORTED | https://www.bleepingcomputer.com/news/security/binance-warns-of-ios-flaw-that-could-leak-crypto-wallet-secrets/ |
| Fix publicly identified in iOS 27.2.1 for `worse_query` | UNVERIFIED | https://support.apple.com/en-us/149715 |
| Wallet theft in the wild using `worse_query` | UNVERIFIED | https://crypto.news/binance-ios-worse-query-vulnerability-crypto-wallets/ |
| Any particular wallet exposed or patched | UNVERIFIED | Requires app-specific evidence and consent |
| ASTRA local evidence checker / synthetic negative controls | PASS (local) | `python3 -m unittest discover -s tests -v`; *not* iOS verification |

## Trust boundaries

Attacker prerequisite: an untrusted app runs on a vulnerable iOS device and can trigger the published sandbox escape. The threatened boundary is **local application file access**, not automatic extraction of Keychain or Secure Enclave secrets. Content that remains encrypted with an independently protected key may not be recoverable. Device lock state, file-protection class, app lifecycle, backups and App Groups change the outcome.

We **do not** build or run the public exploit here, read live app containers, collect keys, defeat Keychain protections or assert arbitrary code execution. The manifest is a scoping and evidence-hygiene tool, not a technical verification of the target implementation.

## Client assessment protocol (requires written authorization)

1. Record in-scope organization, bundle ID, exact app build, iOS build, device type, contact, authorization reference, test dates, exclusions and emergency stop.
2. Use owner-furnished sanitized design artefacts; record origin, timestamps, export process, SHA-256 and retention. Never ingest seed phrases, login details, or real customer files.
3. Reconcile claims against code/configuration and the threat surface; obtain independent review of sensitive-storage design and logs.
4. On disposable device only, with non-funded fixture wallet and separate test accounts, validate authorized hypotheses; record both positive and negative results. Stop on unexpected data access.
5. Report with evidence provenance, severity reasoning, reproducer limited to consented environment, remediation owner and post-fix retest. Use private coordinated disclosure for new vulnerabilities.

## Example remediations to consider, not universal guarantees

- Minimize plaintext secrets, avoid putting recovery phrases in app files, caches, screenshots, analytics or logs.
- Prefer platform-supported Keychain and Secure Enclave where the required design supports them; validate actual entitlement, accessibility and key-lifecycle behavior rather than assuming safety.
- Restrict App Group sharing and backups to what is essential; use authenticated encryption with independent key protection when storage is unavoidable.
- Verify threat scenarios after changes against the actual iOS builds, and avoid describing local hashing as an exploit mitigation.

## Scope and distribution

Source-only public technical notes; no 0-day exploit code redistributed. This repository may be shared for discussion, but do not publish confidential partner artefacts or security findings without the owner's disclosure approval. All client deliverables must clearly separate `PASS`, `PARTIAL`, `FAIL`, `UNVERIFIED` and negative controls.