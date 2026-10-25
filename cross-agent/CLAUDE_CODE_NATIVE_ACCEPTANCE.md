> HISTORICAL / SUPERSEDED. Current operation: [PROTOCOL.md](PROTOCOL.md).
> Hook and GD-state requirements below are not active gates. Old PASS is historical only.

# Demo 4 — Native Claude Code acceptance (GPT → Claude → GPT)

Status: **PROCEDURE READY / CLAUDE CODE NATIVE NOT TESTED / PILOT_NOT_CUTOVER**.
This is a public, non-confidential execution contract, **not** evidence that a Claude runtime ran.

## Scope and authority
- Test the *actual Claude Code* `UserPromptSubmit` hook from `.claude/settings.json` while Claude Code is running inside an authenticated local checkout of this repository.
- Read-only `prompt_context.py` must automatically inject live public metadata on an **ordinary user prompt**. Manual execution of `python3 cross-agent/prompt_context.py`, mocked unit tests, CI or text pasted into the prompt **cannot** establish native PASS.
- The canonical VZP private operational state remains Google Drive. Until explicit accepted cutover, `cross-agent/state.json.storage_mode` must remain `PILOT_NOT_CUTOVER`; it is only a public metadata pilot.
- Never store prompts, private Drive URLs, VZP client evidence, transcript text, runtime tokens or internal artifact IDs in this public repo. Do not print environment variables.

## Prerequisites
1. Open a local repository checkout in Claude **Code** (not only claude.ai). Refresh `main`; record the exact commit SHA and clean/modified local status.
2. Confirm the actual project hook is trusted/enabled in Claude Code. Check `.claude/settings.json` has `UserPromptSubmit → python3 "${CLAUDE_PROJECT_DIR}/cross-agent/prompt_context.py"`, in addition to `SessionStart` and `Stop`.
3. Confirm authenticated network access to GitHub; independently read current `cross-agent/state.json` and its blob SHA. Confirm `storage_mode=PILOT_NOT_CUTOVER`, `workstreams.CROSS_AGENT_TEST.owner=null`. If not: **STOP/RECONCILE**.
4. Confirm separately that Claude can authenticate to the canonical **private** Google Drive and perform complete fresh methodology bootstrap. A working GitHub hook **does not** prove this.

## Native two-turn test — no manual handoff instruction
A. With Claude Code running in the project, send an **ordinary task prompt** such as:
   “Pokračuj v poslední rozpracované testovací práci projektu VZP. Neprováděj žádný zápis; řekni, co je otevřené a z jakého aktuálního zdroje to víš.”
   Do NOT paste the expected revision, scope, work/next codes or this expected-state table into the Claude prompt.
   Verify from Claude Code’s **actual runtime hook trace** that `UserPromptSubmit` invoked the configured script, and that Claude's resulting context/readback independently identifies the GitHub revision, latest workstream, phase, `work_code`, `next_code`, and `source_of_truth=GD_OPERATING_STATE`. Merely inspecting the hook configuration is insufficient.
B. End the turn. Start a second, separate ordinary Claude Code turn. Require a **fresh** read of GitHub state and GD operational status. Reconfirm no cached/unverified status or unsolicited production write.
C. Only after these reads, authorize a **controlled isolated CROSS_AGENT_TEST** work unit; claim ownership at the current exact revision and publish a safe public-only test context/checkpoint through existing CAS-protected code. Read back the updated state and release ownership through an accepted handoff. Do not publish a `VERIFIED` result without evidence.
D. In a separate ordinary GPT turn, independently read GitHub current blob/revision, recover the just-created Claude status **without copying its text from Claude chat**, resolve the private working detail through authorized GD, and show a valid next step.

## Negative and recovery tests
- Old `state_revision` or stale blob SHA → server/agent **STOP without mutation**; distinguish native GitHub CAS failure from local reducer tests.
- Foreign `CROSS_AGENT_TEST.owner` → **FOREIGN_WRITER_STOP** without mutation.
- Missing GitHub/Drive access, incomplete hook invocation or missing readback → `BOOTSTRAP INCOMPLETE` or `NOT TESTED`, never success.
- Verify partial/interrupted publish goes to `RECOVERY_OPEN` or stops for manual reconciliation, never last-write-wins.

## Evidence required for each PASS
- Exact product and runtime (Claude Code version / actual hook enabled), UTC times, GitHub commit/blob SHA, state before/after, and the actual runtime hook execution trace.
- Which *ordinary* prompt was used (sanitized description only), automatically recovered codes (no private prompt text), observed next work unit, write/readback checks, failed-write error codes and owner reconciliation.
- Exact private GD **document identifiers only in authorized private evidence**, not this public repository.
- GPT readback after Claude as an independent tool operation and accepted work continuation.

## Gate results
- `GPT_GITHUB_CONTINUITY_WRITE_READBACK`: PASS from prior recorded evidence.
- `GITHUB_CI`: 34/34 tests PASS in run 40143553614 at commit 0b95ca26f13143081c31756f9055306fe83e05c2 (historical baseline; rerun after code changes).
- `CLAUDE_CODE_USER_PROMPT_SUBMIT_NATIVE`: **NOT TESTED** until this procedure is executed in Claude Code.
- `CLAUDE_STANDARD_CHAT_AUTO_SYNC`: **NOT ESTABLISHED**; Claude Code hooks do not run inside ordinary claude.ai chats.
- `GPT_NATIVE_AUTO_PER_TURN_HOOK`: **NOT ESTABLISHED** in ordinary ChatGPT.
- `PRIVATE_SEMANTIC_CONTEXT_SHARED`: **OPEN**; GitHub public codes are not full CES DEMO context.
- `GPT_CLAUDE_END_TO_END_AUTO_HANDOFF`: **NOT TESTED**.
- `CUTOVER`: **PROHIBITED** until all applicable native gates and private-context safety pass.
