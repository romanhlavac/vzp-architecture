# Cross-agent GitHub state protocol (owner-authorized proposal)

## Status

`PILOT_NOT_CUTOVER` until actual GitHub read/write/back and Claude/Cursor tests finish. Historic Google Drive state remains canonical until in-place policy cutover.

## Start or resume

1. Fresh-read the full VZP methodology in private Google Drive (instructions/manifest/kernel/Source Index/relevant modules); this cannot be replaced by Git state.
2. Read `cross-agent/state.json` on current `main`, capture blob SHA and `state_revision`. When status is PILOT, treat it as a test, not operational authority.
3. Read native artifact revision for the target workstream (Miro/GS/etc.).
4. Claim only an unowned workstream with matching revision. No automatic takeover of a stale owner.

## Claim/publish

- Use the `state_cli.py` adapter with a GitHub token in environment, or use GitHub connector `fetch_file` → `update_file(sha=observed_blob_sha)`.
- Before **every** mutation re-read. If state revision or SHA is stale, or someone else owns scope, STOP; never auto-rebase a handoff.
- A `CLAIM` commit changes state to `IN_PROGRESS`; an accepted `CHECKPOINT_PASS` commit releases ownership as `READY_FOR_HANDOFF`.
- Publish only after independent verification of the actual native artifact. Commit SHA is the durable checkpoint identity (no standalone checkpoint file required).
- Use `CHECKPOINT_OPEN` or `RECOVERY_OPEN` for incomplete runs.
- Work on disjoint workstreams with a single global JSON file; concurrent writes can conflict and must reconcile, not overwrite.

## Security and authority

- Public repo: only non-sensitive operational metadata, no private Drive links, chat transcripts, client evidence, secrets or restricted text.
- Client artifacts remain in their own authorized service and retain their own canonical authority.
- Git state is not an atomic lock on Miro/GS/Archi. The JSON update is conditional on the GitHub SHA; a native editor could still conflict outside Git.
- `Source Index` Sxx/authority, methods, approvals and runtime storage decisions are unaffected.
- No retrospective transfer of work that existed only in an agent's chat.

## Cutover gates

`GITHUB_STATE_NATIVE_PASS` (real GitHub read/write/readback and failed stale update), `CLAUDE_LIVE_PASS`, `CURSOR_LIVE_PASS`, `CROSS_AGENT_CHAIN_PASS`, `GD_POINTERS_UPDATED_PASS`. Only after all gates pass change the Git state from `PILOT_NOT_CUTOVER` to `ACTIVE`, archive GD operational state, and update canonical Project Instructions/Kernel/Entry Point on GD. **Do not claim those gates based only on the Python mock tests.**

## Owner-authorized two-agent pilot scope — 2026-10-25

The current implementation task scopes the proposed cutover to GPT and actual Claude Code. Cursor remains NOT_TESTED and is not a blocker for this two-agent scope. Earlier three-agent requirements remain historical context, not the acceptance definition of this pilot. Before any GD authority transition, require verified implementation/CI, real Claude Code SessionStart context injection and Stop CHECKPOINT_OPEN, independent read-back, stale-version and foreign-writer STOP, and real GPT → Claude → GPT execution using this implementation. Previous manually executed Claude pilot commits do not prove hook execution. GPT automatic turn synchronization remains NOT_ESTABLISHED; instructed tool operations are not an automatic product lifecycle hook. Never label fully automatic synchronization PASS without evidence for both environments. Keep PILOT_NOT_CUTOVER while scoped gates are open; preserve the old GD operational state as live until a verified transition. See AUTO_SYNC_ACCEPTANCE_20261025.md for current results.
