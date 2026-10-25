> HISTORICAL / SUPERSEDED. Current operation: [PROTOCOL.md](PROTOCOL.md).
> Hook and GD-state requirements below are not active gates. Old PASS is historical only.

# VZP continuity v2 — pilot mechanisms versus accepted goal

**Status: HISTORICAL_IMPLEMENTATION_PILOT / PILOT_NOT_CUTOVER.**

The original public `continuity_v2.py` emits safe status codes, `prompt_context.py` uses a Claude Code hook, and `auto_sync.py` exercises CLI/git. These remain valid optional engineering experiments but **not requirements** for user-requested prompt-driven continuity.

**Current target:** [PROMPT_DRIVEN_CONTINUITY.md](PROMPT_DRIVEN_CONTINUITY.md) and [PROMPT_DRIVEN_ACCEPTANCE.md](PROMPT_DRIVEN_ACCEPTANCE.md).

Each ordinary ChatGPT, Claude or later Cursor prompt independently loads current private GD operating state, relevant evidence and live native artifacts, does authorized work, then records material changes + next step to private canonical checkpoints after independent readback. No hooks or agent-to-agent calls. Private GD state remains canonical; public GitHub state remains `PILOT_NOT_CUTOVER`. The public status codes cannot and must not carry sensitive semantic summaries.

The earlier clause requiring native Claude Code UserPromptSubmit and automatic GPT product lifecycle hooks for the main acceptance has been SUPERSEDED by the project owner's clarified objective. Previous unit tests and green CI validate code only. Historical evidence remains in repository history and older acceptance reports.

Actual standard-Claude supported connector reads/writes, GPT resumption and conflict/recovery must be tested before two-agent operational PASS. Cursor can be validated separately later.
