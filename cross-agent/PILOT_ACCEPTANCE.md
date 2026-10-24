# Cross-agent GitHub pilot — native acceptance evidence

Status: **PILOT_NOT_CUTOVER**. Test scope: CROSS_AGENT_TEST only.
Execution: actual GPT / ChatGPT GitHub connector, not Claude or Cursor.

## Public-content review
All eight supplied implementation files were inspected before publication.
Published content consists of operational codes/statuses/revisions, generic tooling,
protocol and tests. No private Drive document locators, client evidence, personal
records or credential values were published. This is a review of these exact
files, not a guarantee that the regex validator detects every future sensitive payload.

## Implementation and validation
- Baseline main: d15c2b5044d71b76a6008068c6fd69d47ed4c9cd.
- Complete publication commit: efc25ffa6b27d771aaa4d04e4bb308fb8ab2d3c8.
- Initial Actions run: https://github.com/romanhlavac/vzp-architecture/actions/runs/40136771011 — success.
- Local tests: 6/6 PASS. Test fixtures now isolate test revision 3 from live state revision; baseline test validates live schema without freezing the operational revision.
- Root repository README preserved; package documentation is under cross-agent/.
- Every published implementation file was independently fetched and compared with intended content.

## Real read / write / read-back / conflict
1. Read revision 3, blob b9f0b3a687576940380634d1e3175d1b9608f205.
2. CLAIM CROSS_AGENT_TEST as GPT; revision 4.
   Commit 7555b8b64eb903264f311f11f7b2dbf54aca80fd.
   Blob 260952aea8d223e9ee78719af4f2690e4b614180.
   Full fresh read-back matched intended content.
3. Attempt checkpoint using stale original revision-3 blob SHA.
   Actual GitHub Contents API returned HTTP 409 / CONFLICT.
   Independent read confirmed the revision-4 blob and complete content unchanged.
   No stale retry or automatic rebase.
4. Fresh-read current revision 4, then valid CHECKPOINT_PASS using current SHA.
   Commit 84853a9577e895113e5e70eb88ace7cd18a5bbc4.
   Final revision 5, blob b7b9b3d0300a2f398ce62cbd96740d06a68ca8e5.
   Full read-back matched intended content.
   CROSS_AGENT_TEST = READY_FOR_HANDOFF, owner = null.
   Other workstream objects unchanged.

GITHUB_STATE_NATIVE_PASS: PASS.
Application stale-revision / foreign-owner rejection: local tests PASS.
Cross-provider native artifact locking: not claimed.
Business artifacts: no mutations.

## Remaining gates and cutover
CLAUDE_LIVE_PASS: PASS (2026-10-25, scoped GitHub pilot; evidence below).
CURSOR_LIVE_PASS: NOT TESTED.
CROSS_AGENT_CHAIN_PASS: NOT TESTED.
GD_POINTERS_UPDATED_PASS: NOT EXECUTED, prerequisite gates open.

The supplied PROTOCOL.md requires all gates before changing state to ACTIVE,
archiving the old operational state or changing canonical GD policy.
Consequently, no canonical GD policy or operational state was changed here.
GD remains authoritative; historical documents and checkpoints are preserved.
GitHub state remains a pilot, not a parallel live operational master.

## Next actual-agent acceptance
Claude native GitHub acceptance completed; continue with actual Cursor identity in its own environment.
Cursor must fresh-read methodology and operational sources on two distinct user turns.
Use only CROSS_AGENT_TEST. At every transition fetch latest state/blob SHA,
require matching revision and ownership, mutate with the observed SHA and
independently read back. Record native runtime evidence in an approved location.
Complete GPT → Claude → Cursor → GPT handoff and stale/recovery tests.
Do not have GPT impersonate external agents to mark their gates PASS.
After these gates pass, update canonical GD files in place, archive historical
operational state, update manifest hashes and independently verify read-back.

## Claude native acceptance — 2026-10-25 (GPT independently reviewed)

Assessment: **CLAUDE_LIVE_PASS = PASS for the GitHub pilot**, with the implementation deviation documented below. This is not the full cross-agent-chain acceptance and does not activate GitHub as operational master.

- Two separate Claude user turns reported fresh authenticated Drive methodology and operating-state reads. The direct independent GitHub evidence below confirms the actual native writes; private Drive-read execution is based on Claude's recorded run report.
- Start: main `fe41a56f95be838c02d56abeb4ceb9dd098dfaeb`, state revision 5, state blob `b7b9b3d0300a2f398ce62cbd96740d06a68ca8e5`.
- Claude CLAIM: commit `8011aec0d7fbca7af8aef35e654bc7dff3dfda55`, state revision 6, owner CLAUDE, status IN_PROGRESS.
- Claude CHECKPOINT_PASS: commit `861af8f49951b957b3b14779f2619afaea16fda6`, state revision 7, owner null, status READY_FOR_HANDOFF; blob `b6b891b39134199310d1e00a725d2f2e6a9e6a21`.
- GitHub commit ancestry verified: `fe41a56f` -> `8011aec0` -> `861af8f4`; only `cross-agent/state.json` changed in the two commits. Associated GitHub Actions checks both succeeded; final run `40139092183`.
- Conflict checks reported by Claude: stale expected_revision rejected locally; a non-fast-forward push from a stale commit rejected by GitHub; foreign-owner state transitions rejected locally. Rejected local attempts and CLI output are **agent-reported**, not independently reproducible from successful commit history. GitHub commits independently establish the authorized successful transitions.
- Transport deviation: Claude used `git push` without force, protected by branch fast-forward requirement, rather than GitHub Contents API with blob SHA. Accepted as equivalent conflict prevention **for this sequential pilot**, not as proof of distributed locking of native business artifacts.
- Other workstreams and business artifacts unchanged; no private-source text copied into the public repo.

**Remaining:** CURSOR_LIVE_PASS = NOT_TESTED; CROSS_AGENT_CHAIN_PASS = NOT_TESTED; GD_POINTERS_UPDATED_PASS = OPEN. `PILOT_NOT_CUTOVER` remains required. Continue later from current main HEAD and state revision (do not hardcode revision 7 after acceptance metadata reconciliation).
