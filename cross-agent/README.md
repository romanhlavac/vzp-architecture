# VZP cross-agent continuity

**Current baseline: prompt-driven design correction; PILOT_NOT_CUTOVER.**

Primary target: users may alternate ordinary prompts among ChatGPT and normal Claude, later Cursor, with each agent independently reading and writing the SAME authorized private Google Drive work state and native artifacts. **No agent triggers another and no Claude Code/ChatGPT lifecycle hook is mandatory.**

- [Current design / identical per-prompt algorithm](PROMPT_DRIVEN_CONTINUITY.md)
- [Standard Claude + GPT acceptance](PROMPT_DRIVEN_ACCEPTANCE.md)
- [Corrected protocol and source-of-truth](PROTOCOL.md)
- [Cutover checklist](CUTOVER_CHECKLIST.md)

## Authorities and limitations

Private GD operating registries / immutable handoffs remain **canonical**. GitHub is PUBLIC: code, tests, CI and optionally **sanitized projection only**. Current `cross-agent/state.json` rev 13 is an experimental projection (`PILOT_NOT_CUTOVER`) and MUST NOT replace the GD Project State. Source Index Sxx and native visual/artifact authorities remain unchanged.

Each agent must follow the same read → work → write → independent readback → checkpoint sequence when prompted. Project instructions can mandate this behavior; no tool fires without a user prompt and a model skipping tool calls cannot be assumed synchronized. Write conflicts or incomplete evidence => STOP/RECONCILE. Existing GD soft lock is not atomic CAS.

## Optional legacy components

`auto_sync.py`, `prompt_context.py`, `.claude/settings.json`, `continuity_v2.py`, `state_cli.py` and older acceptance documents are **experimental/optional** GitHub-pilot tooling and historical test evidence; they must not be interpreted as required for normal Claude chat. Their PASS outcomes are not proof of prompt-driven full GD continuity.

Do not copy private Drive links, prompts, transcripts, client material, evidence, secrets or restricted content to this public repository. No source migration or GD policy update is completed merely by publishing this design.
