# Prompt-driven GPT ↔ ordinary Claude — test contract

Status: PROCEDURE_READY / CLAUDE_STANDARD_CHAT_LIVE_NOT_TESTED / PILOT_NOT_CUTOVER (2026-10-25).

This supersedes Claude Code hook execution as a mandatory acceptance condition.
The existing Claude Code tests are optional implementation-specific checks.

## Test preconditions
- Both agents have real authenticated access to required **private** Google Drive canonical records and their supported read/write workflow, plus relevant native target services.
- Private Project State, Work Log, Decision Log, Write Control and immutable last handoff are live and consistent; a separate public GitHub pilot projection is not the canonical work source.
- Test only a disposable `CROSS_AGENT_TEST`-equivalent isolated scope and do not edit business evidence, Miro, Slides, Archi or any real VZP client decision. Observe current platform-specific writer controls.
- Capture revision, timestamp, file ID or permitted private link and native readback evidence without leaking it into the public repo.

## Test A — GPT ordinary prompt
Prompt: "Pokračuj ve VZP testovací kontinuitě. Ověř poslední otevřenou práci z kanonického stavu; nic nezapisuj."
Expected: mandatory fresh methodology + GD state/handoff read and exact recoverable OPEN/next action. Do not paste status into next tool's prompt.

## Test B — standard Claude (claude.ai), two separate ordinary prompts
1. "Pokračuj v poslední otevřené práci projektu VZP. Nic nezapisuj; dolož, odkud znáš aktuální stav a další krok."
2. "Pokračuj podle aktuálního projektu VZP a ověř, zda se stav od předchozího promptu změnil. Nyní jen čti."

Expected: real authenticated GD reads on BOTH turns; same state pointer + refreshed revisions; not a pasted GPT/Claude transcript, no Claude Code execution, and no reliance on UserPromptSubmit or SessionStart.

## Test C — isolated Claude write
After authenticating both turns and checking ownership, let Claude record a harmless scoped OPEN → verified checkpoint; independently read the new checkpoint, native test artifact if applicable, Work Log and State pointer. Wrong owner or stale baseline must STOP without changing data. Failure is not automatically READY.

## Test D — ordinary GPT takeover
In a NEW ordinary GPT prompt: "Pokračuj v poslední testovací práci VZP." GPT must independently recover Claude's last persisted work and next safe action from canonical private GD **without passing Claude's answer manually**. Verify source/native revision and record acceptance evidence.

## Outcomes
- `PROMPT_CONTINUITY_DESIGN_PASS`: reviewed written protocol, optional code/tests/CI as appropriate; proves design only.
- `GPT_PROMPT_DRIVEN_PASS`: GPT actual tool-based read, controlled write and independent readback.
- `CLAUDE_STANDARD_CHAT_PASS`: Claude **standard chat** actually completes required private-source read/write twice and independent readback.
- `GPT_CLAUDE_CONTINUITY_PASS`: full A–D chain and negative/recovery tests pass in exact scope.
- `HOOKS_NOT_REQUIRED`: a design assertion, not a test result.
- `PILOT_NOT_CUTOVER`: until cross-product acceptance plus matching private GD canonical governance publication.
- Future Cursor acceptance is separate, not a condition for the two-agent scoped goal.

A product connector supporting READ but not WRITE may yield `READ_PASS / WRITE_BLOCKED`; do not workaround by publishing private content to public GitHub. No model may infer another product's real execution from CI/unit tests or its own simulated response.
