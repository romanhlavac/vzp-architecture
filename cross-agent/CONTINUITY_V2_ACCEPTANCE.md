> HISTORICAL / SUPERSEDED. Current operation: [PROTOCOL.md](PROTOCOL.md).
> Hook and GD-state requirements below are not active gates. Old PASS is historical only.

# Cross-agent continuity v2 — live acceptance checkpoint (2026-10-25)

Scope: user wants free alternating ordinary prompts across GPT and Claude without manual handoff and without triggering the other agent.

## Actual implementation
- `cross-agent/continuity_v2.py`: validated agent-neutral public status codes and CAS-based write.
- `cross-agent/prompt_context.py` + `.claude/settings.json`: Claude Code `UserPromptSubmit` read-only context injection, in addition to existing SessionStart/Stop hooks.
- `tests/test_continuity_v2.py` and `tests/test_prompt_context.py`: tests of reducer, conflict gates, safe context injection and failure without leaking exception details.
- `cross-agent/CONTINUITY_V2.md`: explicit security boundary and unsatisfied gates.

## Native GPT GitHub test
- Baseline state revision 11 and blob `eab8ebe1f35fbdb5207d3c93ad7c9b6deac88e51`.
- Real GPT connected GitHub write: commit `d875604ddc272e23f6fc54521c3bc06b43cc5d67`.
- After independent read-back: `state_revision=12`, blob `a4ea02fd0a1db81796c67f1e8721b17a46d4a015`, `continuity.latest_workstream=CROSS_AGENT_TEST`, last `work_code=AUTO_CONTINUITY_V2_GPT_PILOT`, `next_code=CLAUDE_NATIVE_PROMPT_TEST`, `phase=OPEN`.
- `CROSS_AGENT_TEST.owner=null`, existing other workstream objects unchanged; no client artifact altered.
- Previous native GitHub 409 stale-SHA test remains documented in `PILOT_ACCEPTANCE.md`.
- Preexisting 32-test CI success on run `40143369624` included 10 continuity reducer tests; a subsequent workflow run should validate the new prompt hook tests.

## Gates (do not inflate)
- `GPT_GITHUB_CONTINUITY_WRITE_READBACK = PASS`.
- `GITHUB_CI = PASS` — verified workflow run `40143553614` at `main` `0b95ca26f13143081c31756f9055306fe83e05c2`, **34/34 unittest PASS**. This is code-level acceptance, not Claude runtime acceptance.
- `CLAUDE_CODE_USER_PROMPT_SUBMIT_NATIVE = NOT_TESTED` (code/mock tests are not an actual Claude runtime execution).
- `CLAUDE_STANDARD_CHAT_AUTO_SYNC = NOT_ESTABLISHED`.
- `GPT_NATIVE_AUTO_PER_TURN_HOOK = NOT_ESTABLISHED`.
- `FULL_SEMANTIC_CONTEXT_SYNC = NOT_IMPLEMENTED`: public-only status codes cannot preserve confidential task reasoning or private chat history.
- `GPT_CLAUDE_ARBITRARY_ALTERNATION = NOT_ACCEPTED`.
- `GD_OPERATING_STATE_CUTOVER = NOT_EXECUTED`. Legacy GD rev 2 remains canonical; Github `PILOT_NOT_CUTOVER`.

## Required external validation
Run actual authenticated Claude Code with this repository and inspect UserPromptSubmit's automatic injection of revision >= 12 and latest GPT checkpoint; perform separate native status publication without manually instructing handoff. GPT must then independently read and continue a genuine artifact work unit. A normal Claude.ai chat requires separate supported product integration; a Claude Code hook cannot prove that path.

## Demo 4 native Claude Code execution contract
- Native two-turn and GPT read-back test: [CLAUDE_CODE_NATIVE_ACCEPTANCE.md](CLAUDE_CODE_NATIVE_ACCEPTANCE.md).
- Run it in actual **Claude Code**, not by locally calling a Python script or pasting expected metadata into a chat.
- Ordinary claude.ai chat and ordinary ChatGPT do **not** gain OS-level hooks merely from these repository files.
- Until actual native run evidence and safe shared private semantic working context are verified, `PILOT_NOT_CUTOVER` remains mandatory.
