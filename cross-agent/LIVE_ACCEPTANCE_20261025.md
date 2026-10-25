# Live prompt-driven acceptance — 2026-10-25

Implementation: bb85cba8ed589381f7a8f2b1d10c3bb5d6cd6c37.
Implementation CI: [40189206274](https://github.com/romanhlavac/vzp-architecture/actions/runs/40189206274), success.
45 unit tests pass, including retained historical regression fixtures and 11 current-state tests.
Git state authority is deployed; private GD governance has same-ID raw-byte read-back and manifest-last verification.
No hooks. ACTIVE_ACCEPTANCE_PENDING. No CUTOVER_PASS.

| Gate | Result | Evidence |
|---|---|---|
| A1 GPT actual read/write/read-back | PASS | Actual GitHub connector writes; commits below |
| A2 stale SHA | PASS | Actual GitHub Contents update rejected HTTP 409 on isolated branch; full content/blob unchanged |
| A2 stale revision | PASS | Executed current guard against fresh remote fixture; STALE_REVISION_STOP, remote unchanged |
| A2 foreign writer | PASS | Executed guard with distinct GPT run against persisted GPT-owned fixture; FOREIGN_WRITER_STOP, remote unchanged |
| A2 recovery | PASS | Persisted RECOVERY_OPEN; attempted normal completion blocked RECOVERY_STOP; remote unchanged; test-only authorized reconciliation |
| GD governance | PASS | Same IDs, raw-byte SHA-256/size read-back for 12 documents; manifest last; private audit contains identifiers |
| B1 ordinary Claude two reads | NOT TESTED | Current Cloud Browser showed claude.ai/login; historical reports are not this gate |
| B2 ordinary Claude write/read-back | NOT TESTED | Must be actual ordinary Claude execution |
| B3 ordinary Claude guards | NOT TESTED | Manual runbook ready |
| C1 NEW GPT return prompt | NOT TESTED | Requires real Claude checkpoint first |
| D full chain | BLOCKED | External ordinary-Claude phase and fresh GPT return pending |
| Cursor | NOT TESTED | Nonblocking |

## Actual isolated branch evidence

Branch: cross-agent-test/prompt-20261025. No business artifacts changed.
The synthetic foreign run is a test input, not a simulated Claude actor.

- cross-agent-test/prompt-20261025 / CLAIM / revision 16 / `e3355c9ee80478e233ace0cd4959ebb07b08333c` / full read-back PASS
- cross-agent-test/prompt-20261025 / CHECKPOINT_OPEN / revision 17 / `aa41f646381f1ae24d7addf05a061ac1fb15138e` / full read-back PASS
- cross-agent-test/prompt-20261025 / RECOVERY_OPEN / revision 18 / `67a0cb2b9ff1ba8bf41f015dedb273684c0db434` / full read-back PASS
- cross-agent-test/prompt-20261025 / RECONCILE / revision 19 / `df2240f64cd263ecdd6834131ec370c029a95838` / full read-back PASS
- main / CLAIM / revision 17 / `433655eb8556a130418116d367c678abadf6e611` / full read-back PASS
- main / CHECKPOINT_OPEN / revision 18 / `fc3ecd37129941c0c953d93b9899b53ea14bdea1` / full read-back PASS
- main / HANDOFF_OPEN / revision 19 / `ac2bea2832c48fec1586093b10e6c918388c6892` / full read-back PASS

Stale SHA used b27bc14d486ea4d42c5c8c5261d10bf598467728 after claim.
Remote remained 70a592709cfe52bc81b986e5fd441d5c3f5ab56e after HTTP 409,
after the stale-revision guard and after the foreign-run guard.
Recovery fixture remained 08ef65fe377b411b63513e7d2e4a5d7bf47b8426 after refusal.

## Limits and next action

SHA conflict is server-side. Owner/revision/recovery rules are cooperative client
guards with CI verification; they are not GitHub path-level authorization or an
atomic native-artifact lock. CI is not a prepublication confidentiality filter.
Existing main is not branch-protected; direct authorized writers must follow
this protocol, and CI failures mean STOP/RECONCILE. Do not claim native/visual
acceptance from schema or CI alone.

Follow [PROMPT_DRIVEN_ACCEPTANCE.md](PROMPT_DRIVEN_ACCEPTANCE.md) in ordinary
claude.ai on two separate prompts, then a NEW GPT prompt. Current Git state
selects the private context; the manual prompt must not carry the task payload.
The live GD Claude adapter was updated; product Project settings are not changed
automatically. No full acceptance until the actual tool execution is evidenced.
