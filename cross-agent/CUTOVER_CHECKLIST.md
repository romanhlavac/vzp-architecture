# Deployment / acceptance checklist

## Current acceptance status — 2026-10-25
Documentation revision: post-cutover-1; protocol semantics remain 2.1.0.

The Git-state / GD-project implementation is active. GPT ↔ ordinary Claude continuity achieved the separately reviewed CUTOVER_PASS on 2026-10-25.
Evidence: CROSS_AGENT_TEST CHECKPOINT_PASS revision 35, commit 7eb4c0e0f2a77153feceb05efbdd632f38c21e03, successful CI run 40202011072, and the private immutable acceptance report/verdict resolved through the canonical private Entry Point.
The schema-valid deployment=ACTIVE_ACCEPTANCE_PENDING remains unchanged: it is an operational enum, not the acceptance verdict and not a revocation of CUTOVER_PASS.
Per-turn fresh bootstrap, Git operational authority, private GD project/method authority, run ownership, conditional writes, independent read-back and STOP/RECONCILE remain mandatory. Both transports A/B and all nine B invariants remain unchanged.
Cursor, individual Miro/GS/Archi runtimes and business acceptance are outside this verdict. CUTOVER_PASS is not VZP customer architecture approval.
Acceptance test procedures below remain the evidence standard; they do not reopen or require repetition of accepted tests without a newly evidenced defect.

- Git operational authority; GD private project authority; no hooks.
- Same canonical GD governance IDs, full read-back, hashes and manifest last.
- Old GD operating registries preserved as superseded history.
- Strict public metadata and per-session owner, SHA/revision conflicts fail closed.
- Actual GPT tests and CI; isolated ordinary-Claude tests; fresh GPT return prompt.
- Preserve the schema-valid ACTIVE_ACCEPTANCE_PENDING enum independently of the reviewed verdict. Never import historical pilot PASS as current evidence. Cursor NOT TESTED/nonblocking.
- Failed or partial governance rollout: STOP/RECONCILE, no business mutations.

Current contract: [PROTOCOL.md](PROTOCOL.md). Gates: [acceptance](PROMPT_DRIVEN_ACCEPTANCE.md).

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
