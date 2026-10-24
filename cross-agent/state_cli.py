#!/usr/bin/env python3
"""Minimal cross-agent state protocol for a GitHub Contents API-backed JSON snapshot.

One file/one Git commit per meaningful checkpoint. SHA precondition is applied by
GitHub's Contents API. On a conflicting SHA (409/422), stop and re-read; never
retry a PUT with a silently updated base. Public operational metadata ONLY.

No token is written to files or logs. Does NOT lock native Miro/Slides artifacts.
"""
from __future__ import annotations
import argparse
import base64
import copy
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

AGENTS = {"GPT", "CLAUDE", "CURSOR"}
WORKSTREAMS = {"METHOD", "SOURCE", "CES_1B", "CES_DATA", "GS", "ARCHI", "CROSS_AGENT", "CROSS_AGENT_TEST"}
SAFE_EVENTS = {"CLAIM", "CHECKPOINT_PASS", "CHECKPOINT_OPEN", "RELEASE", "RECOVERY_OPEN"}
MAX_EVENTS = 20
MAX_SIZE = 16000
STATE_PATH = "cross-agent/state.json"

class StateConflict(RuntimeError):
    pass

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def validate(data: dict[str, Any]):
    if not isinstance(data, dict) or data.get("schema_version") != "1.0":
        raise ValueError("INVALID_SCHEMA")
    if not isinstance(data.get("state_revision"), int) or data["state_revision"] < 1:
        raise ValueError("INVALID_STATE_REVISION")
    if set(data.get("workstreams", {})) != WORKSTREAMS:
        raise ValueError("WORKSTREAM_SET_DRIFT")
    if len(data.get("events", [])) > MAX_EVENTS:
        raise ValueError("EVENTS_UNBOUNDED")
    if any(item.get("owner") not in AGENTS | {None} for item in data["workstreams"].values()):
        raise ValueError("INVALID_OWNER")
    # Do not accidentally publish private Drive pointers, tokens, emails or records.
    payload = json.dumps(data, ensure_ascii=False)
    forbidden = [r"drive\.google\.com", r"docs\.google\.com", r"@", r"\b(?:ghp_|github_pat_|gho_)\w+", r"(?i)approach[\\/_ -]", r"(?i)password|secret|api[_-]?key"]
    for pattern in forbidden:
        if re.search(pattern, payload):
            raise ValueError("PUBLIC_METADATA_POLICY_STOP")
    if len(payload.encode("utf-8")) > MAX_SIZE:
        raise ValueError("MAX_PUBLIC_PAYLOAD_EXCEEDED")
    return data

def perform_transition(data: dict[str, Any], event: str, agent: str, scope: str, expected_revision: int) -> dict[str, Any]:
    validate(data)
    if agent not in AGENTS or scope not in WORKSTREAMS or event not in SAFE_EVENTS:
        raise ValueError("INVALID_TRANSITION_INPUT")
    if data["state_revision"] != expected_revision:
        raise StateConflict("STALE_BASELINE_STOP")
    state = copy.deepcopy(data)
    w = state["workstreams"][scope]
    owner = w.get("owner")
    if event == "CLAIM":
        if owner is not None:
            raise StateConflict("WRITER_CONFLICT_STOP")
        if w.get("status") == "IN_PROGRESS":
            raise StateConflict("UNKNOWN_WORK_IN_PROGRESS_STOP")
        w.update(owner=agent, status="IN_PROGRESS")
    else:
        if owner != agent:
            raise StateConflict("WRITER_CONFLICT_STOP")
        if event == "CHECKPOINT_PASS":
            w.update(owner=None, status="READY_FOR_HANDOFF")
        elif event == "CHECKPOINT_OPEN":
            w.update(owner=agent, status="IN_PROGRESS_OPEN")
        elif event == "RECOVERY_OPEN":
            w.update(owner=agent, status="RECOVERY_OPEN")
        elif event == "RELEASE":
            w.update(owner=None, status="RELEASED_OPEN")
    state["state_revision"] += 1
    state["events"] = (state.get("events", []) + [{
        "revision": state["state_revision"], "event": event,
        "agent": agent, "workstream": scope, "timestamp_utc": now(),
        "status": w["status"]
    }])[-MAX_EVENTS:]
    return validate(state)

class GitHubBackend:
    def __init__(self, repo: str, branch: str, token: str):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("INVALID_REPO")
        if not token:
            raise ValueError("GITHUB_TOKEN_MISSING")
        self.repo, self.branch, self.token = repo, branch, token
        self.api = f"https://api.github.com/repos/{repo}/contents/{STATE_PATH}"

    def request(self, method: str, url: str, body: dict | None = None):
        binary = None if body is None else json.dumps(body, ensure_ascii=False).encode()
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "vzp-cross-agent-state/1.0",
        }
        if binary is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, headers=headers, data=binary, method=method)
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code in (409, 412, 422):
                raise StateConflict("GITHUB_SHA_CONFLICT_STOP") from None
            raise RuntimeError("GITHUB_HTTP_" + str(e.code)) from None

    def read(self):
        response = self.request("GET", self.api + "?" + urllib.parse.urlencode({"ref": self.branch}))
        if response.get("encoding") != "base64":
            raise RuntimeError("UNEXPECTED_ENCODING")
        binary = base64.b64decode(response["content"])
        state = validate(json.loads(binary))
        return state, response["sha"]

    def write(self, state: dict, expected_sha: str, message: str):
        content = (json.dumps(validate(state), ensure_ascii=False, indent=2) + "\n").encode()
        result = self.request("PUT", self.api, {
            "message": message,
            "content": base64.b64encode(content).decode("ascii"),
            "sha": expected_sha,
            "branch": self.branch,
        })
        if not (result.get("commit") or {}).get("sha"):
            raise RuntimeError("COMMIT_WITHOUT_SHA")
        actual, blob_sha = self.read()
        if actual != state or blob_sha != (result.get("content") or {}).get("sha"):
            raise StateConflict("WRITE_READBACK_MISMATCH_STOP")
        return result["commit"]["sha"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="GitHub cross-agent snapshot state (public operational metadata only)")
    ap.add_argument("action", choices=["read", "verify", "claim", "checkpoint-pass", "checkpoint-open", "release", "recovery-open"])
    ap.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY", "romanhlavac/vzp-architecture"))
    ap.add_argument("--branch", default="main")
    ap.add_argument("--expected-revision", type=int)
    ap.add_argument("--agent", choices=sorted(AGENTS))
    ap.add_argument("--workstream", choices=sorted(WORKSTREAMS))
    args = ap.parse_args(argv)
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or ""
    api = GitHubBackend(args.repo, args.branch, token)
    state, sha = api.read()
    if args.action in ("read", "verify"):
        print(json.dumps({"revision": state["state_revision"], "blob_sha": sha,
            "storage_mode": state.get("storage_mode"), "workstreams": state["workstreams"]}, indent=2))
        return
    if args.expected_revision is None or not args.agent or not args.workstream:
        ap.error("mutation requires --expected-revision, --agent, --workstream")
    event = args.action.replace("-", "_").upper()
    updated = perform_transition(state, event, args.agent, args.workstream, args.expected_revision)
    commit_sha = api.write(updated, sha, f"cross-agent: {event} {args.workstream} rev {updated['state_revision']}")
    print(json.dumps({"status": "COMMITTED_AND_READBACK_PASS", "revision": updated["state_revision"],
                      "commit_sha": commit_sha, "workstream": args.workstream, "event": event}, indent=2))

if __name__ == "__main__":
    try:
        main()
    except StateConflict as error:
        print(str(error), file=sys.stderr)
        sys.exit(3)
    except (ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
