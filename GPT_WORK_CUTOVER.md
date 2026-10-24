# Cutover runbook — GPT/Claude only

This request authorizes preparing two-agent continuity, **not** inventing a ChatGPT event hook or treating raw agent chat context as a shared durable document.

1. Preflight: fresh-read actual VZP Project Instructions, manifest, kernel, Source Index and relevant modules; then current GD operational state and latest handoff, live GH `main`, `state.json` and native artifacts. If drift -> `STOP/RECONCILE`.
2. Publish reviewed, public-safe overlay files to `romanhlavac/vzp-architecture`; GitHub Actions tests plus SHA readback must pass. No force updates. No client content.
3. Claude Code: verify actual SessionStart injection and Stop `CHECKPOINT_OPEN` in isolated `CROSS_AGENT_TEST`. A tokenless GH Contents API does not validate git push; verify the actual Git credential path.
4. GPT: verify actual GitHub state read, CLAIM and CHECKPOINT_PASS through connected GitHub tools, with exact commit SHAs and full read-back.
5. Complete GPT → Claude → GPT handoff, foreign-writer STOP, stale expected revision STOP and OPEN/recovery case. Check no native artifacts were modified in the synthetic test.
6. If all scoped gates PASS, publish a **single** new GitHub `ACTIVE_GPT_CLAUDE` state revision (preserve Cursor NOT_TESTED), then update the existing GD Project Skill, Quality Gates, Operating Protocol, Entry Point, Claude adapter and Skill Manifest in place with exact source IDs and hash read-back. Existing GDPR State/Log/Decision/Control become historical after verified pointer transition. Keep original 53 Sxx and all existing GD business evidence unchanged.
7. If any publish/read-back fails, remain `PILOT_NOT_CUTOVER` and do not claim fully automatic synchronization.

The original protocol expects Cursor to be tested for three-agent cutover. A separate **two-agent-scoped protocol change** must be authorized and consistently published before reducing that gate. This runbook cannot override the live GD baseline alone.
