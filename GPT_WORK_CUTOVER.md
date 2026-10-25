# GPT ↔ ordinary Claude — corrected continuation runbook

**Current status: DESIGN_CORRECTED / PILOT_NOT_CUTOVER (2026-10-25).**

Previous mandatory Claude Code SessionStart/Stop and public-GitHub canonical state cutover requirements were design errors for the owner's clarified objective. Historical Git history preserves that experiment; it is OPTIONAL, not a gate.

**User requirement:** work continuity across ordinary prompts in ChatGPT and ordinary Claude (Cursor later), each agent acting only when directly prompted. Neither invokes the other. Each fetches current private GD state and relevant live artifact, carries out its scoped work, then writes a durable checkpoint with independent readback. No hooks required.

Read [cross-agent/PROMPT_DRIVEN_CONTINUITY.md](cross-agent/PROMPT_DRIVEN_CONTINUITY.md), [cross-agent/PROMPT_DRIVEN_ACCEPTANCE.md](cross-agent/PROMPT_DRIVEN_ACCEPTANCE.md), and [cross-agent/CUTOVER_CHECKLIST.md](cross-agent/CUTOVER_CHECKLIST.md).

Keep the existing private Google Drive State/Work Log/Decision Log/Write Control/hand-offs CANONICAL. GitHub pilot state is secondary public-safe metadata only, not a private context store. Do not archive or delete GD registries. Keep all 53 Source Index IDs/business authorities and actual native masters unchanged. Owners/approvers retain their decision rights.

Before operational promotion: stage and read back public design; revise existing private GD Project Skill, Quality Gates, Operating Protocol, Entry Point, adapter and manifest on their SAME file IDs; verify standard-Claude two-turn prompt-driven live GD read/write, separate GPT continuation, conflicts and recovery. If GD publication/authenticated connector access is not available, report a blocked gate, do NOT claim cutover.

Actual product hooks might help in a specific IDE, but cannot be a precondition to this architecture.
