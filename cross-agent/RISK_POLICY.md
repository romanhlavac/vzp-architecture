# Risk-based governance 2.3.1

Operation classes A/B/C are distinct from Git concurrency transports A/B.
Git is the only shared operational-state authority; private Drive owns methodology,
project content and immutable evidence. Never publish private locators, business
content or credentials in Git, CI inputs, logs or artifacts.

## A — READ_ONLY
Fresh canonical/source reads, analysis and truthful reporting require no CLAIM,
origin or artificial checkpoint. Reading does not grant write authority.

## B — ISOLATED_PRIVATE
Only a new uniquely identified private noncanonical workspace, or a previously
verified workspace exclusively owned by this writer, is eligible. Verify fresh
source identity, authorization, permissions, effective privacy including inherited
access, writer exclusivity and absence of the target before mutation.
Any uncertainty, foreign writer or shared/canonical target stops B and requires C.

Before each mutation save a unique immutable intent directly to private Drive and
independently verify full content, exact parent, uniqueness and permissions.
Perform one authorized operation; independently read back source and destination,
then save and verify an immutable private outcome. Keep the source unchanged.
After ambiguous timeout reconcile read-only by the same operation identity; never
blindly repeat creation. Failure leaves isolation intact and acceptance OPEN.
Do not automatically delete, share or broaden access as recovery.

B alone requires no per-run Git CLAIM or VZP_ORIGIN and does not write shared Git
state. A requested Git checkpoint is a separate C operation under unchanged origin,
CLAIM and CAS rules. For solely B work the private receipt supplies continuity;
do not create another mutable operational registry.

Use existing authorized Work runtime/connectors and private Drive evidence.
No CMS certificates, decryption keys, encrypted CI artifacts, PKI or new external
evidence system are required. Public Actions are CI/read-only audit only.
Unavailable private evidence transport is STOP. Evidence must be accessible to
the owner and the next authorized Work step, never only on an ephemeral runner.

## C — GOVERNED_SHARED_WRITE
Canonical/shared artifacts, identities, catalogs, methodology, Git state and
governance retain the strict protocol: fresh bootstrap, verified exact immutable
private origin, unique agent/run owner, validated CLAIM under approved CAS,
permitted scope, native read-back, private context, checkpoint/HANDOFF and
independent read-back. State schema, transition guard, stale-write rejection,
foreign-run exclusion, recovery and OWNER_AUTHORIZED_RELEASE remain unchanged.
No B exemption in transition(); no force, hooks, timed release or implicit takeover.

## Promotion B to C
Explicit owner mandate, catalog reconciliation, provenance, semantic IDs/links,
access review, C scope acquisition and native acceptance are mandatory. Update
canonical configuration in place under its original ID. Never promote automatically;
preserve the original until separately authorized archival. Working copies are
not approved business models.

## Assurance and rollout
Test A no-write behavior, B eligibility/privacy/failures, private intent/outcome
ordering, C regressions, confidentiality before publication, real CI and native
read-back. API census is not semantic/visual acceptance; Miro G1–G4 remain separate.
Update canonical documents in place and manifest last with actual hashes/bytes.
Partial rollout or version/hash mismatch requires STOP/RECONCILE. Governed rollback
restores verified baselines without deleting history or forcing updates.

## Per-operation qualification — 2.3.1

B is available after coordinated deployment when this operation's own eligibility,
native permissions, private evidence transport and read-back are verified. There
is no global all-agent activation gate. A blocked Git transport for any agent does
not block another agent or an eligible private B operation, including by that same
agent. The configuration selects this policy; it is not evidence or authorization.

C requires the current writer's qualified Git transport and the existing strict
origin/CLAIM/CAS/read-back protocol. Unavailable or unqualified transport stops C
for that writer; never bypass a proxy, force-push or impersonate another agent.
Report qualification per runtime, transport and operation. Reuse evidence only
within its demonstrated scope; retest changed or defective capabilities, not the
whole interoperability chain on every prompt. Cross-agent end-to-end acceptance
remains a separate test and never becomes B's prerequisite. Real Claude execution
and synthetic tests must be reported separately. Source Index/Sxx, native visual
acceptance and business approvals are unchanged.
