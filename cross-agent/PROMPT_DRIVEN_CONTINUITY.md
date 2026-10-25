# VZP cross-agent continuity — symmetric prompt-driven contract

Status: DESIGN_CORRECTED / OWNER_WORKING / ACCEPTANCE_OPEN (2026-10-25).
Supersedes the mandatory-hook and public-GitHub-authority assumptions in the older pilot runbooks. Does not grant client approval or complete a state-store cutover.

## Goal and boundaries

User may alternate ordinary prompts among ChatGPT, Claude (standard chat), and eventually Cursor. Agents DO NOT invoke one another. No agent-specific SessionStart/Stop/UserPromptSubmit hook, operating-system command, daemon, background monitor, or ChatGPT lifecycle hook is required. Hooks and CLI adapters are OPTIONAL accelerators, NOT contract requirements and NOT acceptance gates.

The requested guarantee is **durable work continuity**, not sharing hidden reasoning, full transcripts, all uncommitted chat state, or automatic execution without a user prompt. Continuity is achieved only for work facts an agent actually persisted and independently verified.

## Authorities (no premature migration)

1. **Private Google Drive**: canonical VZP Project State, Work Log, Decision Log, Write Control and immutable handoff checkpoints; canonical project instructions, Skills Manifest, methodology and Source Index (S01–S53). Read the active VZP Project Entry Point to discover the current exact private Drive IDs; never hardcode them in this public repository.
2. **Native systems**: Miro, Google Slides/Sheets, Archi and governed code repositories own their actual artifacts, status and revisions; a checkpoint only references them.
3. **Public GitHub**: code, CI, safe operational metadata projection and CAS-tested pilot. `cross-agent/state.json` remains `PILOT_NOT_CUTOVER` and is NOT the canonical private work context. Never push client material, private Drive URLs/IDs, sensitive decisions, transcript content or secrets to this public repository.
4. GitHub state may be promoted only by a separate justified data-classification/authority decision, not as a precondition to prompt-driven continuity. For the current design no such promotion is required.

## Identical begin/resume sequence for every agent and every user prompt

1. **Fresh bootstrap** from the current private Drive instructions, complete Skills Manifest, kernel, Source Index, work-mode modules. Confirm status, authority, version, currentness and confidentiality. No chat memory/cache substituted for reads.
2. Read the **full** current cross-agent Operating Protocol, Project State, Work Log, Decision Log and Write Control and the **latest checkpoint referred to by State**. Validate State revision/last handoff and resolve named workstream + OPEN/next actions.
3. Read any relevant GitHub pilot/projection as optional information; never let it override private GD until explicitly authorized. Read the actual native target artifacts/versions as required.
4. Determine the user's intent and bounded task scope. Select single-writer workstream and check current owner; never assume an expired or missing lease is an enforceable distributed lock.
5. **Before each shared write** re-read State/Write Control and target-native revision/hash. Compare with captured baseline. Conflict, unknown owner, stale version, incomplete checkpoint or inaccessible source => `STOP/RECONCILE`, no last-write-wins, no blind retry.
6. Perform only authorized changes. If it is a read-only question with no material progress, do not create artificial checkpoints or advance revisions.
7. After meaningful progress, persist *short factual work continuity* on PRIVATE GD: goal, completed work, observed revisions/URLs, OPEN questions, next safe action, statuses, approvals/decision authority, and workstream. Preserve draft/in-progress state when work is not complete. **Never claim READY based on chat text alone.**
8. Independently read back any changed native artifacts and written records; publish a new immutable handoff, append Work Log and Decision Log when justified, update State pointer/revision, release single-writer ownership on READY. Follow existing canonical protocol's ordering and recovery rules; no fabricated atomic Google Drive CAS.
9. On a later user prompt **any agent** repeats the same sequence and resumes from GD State + checkpoint, not from the prior agent's chat. Agents do not need to message or trigger one another.

## Semantics and failure policy

- `READY_FOR_HANDOFF`: all recorded scoped outputs independently verified, checkpoint published and State pointer reconciled.
- `IN_PROGRESS_OPEN` / `RECOVERY_OPEN`: paused, incomplete or partially committed; do not treat as accepted or take ownership silently.
- `STOP/RECONCILE`: stale revision, foreign writer, missing link/source, uncertain write or cross-system conflict.
- Google Drive connector offers **soft cooperative writer control**, not a transactional CAS. Exact concurrency safety needs separate technical controls; do not oversell the mechanism.
- If an ordinary Claude chat lacks authenticated private GD read/write connectors, mark that specific gate `ACCESS_NOT_VERIFIED`; configure supported connections or select a supported mechanism. Do not force Claude Code as a substitute.
- User prompts and persistent agent instructions initiate this sequence. No background run is promised when there is no user prompt.

## Portable prompt contract (for GPT / ordinary Claude / Cursor)

```text
Pracuj na projektu VZP podle aktuálního kanonického Google Drive Entry Pointu.
Při tomto promptu proveď fresh-read kompletní metodiky a Source Indexu,
potom Cross-agent Operating Protocol, Project State, Work Log, Decision Log,
Write Control a poslední immutable checkpoint. Ověř stav, revize, ownership
a živé cílové artefakty. Navazuj na poslední doložený pracovní stav v rozsahu
mého zadání; nečekej na vyvolání jiného agenta a nepoužívej hooks jako podmínku.
Před každým zápisem ověř aktuální baseline, po práci proveď independent
read-back a ulož validní checkpoint i next action do privátního GD.
Při neověřené autoritě nebo konfliktu STOP/RECONCILE; žádný fake PASS.
```

For permanent operation put this logic in each agent's project instructions; users should be able to send ordinary task prompts without pasting this bootstrap contract repeatedly.

## Acceptance (standard product, not Claude Code)

A0. GPT ordinary turn performs authenticated fresh GD bootstrap, reads State/latest handoff and recovers existing OPEN work.
A1. Actual **standard Claude chat** with its real GD/GitHub connections, on two separate ordinary prompts, independently recovers the latest scoped work **without manually pasted revisions, work codes or task summaries**.
A2. Claude performs a harmless isolated TEST work unit, safe private checkpoint and readback, with appropriate State/Log updates. If connector capability is missing, record `ACCESS_NOT_VERIFIED`; no simulated Claude execution.
A3. GPT new ordinary prompt independently reads Claude's private checkpoint and actual native artifact, continues the same work; exact revision and evidence must agree.
A4. Intentionally exercise stale revision, foreign writer and incomplete/recovery checkpoint in isolated TEST scope; verify **no** unauthorized business writes.
A5. Cursor may later run the identical contract; its absence does NOT block GPT↔Claude two-agent acceptance.

Hooks are NOT a gate. ChatGPT/Claude prompt compliance and supported authenticated tools still require genuine per-product end-to-end evidence. No UI/product mechanism guarantees automatic sync when agents skip required tool calls. Keep state `PILOT_NOT_CUTOVER` pending acceptance and private GD policy alignment.

## Migration plan

First publish this corrected public-safe contract and verify GitHub CI/readback. Then update SAME existing private GD IDs for Operating Protocol, Project Skill, Quality Gates, Entry Point and Claude adapter; preserve original GD State/Work Log/Decision Log/Write Control as canonical and all historical checkpoints. Update Skills Manifest metadata last and verify raw readbacks. No changes to Source Index Sxx/business evidence. Never archive the GD operational state merely to promote a public code repository.
