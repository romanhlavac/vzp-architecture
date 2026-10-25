#!/usr/bin/env python3
"""Explicit per-prompt read helper, not a hook or an agent invocation."""
import json
from auto_sync import read_remote
from prompt_state import validate

def main():
    try:
        state, sha = read_remote()
        validate(state)
        print(json.dumps({'status':'READ_PASS','blob_sha':sha,'state':state}))
    except Exception:
        print(json.dumps({'status':'BOOTSTRAP_INCOMPLETE','write_allowed':False}))
if __name__=='__main__': main()
