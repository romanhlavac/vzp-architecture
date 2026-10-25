# GPT ↔ ordinary Claude prompt-driven continuity — staged acceptance

**Scope:** ChatGPT + ordinary claude.ai, not Claude Code or Cursor. Status `PILOT_NOT_CUTOVER`.

- [x] Owner clarified intent: symmetric, prompt-driven, no inter-agent calls and **hooks NOT REQUIRED**.
- [x] Publish corrected public-safe protocol / normal-Claude acceptance in GitHub; retain historical implementation as optional pilot only.
- [ ] Independent GitHub head SHA, changed-file scope, CI and content readback PASS for this correction.
- [ ] Existing private GD Operating Protocol, Kernel, Quality Gates, Entry Point and Claude adapter revised **in-place on same IDs**; Skills Manifest version/bytes/SHA readback completed.
- [ ] Legacy GD State / Work Log / Decision Log / Write Control **retained as canonical**; old handoffs preserved. No public-GitHub source-of-truth migration.
- [ ] Ordinary GPT turn fresh GD methodology+operational bootstrap and valid scope readback.
- [ ] Ordinary Claude chat, two separate prompts, independently authenticates and reads private GD state and its latest handoff without manually transferred context.
- [ ] Claude chat test-only controlled write/independent GD readback, precise ownership and revision; no business artifacts altered.
- [ ] Ordinary GPT next prompt independently discovers Claude persisted checkpoint and continues, using current native artifact revisions.
- [ ] Stale revision, foreign writer, partial write/RECOVERY_OPEN => fail-closed verified; no leaked data.
- [ ] Full real-product scope evidence and fresh canonical GD readback; then and only then mark `GPT_CLAUDE_CONTINUITY_PASS`.

Claude Code hooks are **optional** and NOT acceptance gates. Cursor has its own future onboarding. If ordinary Claude lacks needed private Drive permissions or write features: mark `ACCESS_NOT_VERIFIED`, do not substitute Claude Code. No automatic chat transcript capture, spontaneous background runs or atomic Google Drive CAS is claimed.
