# Prompt-driven continuity — protocol 2.3.0

## Prompt-boundary release

The original 2.1.0 transport and privacy contract still applies. An owned
workstream MUST be finalized before the agent returns its terminal response:
read back native changes, persist and verify immutable private context,
call `finalize_phase` in `prompt_state.py`, publish through approved CAS,
and independently read back the remote Git revision and owner.

The default for unfinished work, Human Review pauses and multi-phase Work is
`HANDOFF_OPEN` (owner null, WIP retained). Fully evidenced completed work
may use `CHECKPOINT_PASS` (owner null). The operator chooses the internal
completion outcome automatically; the user need not request a release.

No chat hook, timer, expiry, or background agent is assumed. An interrupted
process can leave a claim stranded and cannot silently release it. A subsequent
writer must STOP and use the OWNER_AUTHORIZED_RELEASE contract below.

## Current acceptance status — 2026-10-25
Historical acceptance baseline: protocol 2.1.0; current implementation contract 2.2.0.

The Git-state / GD-project implementation is active. GPT ↔ ordinary Claude continuity achieved the separately reviewed CUTOVER_PASS on 2026-10-25.
Evidence: CROSS_AGENT_TEST CHECKPOINT_PASS revision 35, commit 7eb4c0e0f2a77153feceb05efbdd632f38c21e03, successful CI run 40202011072, and the private immutable acceptance report/verdict resolved through the canonical private Entry Point.
The schema-valid deployment=ACTIVE_ACCEPTANCE_PENDING remains unchanged: it is an operational enum, not the acceptance verdict and not a revocation of CUTOVER_PASS.
Per-turn fresh bootstrap, Git operational authority, private GD project/method authority, run ownership, conditional writes, independent read-back and STOP/RECONCILE remain mandatory. Both transports A/B and all nine B invariants remain unchanged.
Cursor, individual Miro/GS/Archi runtimes and business acceptance are outside this verdict. CUTOVER_PASS is not VZP customer architecture approval.
Acceptance test procedures below remain the evidence standard; they do not reopen or require repetition of accepted tests without a newly evidenced defect.

Owner-approved authority: Git operational state; private Google Drive project.
No hooks, no agent invocation. This supersedes previous GD-state and hook designs.
Deployment remains ACTIVE_ACCEPTANCE_PENDING; the separate acceptance verdict is recorded below.

## Authority and bootstrap

On EVERY user prompt, both ordinary ChatGPT and ordinary claude.ai fresh-read
private project instructions, manifest, kernel, Source Index and routed modules.
Then read this protocol, `state.json` from current main with its blob SHA and
commit, the selected scope checkpoint, and the referenced private/native artifacts.
Do not reconstruct current work from an old chat or downloaded migration bundle.
Cursor is NOT TESTED and nonblocking. No Claude Code dependency.

`state.json` is the only mutable operational registry. Its scope checkpoint,
owner and artifact key are committed together. Git commits are immutable handoffs;
use the exact commit plus state revision, not a moving main URL as evidence.
Existing private GD operating registries are historical; business evidence and
business decision authority remain on GD. Do not resume writing old GD State,
Work Log or Write Control. Private governance defines exact canonical GD IDs.

## Confidentiality and work context

Public state accepts only the strict schema in `prompt_state.py`: finite codes,
random opaque keys/run IDs, timestamps, revisions and public commit SHAs.
No prompt, private URL/ID, filename revealing business context, business content,
or arbitrary free text. Review every public change BEFORE upload; schema/CI
cannot detect information intentionally encoded into an otherwise valid key.
Commit messages are generic operation/scope/revision only. CI logs are public.

Full goal, last verified completion, WIP, versions, decisions, risks, blockers,
next safe action and provenance belong to a private immutable context artifact.
Use `VZP_CONTEXT_<random32hex>.md` in the private handoff folder resolved through
Entry Point. Its random key alone goes into Git. Fetch by exact unique filename
within that private folder, verify embedded key/scope and any native references.
No matches or multiple matches => STOP. The file is not a second latest-state
registry; only Git selects the active key. Existing method/source originals
retain their IDs. Creating a new context snapshot does not replace a canonical
method file and does not require in-place GD replacement in ordinary Claude.

## Write transaction

1. Fresh-read state + blob SHA; compare expected revision. Verify scope owner.
2. Generate a unique 32-hex run ID for this execution. CLAIM requires owner null.
   Owner is `{agent, run_id}`; another chat of the same agent is a foreign writer.
3. Validate the exact transition locally using `prompt_state.py`, or reproduce
   the documented transition exactly through the connector. Review privacy.
4. Write the complete state using approved transport A or B below.
   A client without an approved concurrency transport is WRITE_BLOCKED. Never force,
   silently refresh the baseline, or merge around a conflict.
5. Independently read back exact full content and blob/commit. A timeout or
   uncertain write outcome requires read/reconcile, never blind retry.
6. Before each native artifact write, recheck Git ownership AND native baseline.
   Git CAS does not lock Drive, Miro, Slides, or other native services. If native
   revision checking is unavailable, use cooperative serialization and STOP on
   ambiguity; never describe it as an atomic distributed lock.
7. Native read-back precedes saving new private context and Git checkpoint.
   Read back that private context before publishing its opaque key in Git.
   Unreferenced private snapshots after a failed Git update are staged/orphaned,
   never authoritative; reconcile them without inventing a successful handoff.

## Lock governance and provenance — 2.2.0

Read-only prompts do not CLAIM. Before class C protected writes, fresh-read main HEAD,
state blob SHA, revision, scope owner and native baseline. A foreign agent OR
run means STOP for conflicting mutations; safe read-only assistance continues.

Create a private immutable `VZP_ORIGIN_<32hex-key>.json` in the canonical handoff
folder. Required fields: key, scope, actor (agent/run_id), created_utc (real UTC),
request_id (generated unique 32hex), purpose and platform. Optional chat_title,
chat_id, chat_url, message_id and message_url are included only if actually
available. Generated request_id is NOT a native message ID. Never invent links
or create public conversation shares. Resolve exactly one file by folder/name,
verify identity and complete provider read-back before CLAIM. `lock_origin.py`
validates the private record and prepares the claim; it does not perform I/O.

Publish owner and `claim_origin_key` together through one validated CLAIM and
approved CAS; independent Git read-back is mandatory. A failed Git write leaves
a staged/orphan private origin, never active ownership. `claim_origin_key` is
separate from the latest work `private_artifact_key`, immutable while owned,
and cleared on release (the CLAIM event/Git history preserves its value).
The state schema 2.0 accepts this narrow optional field and two event extensions:
CLAIM carries claim_origin_key; OWNER_AUTHORIZED_RELEASE carries expected_owner.
Old snapshots and history remain readable without rewrite. Older writers that
do not understand these fields MUST stop and load the current guard. Missing
historical origins are LEGACY_ORIGIN_UNAVAILABLE, never reconstructed guesses.

Conflict reporting is private: stream, owning agent, verified start/purpose,
chat title/link if known, status and latest checkpoint; recommend asking that
agent to release. If no chat can be resolved, say so and offer explicitly
project-owner-authorized release from another session. Technical IDs belong in
extended diagnostics, not the ordinary user message. `conflict_details()` does
not claim lookup success when a current origin cannot be resolved.

OWNER_AUTHORIZED_RELEASE requires all of: actual explicit project-owner mandate
in current context for the exact scope and expected old agent/run; fresh exact
revision/blob SHA; available provenance (or explicit legacy unavailability);
verified last changes/native artifacts; immutable private reconciliation audit
and authorization evidence; transition() and verify_transition(); approved CAS;
full remote read-back. Boolean flags/opaque keys are attestations, not proof or
permission. CI checks public structure, not private mandate or runtime identity.
The new session uses its own run ID, never impersonates the previous owner.
An authorized GPT may perform the operation when Claude lacks Git permission.
Without mandate, matching owner, permissions or reliable evidence: STOP/RECONCILE.
No retry, force, takeover, age-based expiry or background orchestration.

Result: IN_PROGRESS_OPEN, owner=null. Preserve last work checkpoint, working
context and OPEN items; append an audit event rather than fabricating completion.
RECOVERY_OPEN still requires the existing explicit RECONCILE path. Delayed old
Git writers fail owner/revision/CAS guards; native systems without CAS require
fresh ownership checks and cooperative serialization, not a distributed-lock claim.

At normal completion or controlled interruption, invoke finalize_phase() with
verified private working context/native read-back: HANDOFF_OPEN for unfinished
work, CHECKPOINT_PASS only for evidenced completion. No special user release
request is needed for the owning live run. Crashed sessions cannot execute this
function; there are no hooks, leases, heartbeats, watchdogs or timeout release.

The prior 2.1.0 CUTOVER_PASS is preserved and does not accept these new 2.2.0
features. Symmetric unit tests using GPT/CLAUDE labels are not Claude runtime
execution. Report new runtime checks separately. Deployment enum is unchanged.
During rollout, a Git/GD protocol mismatch is STOP for mutations; publish the
canonical private documents in-place and manifest last before normal use.

## Events

| Event | Preconditions | Result |
|---|---|---|
| CLAIM | Fresh revision, owner null, no recovery, verified private origin | IN_PROGRESS, owner=this run; saved checkpoint retained |
| CHECKPOINT_OPEN | Own run, native read-back | IN_PROGRESS_OPEN, owner retained |
| HANDOFF_OPEN | Own run, native read-back | IN_PROGRESS_OPEN, owner null; unfinished work explicitly preserved |
| CHECKPOINT_PASS | Own run, native read-back and evidence commit | READY_FOR_HANDOFF, owner null; this scope only, not overall acceptance |
| RECOVERY_OPEN | Own run, uncertain/partial work | RECOVERY_OPEN, owner retained |
| RECONCILE | Recovery, explicit owner authorization, verified native baseline | IN_PROGRESS_OPEN, owner null; never automatic completion |
| OWNER_AUTHORIZED_RELEASE | Exact expected owner, explicit scope mandate, private audit, native read-back, CAS | IN_PROGRESS_OPEN, owner null; last work checkpoint/context retained |

All mutations increase global revision exactly once and append a bounded event.
The Git history retains older events. No mutation is needed for an informational
prompt. No automatic lock expiry or ownership takeover. Native-readback flags
are agent attestations requiring inspectable evidence; schema validation alone
is not native or visual acceptance. Production RECONCILE requires owner-reviewed
recovery; current automated recovery fixture is restricted to CROSS_AGENT_TEST.

## Tool-neutral usage

Download `prompt_state.py` and state into a temporary execution environment if
Python is available. `transition state.json request.json output.json` prepares
an upload; it does not publish. Request supplies expected_revision, actor, scope,
event and optional evidence/context fields. `compare before.json after.json`
verifies the whole diff. Ordinary chat with a SHA-capable GitHub connector may
make the identical JSON update directly, then run CI and full read-back. A local
script is a guard, not a simulated Claude runtime. `state_cli.GitHubBackend` is an
optional authenticated backend, not a prerequisite and never a place for tokens.
Legacy auto_sync/continuity_v2 entry points are disabled; old files/tests document
historical behavior only. `.claude/settings.json` has no hooks.

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

## Operation risk classification — 2.3.0

RISK_POLICY.md is normative for operation classes A/B/C and private Drive evidence.
Existing write transactions, origin/CLAIM, checkpoint and CAS requirements apply
to class C. B does not modify shared Git state or bypass transition guards.
Deployment of this policy is separate from B activation; runtime acceptance OPEN.
