# VZP cross-agent state — migration package

**Status: PILOT_NOT_CUTOVER.** No authenticated publication has been verified. The live Google Drive state (revision 2) remains authoritative until a validated cutover.

## Purpose

- One **public-metadata-only** snapshot in `cross-agent/state.json`, not five routinely edited Google Drive files.
- One Git commit per meaningful change; Git history is the immutable event/checkpoint log.
- Conflict detection through GitHub Contents API `sha` and application-level `state_revision`.
- Workstream scope ownership, no automatic lease stealing, no simultaneous writers.
- Native Miro/Slides/Archi revision and visual acceptance remain independent.

## One-time controlled installation

1. Inspect all files for secrets, internal document content, addresses, client details, private Drive URLs or restricted excerpts.
2. Commit only sanitized `cross-agent/state.json`, `cross-agent/state_cli.py` and this README to `romanhlavac/vzp-architecture`.
3. Set **locally** `GITHUB_TOKEN` (fine-grained token with Contents read/write on the repo) and optional `GITHUB_REPOSITORY`.
4. Execute `python cross-agent/state_cli.py read`, then exercise test-only workstream `CROSS_AGENT_TEST` with `claim`, `checkpoint-pass`; inspect resulting commits.
5. Deliberately test wrong `--expected-revision` and foreign agent; both must STOP without mutation.
6. Have actual GPT, Claude Code and Cursor independently read the same new Git state on two distinct turns and perform a controlled test handoff.
7. Only after the acceptance matrix passes, update the **existing** Google Drive Project Skill, Quality Gates, Operating Protocol, Entry Point, and Claude/Cursor adapters in-place with read-back. Mark the old GD state as archival snapshot. Update Skills Manifest SHA/bytes/version. Do not duplicate or delete source materials.

## CLI examples

```bash
export GITHUB_TOKEN='set-in-your-local-secret-store-not-in-chat'
python cross-agent/state_cli.py read
python cross-agent/state_cli.py claim --agent GPT --workstream CROSS_AGENT_TEST --expected-revision 3
python cross-agent/state_cli.py checkpoint-pass --agent GPT --workstream CROSS_AGENT_TEST --expected-revision 4
python cross-agent/state_cli.py claim --agent CLAUDE --workstream CROSS_AGENT_TEST --expected-revision 5
```

Each later invocation must use the actual latest revision. A conflict error is not permission to overwrite — re-read and reconcile.

## Confidentiality

The target repository is public. It may contain only approved operational metadata: statuses, pseudonymous workstream/agent codes, revision numbers, non-sensitive test events and commit hashes. Never publish Project Instructions content, client documents, personal data, credentials, restricted `Approach*` content or private Drive document locators.

## Operating states

- `PILOT_NOT_CUTOVER`: GitHub snapshot is proposed only, Google Drive rev2 remains canonical.
- `READY_FOR_HANDOFF`: meaningful result read back and safe to transfer.
- `RECOVERY_OPEN`: partial or conflicting work; no silent resumption.
- `CUTOVER_APPROVED`: to be assigned **only after** cross-agent runtime acceptance and in-place GD pointers verified.

## Acceptance limits

Tests in this package validate application-side stale revision, writer conflict and public-data guard. They do **not** prove actual GitHub API conflict handling, Claude/Cursor runtime access, live cutover or native Miro visual acceptance.
