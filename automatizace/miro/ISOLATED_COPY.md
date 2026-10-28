# Isolated workspace transport — implementation candidate

Status: **INACTIVE / NOT A GOVERNANCE CUTOVER**. The current shared operating
protocol remains in force. The activation file deliberately disables apply.
This release may be used for read-only audit and synthetic safety tests only.

## Operation

`miro-isolated-copy.yml` accepts only `mode=audit|apply`, default audit. It runs
only on main in the named protected environment, with read-only Git permissions
and serialized executions. Source identity and OAuth credentials come only from
environment secrets. No private locator is a workflow input. Audit issues GETs,
checks token scope/team, paginates items, connectors and members, and compares
two source snapshots. Public output contains fixed status codes only.

Apply additionally requires a coordinated canonical policy deployment, ACTIVE
activation record, an existing valid recipient certificate in environment
secret `MIRO_RECEIPT_CERT_PEM`, its pinned DER SHA-256, and a private immutable
recipient acceptance record. Setting a flag is not proof of authorization.
Before activation, an authorized recipient must decrypt a non-sensitive CMS
challenge outside public CI and demonstrate continued access to the private key.
Record certificate fingerprint, expiry, custodian, safe decryption procedure,
receipt retention/access and verification in that private record. Never put the
private key in this repository, CI logs, artifacts or workflow inputs.

No generic key-generation or token-derived key fallback is provided. An expired
certificate or an inaccessible decryption key is a blocker, not a reason to
silently select another recipient. Re-check validity before every copy.

The workflow uploads encrypted intent before mutation, then makes at most one
Copy Board PUT and preserves the encrypted outcome even on failed verification.
Its copy name uses the provider run ID, so reruns share the original identity;
`run_attempt > 1` is rejected. Ambiguous writes trigger read-only exact-name
reconciliation and STOP, even if provider search temporarily returns nothing.
Do not rerun apply or start another apply run to bypass that STOP.

Download and decrypt both CMS artifacts outside public CI. For an approved
recipient, the standard command is:

```sh
openssl cms -decrypt -binary -inform DER -in receipt.p7m \
  -recip recipient.pem -inkey private-key.pem -out receipt.json
```

Persist the plaintext receipt in the authorized private workspace, verify its
permissions and full read-back, and pass its location to the next Work turn.
Seven-day CI retention is only temporary delivery, not durable project evidence.
If the outcome receipt is missing after interruption, the already uploaded
intent contains the exact identity for read-only reconciliation. No auto-delete,
sharing, replacement of source, or canonical promotion is implemented.

## Assurance limits

Privacy checks require all four sharing fields and exactly the owning member.
API census equality covers observed types and connectors, not unsupported
objects, native docs/comments, all links, metadata, geometry or render fidelity.
Copy item IDs can change; source deep links may remain source-bound. Audit and
copy output explicitly leave native G1-G4 OPEN. Verify those separately before
editing the new workspace or claiming complete clone fidelity.

The scope owner check reads the workflow checkout, not a distributed native lock.
The invoking Work agent must perform the fresh canonical bootstrap, exact live
Git/source checks, authorization, exclusivity and source-configuration match
immediately before dispatch, and independent native read-back afterwards.
No promotion is automatic. Shared writes still use the unchanged transition
guard, origin, CAS, immutable private evidence and finalization protocol.

## Validation

Run `python3 -m unittest discover -s tests -p test_isolated_workspace.py -v`.
HTTP failure, retry, pagination and CMS tests use synthetic fixtures only;
the test certificate is temporary and is never a production recipient.
Real audit and deployment evidence must be recorded separately. These tests
are not actual Claude runtime acceptance or native Miro acceptance.

API references: https://developers.miro.com/reference/copy-board-1 and
https://developers.miro.com/docs/rest-api-reference-guide.
