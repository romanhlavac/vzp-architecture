# Real ordinary-chat acceptance — version 2.0

No Claude Code or hooks. No model impersonation. Separate user prompts are the
trigger. User may relay test status but must not relay work content as proof of
continuity. The tested actor must make its own source reads/writes.

## Gates

| Gate | Required evidence |
|---|---|
| A1 GPT | Real Git CLAIM, CHECKPOINT_OPEN/HANDOFF_OPEN, full independent read-back |
| A2 GPT guards | Real stale blob SHA rejected; stale revision, foreign run and recovery fixtures produce STOP with unchanged remote blob |
| B1 Claude reads | Two separate ordinary-Claude prompts read current GD methodology and current Git revision/blob/checkpoint; second independently restores open work |
| B2 Claude write | Own run CLAIM, own checkpoint and private context if materially changed, Git read-back and CI |
| B3 Claude guards | Isolated stale revision, foreign-run and recovery STOP; real stale SHA rejected; no changes to rejected baseline |
| C1 New GPT prompt | Finds Claude commit/context directly, verifies evidence, claims with new run and safely continues |
| D Whole chain | A1/A2/B1/B2/B3/C1 PASS, no unresolved state conflict or confidential public output |
| Cursor | NOT TESTED, nonblocking |

Historical pilot evidence is not current B1/B2/C1. A new GPT prompt is required
for C1; the GPT turn preparing the handoff cannot claim that future prompt ran.

## Ordinary Claude prompt 1 (read only)

Use the configured private VZP Entry Point, fresh-read instructions/manifest,
kernel/index and GOV/OPS modules, then current Git protocol/state/checkpoint in
romanhlavac/vzp-architecture. Resolve CROSS_AGENT_TEST's opaque private context
key inside the private handoff folder; read it, not a chat summary. Report live
revision/blob/commit, goal/WIP/next action and source provenance in private chat.
Inspect available Git connector read/conditional-write/branch tools. No writes.
Never publish private locations or content to GitHub. Report missing capabilities
without inventing a successful test. Do not require GD in-place state writes.

## Ordinary Claude prompt 2 (new user prompt)

Repeat all fresh reads. Continue only CROSS_AGENT_TEST work discovered from Git
and its private context; do not reuse the previous response as the source. Use a
new random run ID. Make a SHA-conditional CLAIM and full read-back. Save a genuine
own private context snapshot under a new opaque key if context changes, read it
back, then CHECKPOINT_OPEN and HANDOFF_OPEN with next_code GPT_RESUME, preserving
IN_PROGRESS_OPEN and releasing ownership only in the handoff event. Inspect CI.
Record exact commit/blob/revision and evidence; do not mark overall PASS.

For negative tests, create your own temporary branch from the fresh main commit,
never corrupt main. In CROSS_AGENT_TEST: CLAIM with your actual Claude run; use
that prior blob SHA for an attempted update after the successful claim and
require GitHub conflict plus unchanged read-back. Use the actual transition guard
against the persisted fixture with old expected revision; then with a distinct
synthetic run ID (same agent is enough), and then an owned RECOVERY_OPEN fixture.
Each unauthorized transition must STOP BEFORE upload; fetch the fixture again
and verify unchanged bytes/blob. This tests the guard, not server-side ownership
ACLs. The synthetic identity is a test input, never a claim another agent ran.
The task owner authorizes test-only RECONCILE after fixture/native read-back;
record the authorization as an opaque key to your private test evidence. Never
resolve business recovery by this test authorization. Release the fixture and
return only evidence pointers/status. If no execution tool can run the guard,
report those negative tests NOT TESTED; logical narration is not execution.

## New GPT user prompt

Fresh bootstrap VZP; read current Git state and CROSS_AGENT_TEST checkpoint plus
private context directly. Verify ordinary-Claude commits, read-backs, CI and
negative-test evidence. Continue the discovered next action with a new GPT run,
write/read-back own scoped checkpoint. Report each gate separately. Do not infer
real Claude runtime solely from an agent string in public JSON: cross-check the
owner's real Claude tool transcript or witnessed session. No CUTOVER_PASS until
the whole chain is actually proven.
