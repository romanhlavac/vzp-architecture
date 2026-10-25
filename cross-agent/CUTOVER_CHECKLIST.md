# Deployment / acceptance checklist

- Git operational authority; GD private project authority; no hooks.
- Same canonical GD governance IDs, full read-back, hashes and manifest last.
- Old GD operating registries preserved as superseded history.
- Strict public metadata and per-session owner, SHA/revision conflicts fail closed.
- Actual GPT tests and CI; isolated ordinary-Claude tests; fresh GPT return prompt.
- ACTIVE_ACCEPTANCE_PENDING until all current gates pass. Never import historical
  pilot PASS as current evidence. Cursor NOT TESTED/nonblocking.
- Failed or partial governance rollout: STOP/RECONCILE, no business mutations.

Current contract: [PROTOCOL.md](PROTOCOL.md). Gates: [acceptance](PROMPT_DRIVEN_ACCEPTANCE.md).
