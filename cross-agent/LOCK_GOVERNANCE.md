# Lock governance contract

## Lock governance and provenance — 2.2.0

Read-only prompts do not CLAIM. Before protected writes, fresh-read main HEAD,
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
