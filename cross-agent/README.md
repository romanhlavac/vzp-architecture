# Cross-agent prompt continuity

Start with [PROTOCOL.md](PROTOCOL.md), then [state.json](state.json) and
[PROMPT_DRIVEN_ACCEPTANCE.md](PROMPT_DRIVEN_ACCEPTANCE.md).

Git owns operational state. Private Google Drive owns project materials and
private context. Both ordinary ChatGPT and ordinary claude.ai act only on their
own user prompts. No hooks. Cursor NOT TESTED. The implementation is active;
real GPT → Claude → fresh GPT acceptance remains pending until evidenced.

`prompt_state.py` is the current strict transition guard. `state_cli.py` retains
the conditional GitHub backend. Legacy v1/hook docs and tests are historical,
not current operating instructions. Read the private Entry Point for private
locations; none are published here.
