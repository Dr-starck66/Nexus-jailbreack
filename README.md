<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/7f0e6aee-6471-4435-955a-6914601bf21a

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## NEXUS Supply-Chain Guard Ω (offline security module)

A separate read-only Node.js gate detects Python agent dependency exposure to the compromised Microsoft `agent-framework` 1.26.1/1.26.2 releases, known executable `.pth` startup hooks and suspect installed metadata. **No Python interpreter is started.** It does not replace prompt-injection tests or secure sandboxing.

- Tests: `npm run test:security`
- Audit dependency files: `npm run security:gate -- --source /path/to/python/project`
- Audit an installed environment: `npm run security:gate -- --runtime /path/to/site-packages`
- Remediation, scope, exit codes and limits: [`security/SUPPLY_CHAIN.md`](security/SUPPLY_CHAIN.md)

This React prompt-generation app does not currently connect that gate to a deployed Python executor. Green source checks are not proof of safety of containers, hosted runners or credentials.
