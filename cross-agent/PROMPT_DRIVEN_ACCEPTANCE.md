# Real ordinary-chat acceptance — version 2.0

## Current acceptance status — 2026-10-25
Documentation revision: post-cutover-1; protocol semantics remain 2.1.0.

The Git-state / GD-project implementation is active. GPT ↔ ordinary Claude continuity achieved the separately reviewed CUTOVER_PASS on 2026-10-25.
Evidence: CROSS_AGENT_TEST CHECKPOINT_PASS revision 35, commit 7eb4c0e0f2a77153feceb05efbdd632f38c21e03, successful CI run 40202011072, and the private immutable acceptance report/verdict resolved through the canonical private Entry Point.
The schema-valid deployment=ACTIVE_ACCEPTANCE_PENDING remains unchanged: it is an operational enum, not the acceptance verdict and not a revocation of CUTOVER_PASS.
Per-turn fresh bootstrap, Git operational authority, private GD project/method authority, run ownership, conditional writes, independent read-back and STOP/RECONCILE remain mandatory. Both transports A/B and all nine B invariants remain unchanged.
Cursor, individual Miro/GS/Archi runtimes and business acceptance are outside this verdict. CUTOVER_PASS is not VZP customer architecture approval.
Acceptance test procedures below remain the evidence standard; they do not reopen or require repetition of accepted tests without a newly evidenced defect.

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
| B3 Claude guards | Isolated stale revision, foreign-run and recovery STOP; server-side stale write rejected by an approved transport; no changes to rejected baseline |
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

## Transport-neutral concurrency contract — version 2.1.0

This section supersedes transport-specific wording in earlier sections and historical evidence. Gate: SERVER_SIDE_STALE_WRITE_REJECTION_PASS; HTTP 409 is not universal.
A: Contents API expected blob SHA and server-side stale-write rejection.
B: non-force git push, permitted ONLY with ALL invariants below evidenced:
1. Fresh exact branch HEAD, state blob SHA, revision and scope owner.
2. New commit directly parented by that HEAD; no automatic pull, merge, rebase or retry after conflict.
3. Execute transition() AND verify_transition(); verify agent plus unique run_id, expected revision and exact public diff.
4. Non-force only. Force and force-with-lease forbidden.
5. Non-fast-forward rejection => STOP/RECONCILE, no reconstruction against refreshed HEAD.
6. Independent remote full read-back: HEAD, blob SHA, state revision, checkpoint and owner.
7. Verify branch history cannot be rewritten uncontrolled; inspect actual protection/rules and permissions. Local policy is not server enforcement. Missing/unverified history protection => variant B BLOCKED for accepted operation, even if a particular non-force push succeeded.
8. Only authorized scope and expected paths may change.
9. Review strict public metadata BEFORE publication; no private locators, prompts, client content or credentials.

Git protects its own update only, not a distributed transaction with GD/Miro/Slides.
A successful conflict test alone does not prove all transport invariants. Report implementation, runtime provenance, transport qualification and overall acceptance separately. Keep the schema-valid deployment enum ACTIVE_ACCEPTANCE_PENDING; use the separately reviewed acceptance verdict, never infer it automatically.
