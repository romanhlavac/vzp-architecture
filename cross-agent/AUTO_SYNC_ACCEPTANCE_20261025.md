# GPT–Claude auto-sync implementation acceptance — 2026-10-25

**Final scope status: IMPLEMENTED_PILOT / PILOT_NOT_CUTOVER.**
CUTOVER_PASS: NOT GRANTED. No native Claude runtime was simulated.
Cursor: OUT_OF_SCOPE / NOT_TESTED.

## Input and public-content review
Input ZIP SHA-256: ee41e0316234f775cfec57545b03e987e77eb123e992b2028d32f356ab1eb9e0.
Both supplied copies matched. All six overlay files were read before publication.
Only public operational metadata, generic code, tests and operating documentation
were published. No client documents, internal evidence, private Drive locators,
chat transcripts or credential values are included in this report or overlay.
Regex checks alone are not a general confidentiality guarantee.

Fresh starting main: 0daa83fd2015b3b1f738189c772c5a6f728d249a.
Starting GitHub state: revision 8, PILOT_NOT_CUTOVER, no test owner.
Private GD operational state remains revision 2 and canonical; full bootstrap and
latest referenced handoff were freshly read. Source evidence was not changed.

## Package remediation
- SessionStart uses hookSpecificOutput.additionalContext, not a display-only message.
- Hook paths use the quoted CLAUDE_PROJECT_DIR root.
- SessionStart read failure emits stopReason/continue=false without exception details.
- All writes require explicit expected revision. Stale/missing baselines STOP;
  the bridge does not silently adopt a newer revision during clone.
- Foreign writer raises WRITER_CONFLICT_STOP.
- Non-active/unknown storage modes are restricted to CROSS_AGENT_TEST.
- Git stderr is captured; no auth diagnostics are printed.
- Stop budget accommodates the full independent clone/write/push/readback sequence.
- Workflow path filters include new test modules and hook configuration.
- The GPT product-event claim in the original overlay was removed as unestablished.
- Proposed scope is explicitly GPT–Claude only; historical Cursor requirement does
  not block this task. GD policy is not yet switched.

## Results
| Gate | Actual result / evidence boundary |
|---|---|
| Local tests | 22/22 PASS; mocked tests are unit evidence, not Claude runtime evidence |
| GitHub Actions implementation | PASS: https://github.com/romanhlavac/vzp-architecture/actions/runs/40141503861 at 67c3e549765e876fdb1de6253b079e1fd4a52b87 |
| Published bytes read-back | All eight implementation/config/doc files matched intended full text |
| GPT native read/write/readback | PASS, actual connected GitHub operations |
| Safe CHECKPOINT_OPEN | PASS for GPT GitHub protocol; NOT a Claude Stop-hook execution |
| Stale SHA | Actual HTTP 409; independently verified state unchanged |
| Stale expected revision | Application guard against freshly read live state: STALE_BASELINE_STOP, zero write |
| Foreign writer | Application guard against live GPT-owned state: WRITER_CONFLICT_STOP, zero write; NOT server-side authorization |
| Actual Claude Code SessionStart/Stop | NOT_TESTED; Claude executable absent and API/OAuth environment auth not configured in this execution environment |
| GPT automatic turn synchronization | NOT_ESTABLISHED; instructed connector operations are not a lifecycle hook |
| GPT → Claude → GPT using new hooks | NOT_TESTED |
| GD cutover / archive transition | NOT_EXECUTED; conditional PASS prerequisite unmet |
| Cursor | NOT_TESTED, out of scope |

The historical Claude pilot evidence in PILOT_ACCEPTANCE.md remains valid in its
recorded scope. Its successful native Git commits and reported private bootstrap
do not establish execution of the newly installed Claude Code hooks.

## Exact native GPT test
- Read rev 8 / blob 5e7d8ea5c599a88e80a65ec0eddef08e37eb5967.
- CLAIM -> rev 9 / blob 1db559f57bcbbac6f6d6a5d13bb296fe8dfb4c94.
- Attempt OPEN using rev-8 blob SHA -> HTTP 409. Fresh GET confirmed rev-9
  full content and SHA unchanged.
- Correct OPEN using fresh rev-9 SHA -> rev 10 / blob
  757916d78651a61c951463b8ebbd4d0fbe97d4c8.
  Status IN_PROGRESS_OPEN, owner GPT; no false READY.
- After independent readback, scoped synthetic test CHECKPOINT_PASS -> rev 11 /
  blob eab8ebe1f35fbdb5207d3c93ad7c9b6deac88e51, owner null,
  READY_FOR_HANDOFF. This closes only the GPT synthetic test, not the requested
  auto-sync acceptance. Explicit automatic gates remain NOT_TESTED.
- Other workstream objects unchanged; no Miro/Slides/Archi/business mutations.

## Remaining actual-runtime procedure
1. In a real authenticated Claude Code checkout, fetch current main and verify
   .claude/settings.json is loaded (not a standard Claude chat).
2. Fresh bootstrap and capture current state/revision/SHA. Legitimately CLAIM
   CROSS_AGENT_TEST as CLAUDE only if unowned; independently read back.
3. Configure VZP_AUTO_SYNC_ENABLED=1, VZP_WORKSTREAM=CROSS_AGENT_TEST and
   VZP_EXPECTED_STATE_REVISION equal to the exact post-CLAIM revision in the
   Claude runtime. Never guess the current number from this report.
4. Start/resume a real Claude Code session. Record version, runtime timestamp and
   redacted native hook execution evidence. Verify SessionStart context delivery.
   Trigger actual Stop naturally; verify new OPEN commit via an independent read.
   Raw debug logs may contain private information: do not publish them wholesale.
5. Verify stale expected revision / foreign owner refusal with unchanged remote
   state. Reconcile OPEN explicitly; do not steal ownership or auto-rebase.
6. After actual test evidence review, finish with the newly observed revision and
   VZP_NATIVE_READBACK_PASS=1. GPT must independently read the real Claude result
   and complete the return handoff.
7. Separately establish an actual automatic GPT trigger, or explicitly accept an
   instructed/semi-automatic operating mode. This implementation supplies no GPT
   lifecycle hook. Installation cannot manufacture that capability.
8. Only after scoped acceptance update canonical GD files on the same IDs,
   verify content/hash and manifest, then archive old state without deletion.

Explicit expected-revision setup and legitimate ownership are prerequisites, not
unattended session coordination. Automatic full chat/context sync is not supplied.

## New commits in this work unit (before this report's own commit)
| Change | Commit SHA |
|---|---|
| cross-agent/auto_sync.py | 36dc71ba7e97280f9512aafa91f7f9ac4d8a2361 |
| .claude/settings.json | 2b2d8897b6cb999d2b74dbc70c6f9e027bcc609d |
| tests/test_auto_sync.py | 80a89cfffad2fd53734ad4602d03564dc22c48a2 |
| tests/test_auto_sync_guards.py | d33e88fc17daf7d0d74939ce4bb9c32fb18fbce0 |
| cross-agent/AUTO_SYNC.md | 2e64256bc224ab79754f395619bcfdcc315d869a |
| GPT_WORK_CUTOVER.md | 6e6670b8fbe72073c2913e3420ffa5f44877b026 |
| .github/workflows/cross-agent-state-validate-overlay.md | 81ff5946f38309ca006d40e078df57f17afe5d7e |
| .github/workflows/cross-agent-state-validate.yml | 67c3e549765e876fdb1de6253b079e1fd4a52b87 |
| GPT CLAIM rev 9 | e12b27a17f329f103289e6b232c3d1d14f0db79d |
| GPT CHECKPOINT_OPEN rev 10 | af73d142aae9e491a2217ea05d859ef05ec8b7e2 |
| GPT CHECKPOINT_PASS rev 11 | b19b9fde68f50487e7e50ef5b34794d78d8ec52b |
| two-agent pilot protocol | 743999406892d7d079b8e5604d69c59699e3df67 |

The commit containing this report is returned separately in the final response.
Original GD documents and historical handoffs are preserved unchanged.
