# Cross-agent prompt continuity

## Current acceptance status — 2026-10-25
Documentation revision: post-cutover-1; protocol semantics remain 2.1.0.

The Git-state / GD-project implementation is active. GPT ↔ ordinary Claude continuity achieved the separately reviewed CUTOVER_PASS on 2026-10-25.
Evidence: CROSS_AGENT_TEST CHECKPOINT_PASS revision 35, commit 7eb4c0e0f2a77153feceb05efbdd632f38c21e03, successful CI run 40202011072, and the private immutable acceptance report/verdict resolved through the canonical private Entry Point.
The schema-valid deployment=ACTIVE_ACCEPTANCE_PENDING remains unchanged: it is an operational enum, not the acceptance verdict and not a revocation of CUTOVER_PASS.
Per-turn fresh bootstrap, Git operational authority, private GD project/method authority, run ownership, conditional writes, independent read-back and STOP/RECONCILE remain mandatory. Both transports A/B and all nine B invariants remain unchanged.
Cursor, individual Miro/GS/Archi runtimes and business acceptance are outside this verdict. CUTOVER_PASS is not VZP customer architecture approval.
Acceptance test procedures below remain the evidence standard; they do not reopen or require repetition of accepted tests without a newly evidenced defect.

Start with [PROTOCOL.md](PROTOCOL.md), then [state.json](state.json) and
[PROMPT_DRIVEN_ACCEPTANCE.md](PROMPT_DRIVEN_ACCEPTANCE.md).

Git owns operational state. Private Google Drive owns project materials and
private context. Both ordinary ChatGPT and ordinary claude.ai act only on their
own user prompts. No hooks. Cursor NOT TESTED. The implementation is active;
GPT → Claude → fresh GPT acceptance is recorded in the current status below.

`prompt_state.py` is the current strict transition guard. `state_cli.py` retains
the conditional GitHub backend. Legacy v1/hook docs and tests are historical,
not current operating instructions. Read the private Entry Point for private
locations; none are published here.
