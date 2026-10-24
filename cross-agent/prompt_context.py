#!/usr/bin/env python3
"""Fresh cross-agent context injection for Claude Code UserPromptSubmit.

Reads public operational metadata only. It cannot retrieve private chat history.
"""
import json
from auto_sync import read_remote
from continuity_v2 import context_for_turn

def main():
    try:
        state, blob_sha = read_remote()
        cur = context_for_turn(state)
        last = cur.get("last") or {}
        summary = (
            "VZP cross-agent context: GH state_revision=" + str(cur["revision"]) +
            "; blob=" + blob_sha +
            "; mode=" + str(cur["storage_mode"]) +
            "; latest_workstream=" + str(cur["latest_workstream"]) +
            "; last_agent=" + str(last.get("agent")) +
            "; phase=" + str(last.get("phase")) +
            "; work_code=" + str(last.get("work_code")) +
            "; next_code=" + str(last.get("next_code")) +
            ". This is public-code-only metadata, not the full working context. "
            "Mandatory fresh private Google Drive bootstrap and native artifact "
            "read-back still apply before any substantive work. In PILOT mode "
            "this GitHub record is not the operational authority. "
            "Never publish raw prompts or client content to the public repo."
        )
        print(json.dumps({"hookSpecificOutput":{
            "hookEventName":"UserPromptSubmit","additionalContext":summary}}))
    except Exception:
        print(json.dumps({"continue":False,
            "stopReason":"VZP CONTINUITY BOOTSTRAP INCOMPLETE: GitHub metadata not verified"}))
if __name__=="__main__":
    main()
