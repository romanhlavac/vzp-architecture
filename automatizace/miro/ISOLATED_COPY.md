# Isolated private workspace transport

Policy: cross-agent/RISK_POLICY.md, version 2.3.1. B eligibility is per operation;
a blocked Git transport does not disable eligible private work.

Public workflow supports workflow_dispatch audit only. It uses existing environment
secrets, reads source inventory twice and prints fixed safe codes. No mutation,
artifact upload, private inventory or receipt content enters public GitHub.

Work uses an authorized Miro connector, native UI or REST client. work_copy accepts
an authorized private Drive adapter. put_immutable(folder,name,value) creates a new
file; read(id) returns native content, parent, private and unique evidence.
The adapter must verify effective permissions and exact name uniqueness, not
substitute local flags. The caller verifies fresh bootstrap, authorization,
exclusive writer, native baseline and this operation's eligibility evidence.
Pass those verified attestations as the required operation argument; the policy
configuration alone never authorizes a write.

Intent is saved/read before one mutation; outcome is saved/read after success or
failure. On ambiguous PUT reconcile read-only by the unique identity. Preserve
intent if outcome storage fails and reconcile before any further mutation.
The generic Python interface does not prove availability of live connectors.

Native duplication must be an actual copy, not reconstructed shapes. Census is
inventory assurance only; deep links, semantic IDs, unsupported objects and
native G1–G4 require separate private acceptance. No automatic promotion or source
archival. Historical code/evidence remains preserved in Git and private Drive.
