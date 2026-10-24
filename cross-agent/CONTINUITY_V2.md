# VZP agent-neutral continuity v2 — scoped implementation

**Status: INTEGRATION_PILOT / NOT FULLY AUTOMATIC / NOT CUTOVER** (2026-10-25).

## The required user experience
A user can write ordinary prompts in ChatGPT or Claude and return at any time; the next agent must recover the current work intention, progress, validated artifacts and OPEN work **without a manual handoff command or manual choice of workstream**. This does not require one model to execute the other.

## Implemented in this repository
- `cross-agent/continuity_v2.py` extends existing `state.json` with a safe `continuity.latest_workstream` and a stream-specific snapshot: `phase`, `work_code`, `next_code`, `artifact_system`, `evidence_commit`.
- `context_for_turn()` reconstructs the latest **public operational metadata**. `transition()` rejects stale revisions, unsafe free text, foreign ownership, unverified completion, and non-test writes during pilot. Contents API uses blob SHA compare-and-swap; Git history is the audit trail.
- Claude **Code** project `.claude/settings.json` contains `UserPromptSubmit` hook; `cross-agent/prompt_context.py` fetches fresh GH metadata on every prompt and injects it as model context. This is not the same as a native Claude.ai chat hook.
- Original Claude `SessionStart` and `Stop` hooks remain: Stop can record an OPEN checkpoint only with explicit scope/ownership/expected revision. It does not automatically summarize the semantic content of a conversation.
- GPT connected GitHub operations proved an actual state update/read-back in the test scope. No automatic ChatGPT product-level turn hook has been installed; project prompts requiring tools are a behavioral protocol, not an external lifecycle guarantee.

## Authority and confidentiality
- All published GitHub status codes are suitable for a **public** repository. Never publish raw prompts, private client information, business-source excerpts, Drive URLs, credentials, chat transcripts or private artifact IDs.
- Semantic work summaries would require an approved **private** shared context store. This repository does not provide it and therefore cannot reconstruct unrestricted GPT/Claude private chat context.
- Private Google Drive methodology, Source Index and legacy operational state **remain canonical**. No cutover until the full two-agent acceptance passes.
- Neither a GH workflow PASS nor a code-level test proves real Claude Code hook execution or native Miro/Slides/Archi read-back.

## Remaining before a true success claim
1. Native Claude Code `UserPromptSubmit` hook must run in an authenticated session; verify automatic context injection from the latest GPT update. Test `Stop` with real runtime and preserved ownership.
2. Claude must publish a valid next context update after actual work, with independently readable evidence; GPT must read and use it in a different ordinary user turn.
3. Verify resumed real native artifacts and OPEN work, plus stale/foreign-writer STOP.
4. Demonstrate **automatic** read/write on every relevant ordinary prompt for the actual GPT and Claude products the user operates; otherwise classify as INSTRUCTED / SEMI-AUTOMATIC, not fully automatic.
5. For detailed semantic continuity, deploy a confidential shared context store with both agents' authorized access. Do not put such content into this public repo.
6. Only then update canonical GD policy documents in place and grant scoped cutover. Cursor remains outside scope.

**Product limitation:** a repository cannot install lifecycle hooks into an ordinary ChatGPT or Claude.ai conversation. Claude Code and Codex-like local runtimes can support hooks; those hooks must be installed, trusted and actually executed in each runtime. No fallback may claim that it has synchronized content it cannot access.
