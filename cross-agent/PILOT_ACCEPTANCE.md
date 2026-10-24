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
CLAUDE_LIVE_PASS: NOT TESTED.
CURSOR_LIVE_PASS: NOT TESTED.
CROSS_AGENT_CHAIN_PASS: NOT TESTED.
GD_POINTERS_UPDATED_PASS: NOT EXECUTED, prerequisite gates open.

The supplied PROTOCOL.md requires all gates before changing state to ACTIVE,
archiving the old operational state or changing canonical GD policy.
Consequently, no canonical GD policy or operational state was changed here.
GD remains authoritative; historical documents and checkpoints are preserved.
GitHub state remains a pilot, not a parallel live operational master.

## Next actual-agent acceptance
Run under actual Claude and Cursor identities in their respective environments.
Fresh-read methodology and operational sources on two distinct user turns.
Use only CROSS_AGENT_TEST. At every transition fetch latest state/blob SHA,
require matching revision and ownership, mutate with the observed SHA and
independently read back. Record native runtime evidence in an approved location.
Complete GPT → Claude → Cursor → GPT handoff and stale/recovery tests.
Do not have GPT impersonate external agents to mark their gates PASS.
After these gates pass, update canonical GD files in place, archive historical
operational state, update manifest hashes and independently verify read-back.
