# Partner briefing & outreach pack · ASTRA NEXUS Ω

**12 November 2026 | Version 0.1 | Status: partner-ready for scoping, NOT iOS-device validated**

## Positioning (English — reusable verbatim)

**ASTRA NEXUS Ω — Evidence-first mobile wallet security research.** Following the public `worse_query` iOS sandbox-escape disclosure, we developed a small zero-cost, offline evidence-integrity gate for the review of wallet storage controls. Our published lab tests verify scope refusal, SHA-256 integrity, negative controls and the avoidance of false security assurances. We have **not** demonstrated exploitation of any third-party wallet. We seek one authorized technical partner to co-design a strictly scoped assessment on a disposable iOS device using fictitious assets, and independently validate the methodology against OWASP MASVS.

## Offer (proposal, not an agreed contract)

- **Discovery:** technical discussion on scope, test OS/build, authorized app build, allowed evidence and independent review.
- **Fixed-scope pilot:** one app, one iOS build, a disposable test device, non-funded wallet, pre-agreed five storage controls; share a concise audit with hashes, limitations, remedies and re-test criteria.
- **Commercial term:** price and liability to be negotiated only after an authorized mandate; no guarantee of findings or sales. No new paid hosting/subscriptions required for the current evidence gate.

## Ranked partner candidates — verified *official* channels

1. **Ledger Donjon** — primary scientific collaboration and technical peer review. Official `donjon@ledger.fr`; https://donjon.ledger.com/contact/ . Do **not** use this address to report a Ledger vulnerability; use their bug bounty for that.
2. **Trail of Bits** — research/methodology review and potential commercial collaboration. Official contact form: https://trailofbits.com/contact/ . No unverified direct address asserted.
3. **OWASP MAS** — methodology community rather than a wallet purchasing organization. Official project https://owasp.org/projects/mobile-application-security/ ; publicly listed project leaders on the official page. Ask for peer review, not endorsement.
4. **Zellic** — possible technical peer review / joint pilot; official services/contact funnel https://www.zellic.io/services . No verified individual mailbox.
5. **Trust Wallet / Binance** — **not** a sales outreach via vulnerability channels. For an original, substantiated, privately disclosed flaw only, use https://github.com/TrustWallet/wallet-core/security/policy and the linked Binance Bugcrowd program. Any commercial approach requires a different approved business channel.
6. **Apple Product Security** — ONLY if ASTRA obtains independently new, authorized technical evidence. Report through https://security.apple.com/bounty/guidelines ; do not file a bounty claim based on another researcher's published PoC or synthetic tests.

**Special case:** MetaMask's official security program page currently says its HackerOne program is temporarily paused and does not review submissions outside it: https://metamask.com/security/metamask-security-program . Do not imply an active bounty route or send an unsolicited vulnerability claim.

## Initial email — Ledger Donjon (no premature claims)

**To:** donjon@ledger.fr  
**Subject:** Research collaboration proposal — reproducible iOS wallet storage evidence gate (ASTRA NEXUS Ω)

Hello Ledger Donjon team,

I'm developing ASTRA NEXUS Ω, a small evidence-first security methodology focused on sensitive-data storage in iOS wallet applications, prompted by the publicly disclosed `worse_query` sandbox escape.

We have a zero-dependency offline evidence checker, synthetic fixtures and passing negative-control tests covering scope authorization, SHA-256 integrity and false-assurance prevention. We have **not** tested or identified a vulnerability in Ledger or any other third-party wallet.

Would your team be open to a short technical review of this methodology, or a discussion about a narrowly scoped, authorized pilot on a disposable test environment? We can share the source, test evidence and a concise threat model in advance. No customer data, real wallet keys or unpublished exploit is involved.

Best regards,  
ASTRA NEXUS Ω research

## Initial contact note — Trail of Bits (official form)

**Subject:** Technical peer review / authorized mobile wallet security pilot

We're building ASTRA NEXUS Ω, an offline evidence-integrity workflow to help distinguish reproducible wallet data-storage observations from claims that remain unverified after the public `worse_query` iOS disclosure. A 13-test synthetic harness is available, with explicit safeguards against scope escape and false green reports. We are looking for an independent technical reviewer or a jointly scoped pilot with authorized iOS devices and disposable assets. This is not a claim that any named wallet has been exploited. May we send a short technical brief and repository link to the appropriate team?

## Contacting guard

Never send a vulnerability allegation based only on this dossier. Never send the same outreach twice. Check recipients, privacy preference and prior Gmail thread before sending. Until a reply is obtained, partner interest, purchase intent, actual iOS testing and real-world exploit protection all remain **UNVERIFIED**.