# NEXUS / ASTRA Ω — Supply-chain and Python startup gate

**Status:** offline static control, not a deployed runtime sandbox. This module extends the existing prompt-testing project with a security component; it does **not** turn a prompt generator into a protected agent runner.

## Why this gate exists

On 17 November 2026, `agent-framework` 1.26.1 and 1.26.2 were distributed through the official PyPI package name with malicious Python startup `.pth` hooks. The compromised versions are identified in [GHSA-764m-3ppc-5m73](https://github.com/advisories/GHSA-764m-3ppc-5m73). A startup hook can execute before the Python application imports its dependencies. Prompt-injection detection alone cannot stop it.

## Architecture and trust boundary

```text
Untrusted dependency/manifests ─┐
Python site-packages tree ──────┤ (read-only, Node.js, no Python startup)
                                 ▼
                        NEXUS supply-chain gate
                          ├─ FAIL: deny startup + incident response
                          ├─ PARTIAL: deny unattended startup, review
                          └─ PASS_SCOPED: allow only the inspected target scope
                                 ▼
               *External* agent runtime adapter (not wired here)
                                 ▼
            Prompt/tool policy + least privilege + secret isolation
```

**Fail-closed integration contract:** A future authorized executor must invoke this gate **before** starting Python, reject `FAIL` and `PARTIAL`, and pass only if `PASS_SCOPED` covers the exact environment it will use. A clean source scan is *not* a clean runtime scan. A clean runtime scan does *not* prove every cache, container image, machine or other agent is clean.

## Use (no network or extra dependencies)

From the NEXUS repository:

```bash
npm run test:security
npm run security:gate -- --source ./my-python-project
npm run security:gate -- --runtime /opt/venv/lib/python3.12/site-packages
npm run security:gate -- --source ./my-python-project --runtime /opt/venv/lib/python3.12/site-packages
```

* `--source`: scans only known dependency files (`requirements*.txt`, Poetry/uv locks, Pipfile locks, pyproject, setup, environment YAML), skipping virtual environments, `node_modules`, hidden caches, build outputs and `.env` files.
* `--runtime`: scans a supplied *site-packages* or *dist-packages* directory, without running Python or pip. Detects known artifact names (`agent_framework_meta.pth`, `agent_framework_meta/_telemetry.py`, `af_runtime_diag.pth`, `af_runtime_diag.py`), executable `.pth` hooks requiring review, and installed `agent-framework` dist-info metadata.
* The gate emits a **JSON report** without printing dependency file contents, environment variables, credentials or `.pth` code. It never follows symlinks. It does not fetch threat intelligence dynamically; it requires a documented rules update for new incidents.
* Exit **0** = `PASS_SCOPED`, **1** = `PARTIAL`, **2** = `FAIL`. A malformed invocation or missing/unreadable target is `PARTIAL` and exits 1. The gate has hard limits on number/size of files.

`PASS_SCOPED` means *no known red flag within the explicitly scanned scope*. It is not a general security certification, a signature proof, or evidence of live deployment. Dependency ranges that may resolve to a compromised version are `PARTIAL` until the installed version is checked.

## Incident response, if FAIL or actual historical installation

1. Stop the affected execution path and isolate the environment without launching Python or `pip` (running them may trigger the hook).
2. Treat reachable cloud/API tokens and CI credentials as potentially exposed. Revoke/rotate them through their authorized providers; review provider activity and audit logs.
3. Rebuild affected images, runners and caches from a trusted base, after revocation. Do not rely on `pip uninstall` as the sole response.
4. Use only a version supported by a current vendor advisory and verify wheel hashes/provenance; the last clean version documented for this incident was 1.26.0 at disclosure. Check the current official advisory before redeployment.
5. Run the gate on the rebuilt exact runtime, audit user-visible functions, and preserve a sanitized evidence report. Never paste raw secrets into issues or logs.

## Current boundaries (2026-11-20)

The NEXUS repo is a React/TypeScript prompt-building interface, not a Python agent executor. The gate is a manually invokable offline component here, and the existing site/build/workflows remain unchanged. No CI workflow, scheduler, infrastructure, billing item or automatic secret rotation has been created. Integration into a real agent executor and provider-hosted CI/runtime verification are **UNVERIFIED**.

Provenance: functional extension of the read-only ASTRA scanner proposed at [ASTRA PR #307](https://github.com/Dr-starck66/indexation/pull/307). The Python-installed-runtime checks and fail-closed CLI are NEXUS-specific additions. Tests use synthetic fixtures and do not install malware.
