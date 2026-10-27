# Commit publication privacy

For transport B state writes use `publish_state.py` from the reviewed checkout.
It creates a candidate using `git commit-tree` with explicit public author and
committer identities and a canonical single-line message. It then reads the
actual object with replacement refs disabled: full message/trailers, one exact
parent, the state-file-only diff, regular file mode, baseline blob/revision/owner,
and the exact request reproduced by `transition()` and `verify_transition()`.
The event, scope, revision and agent in the message must match that state;
the run ID is checked in the transition, not inferred from the Git author.

Supply the fresh expected HEAD/blob and a private JSON request with the current
`prompt_state.transition` arguments, including a fixed real `timestamp_utc`.
The private evidence JSON must contain `privacy_review: true` only after review
of all public metadata. Origin verification and release authorization flags are
external evidence attestations, never substitutes for Drive read-back or mandate.
Neither private input file belongs in the repository.

```sh
python /reviewed-checkout/cross-agent/publish_state.py \
  --repo-dir /target-checkout --repository OWNER/REPOSITORY \
  --branch EXACT_AUTHORIZED_BRANCH --expected-head EXPECTED_HEAD \
  --expected-blob EXPECTED_STATE_BLOB \
  --request /private/request.json --evidence /private/evidence.json
```

The publisher reads live GitHub push permission and effective branch rules using
existing `gh` authentication. Both deletion and non-fast-forward rules must be
active with no bypass. Missing permission or uninspectable protection blocks B.
It rechecks remote HEAD and pushes only the inspected SHA with an explicit
non-force refspec. A conflict or uncertain result stops; never retry, rebuild,
merge, rebase or force around it. Existing Git authentication must already work.
No credentials are written by this workflow. No hooks are installed or required.

`qualify(..., phase='prepublish')` returns `PREPUBLICATION_PASS`, not a completed
transport verdict. Caller-supplied `candidate_commit_inspected` and
`candidate_commit_message` are rejected, even if true/canonical. Post-publication
qualification requires a separately fetched full snapshot matching the inspected
HEAD, blob and bytes (therefore revision, checkpoint and owner too). CI and
private evidence checks remain subsequent acceptance gates.

Transport A remains Contents API with expected blob SHA and independent read-back.
The candidate-object gate is for B, where a local commit exists before upload.
This client workflow prevents accidental metadata publication when used; it is
not a server-side ban on every possible direct Git client. An operator must not
bypass it. Unit tests and CI do not prove ordinary Claude runtime execution.

In Claude Code verify effective `attribution.sessionUrl=false` and empty
attribution settings, but never use settings as proof of safe commit metadata.
If a harness appends trailers, the candidate object must still pass inspection;
no rejected commit may be pushed. Do not rewrite historical commits.
