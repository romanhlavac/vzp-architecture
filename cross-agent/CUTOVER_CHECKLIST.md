# Cutover to GitHub state — controlled execution checklist

Current owner decision: use existing public `romanhlavac/vzp-architecture` for non-sensitive operational state only.

- [ ] GitHub file publication and exact commit/SHA read-back completed (not just a local file).
- [ ] Branch head and blob SHA recorded; Contents API stale-sha mutation returns conflict.
- [ ] GPT test read/claim/handoff of `CROSS_AGENT_TEST` completed with native Git commits.
- [ ] Independent Claude and Cursor live read/write/read-back tests, on separate turns, PASS.
- [ ] One cross-agent full handoff GPT → Claude → Cursor → GPT, including STOP on stale revision.
- [ ] Confirm public metadata only, zero confidential business material (the Git history is permanent).
- [ ] Update `VZP_PROJECT_SKILL.md` on same GD file ID to read `cross-agent/state.json` after normal methodology bootstrap.
- [ ] Update `VZP_METHOD_QUALITY_GATES.md`, `VZP_CROSS_AGENT_OPERATING_PROTOCOL.md`, `VZP_PROJECT_ENTRYPOINT.md` and agent adapters to GitHub authority (same GD IDs).
- [ ] Update `VZP_SKILLS_MANIFEST.md` bytes/hash/version on same ID; independent read-back.
- [ ] Make legacy GD State, Work Log, Decision Log and Write Control read-only archived snapshots, not parallel live masters. Do not delete historical handoffs.
- [ ] Source Index stays on GD and retains original Sxx IDs. No new VZP client architecture decision implied.
- [ ] Final status explicitly `CUTOVER_PASS` only when all applicable gates pass. Otherwise `PILOT_NOT_CUTOVER`.
