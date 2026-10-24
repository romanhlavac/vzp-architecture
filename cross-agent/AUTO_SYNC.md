# Cross-agent GPT / Claude Code integration — controlled pilot

## Current status

**PILOT_NOT_CUTOVER**. Publication/CI evidence is tracked separately from real Claude Code runtime acceptance. Existing GD operational state is canonical. The GitHub snapshot is a pilot (`PILOT_NOT_CUTOVER`).

## What is automatic after installation

- `SessionStart` on **Claude Code**, including a resumed session, reads actual GitHub `state.json` and injects revision/status into the session context. This does not replace mandatory fresh private Drive methodology, Source Index, or native target reads.
- `Stop` checks the explicitly selected `VZP_WORKSTREAM`. With `VZP_AUTO_SYNC_ENABLED=1` and owner `CLAUDE`, it publishes **CHECKPOINT_OPEN** via an isolated non-force Git push, never a false `READY_FOR_HANDOFF`.
- The `stop` hook does **not** store the chat transcript, source excerpts or full details of completed tasks. If no scope, no active ownership, no authenticated push, or a version conflict: no automatic cross-agent completion is claimed.
- `finish` requires `VZP_NATIVE_READBACK_PASS=1` (assertion made only after actual evidence review); it publishes `CHECKPOINT_PASS`, releases ownership and performs fresh read-back.
- In pilot mode, all writes are restricted to `CROSS_AGENT_TEST`. This must remain true until owner-authorized cutover.

## Installation

Copy `.claude/settings.json`, `cross-agent/auto_sync.py`, and `tests/test_auto_sync.py` into the same paths of `romanhlavac/vzp-architecture`. Claude Code must load the repository and run the hooks. A standard Claude chat does not automatically execute repository hooks.

Run tests:

    python3 -m unittest discover -s tests -v

For an **isolated test**, configure the Claude Code *runtime*, not GitHub files:

    export VZP_AUTO_SYNC_ENABLED=1
    export VZP_WORKSTREAM=CROSS_AGENT_TEST

Ownership must first be legitimately claimed under the current GitHub revision using the canonical state transition command. Never auto-claim an arbitrary workstream.

To publish a completed, independently validated checkpoint:

    export VZP_NATIVE_READBACK_PASS=1
    python3 cross-agent/auto_sync.py finish --workstream CROSS_AGENT_TEST

The flag is an operator/agent attestation, not cryptographic evidence. Actual native artifact read-back and links are mandatory for a meaningful business checkpoint.

## GPT side

ChatGPT Work/ChatGPT does **not** execute Claude repository hooks, and opening a chat does not automatically import another provider's private transcripts. GPT can fresh-read `state.json` with connected GitHub tools, and its VZP project operating instructions can require publication of verified checkpoints; a genuine product-level automatic on-turn hook has not been established.

## Security invariants

No restricted material, client documents, private Drive URLs, chat transcripts or credentials in this public repo. GitHub state is operational metadata only; Miro/GS/Archi and GD remain their own artifact authorities. Every cross-agent task must still select one writer and verify native artifact revisions.

## Acceptance still required

1. Publish this implementation to GitHub and verify exact commit/SHA plus CI.
2. Run actual Claude Code `SessionStart` and `Stop` in `CROSS_AGENT_TEST`, test conflict and independent re-clone.
3. Complete GPT → Claude → GPT native handoff with real artifact evidence and fail-closed recovery.
4. Update GD kernel, quality, operating protocol, entrypoint, and agent adapters **in-place on the same IDs**, verify raw bytes and hashes, update manifest. Do not cut over prematurely; Cursor is explicitly out of two-agent scope.
5. Revalidate a fresh GPT and Claude session. Only then may the scoped operating mode become `ACTIVE_GPT_CLAUDE`.

## Publication hardening and operational limits

The hook commands use the project-root path; SessionStart injects additionalContext.
Git subprocess stderr is captured instead of leaking authentication details.
All unknown/non-active storage modes remain test-scope-only. Foreign ownership
raises WRITER_CONFLICT_STOP. Every write requires an explicit expected revision:
set VZP_EXPECTED_STATE_REVISION in the Claude runtime to the actual revision after
its legitimate CLAIM, or pass --expected-revision to the CLI. This value is NOT
auto-refreshed: stale values STOP, never adopt someone else's newer baseline.
After a successful OPEN checkpoint, refresh/reconcile the exact baseline before
finish. Missing expected revision means no write. The Stop timeout covers the
isolated clone/commit/push/independent-clone sequence. Unexpected interruption
still requires remote reconciliation; no retry or lease stealing.

This explicit revision/ownership setup is an automation limitation: installing
hooks alone does not provide unattended two-way session coordination. GPT still
uses instructed connected-tool operations; no native GPT turn hook is deployed.
A shell invocation of this script or a mocked test is NOT a real Claude hook run.

Hook API reference: https://code.claude.com/docs/en/hooks
