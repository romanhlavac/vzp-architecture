# VZP cross-agent continuity protocol — corrected design

**Status: OWNER_WORKING / PROMPT_DRIVEN_DESIGN / PILOT_NOT_CUTOVER (2026-10-25).**

The active target is symmetric **prompt-driven continuity** across ordinary ChatGPT, ordinary Claude and future Cursor. See [PROMPT_DRIVEN_CONTINUITY.md](PROMPT_DRIVEN_CONTINUITY.md) for the full normative design proposal and [PROMPT_DRIVEN_ACCEPTANCE.md](PROMPT_DRIVEN_ACCEPTANCE.md) for the real-product test.

**No Claude Code hooks, GPT lifecycle hooks, inter-agent invocation, local OS runtime, or background process are required.** Hooks are optional conveniences. They may not be mandatory gates for the user's cross-tool continuity requirement.

Current authority is the **private Google Drive Project State / Work Log / Decision Log / Write Control / immutable handoffs**, referenced by the canonical Drive Entry Point. This repository remains public code/CI and a sanitized optional status projection. The public `cross-agent/state.json` is **PILOT_NOT_CUTOVER** and must not override confidential canonical GD state, Source Index or native live artifact masters. Do not archive GD operational registries to promote public GitHub.

Per user prompt, each agent performs the same chain:
`full fresh bootstrap -> private GD operational resume -> live artifact read -> scoped single-writer/staleness check -> work -> verified native readback -> private GD checkpoint/Work Log/State update`.
Only material progress needs a checkpoint. Paused/failed work stays OPEN/RECOVERY; no false READY. Soft writer control is not atomic; conflicts stop.

Acceptance: actual ordinary Claude chat must read private GD on two separate prompts, write/read back a harmless test checkpoint when authorized, then ordinary GPT must independently resume from it. No manually pasted prior answer; no hook runtime. Stale revision, foreign writer and recovery remain required fail-closed tests. Cursor is future separate onboarding.

**Supersession:** Previous sections of this file proposing mandatory Claude Code native hooks, full public-GitHub state cutover and Cursor-before-two-agent acceptance are historical. Git history retains them; they are not current target requirements. The private GD canonical operating protocol still requires in-place update and acceptance before claiming final implementation cutover.
