#!/usr/bin/env python3
"""Sanitized per-turn continuity records. No transcripts or client content."""
from __future__ import annotations
import argparse, copy, json, os, re, sys
from state_cli import GitHubBackend, StateConflict, validate

AGENTS={"GPT","CLAUDE"}
PHASES={"OPEN","VERIFIED","BLOCKED"}
SYSTEMS={"NONE","GITHUB","MIRO","GOOGLE_DRIVE","GOOGLE_SLIDES","ARCHI"}
CODE=re.compile(r"^[A-Z][A-Z0-9_]{1,47}$")

def context_for_turn(state):
    validate(state)
    c=state.get("continuity",{})
    scope=c.get("latest_workstream")
    return {"revision":state["state_revision"],"storage_mode":state["storage_mode"],
            "latest_workstream":scope,"last":c.get("streams",{}).get(scope),
            "source_of_truth":"GITHUB_STATE" if state["storage_mode"]=="ACTIVE_GPT_CLAUDE" else "GD_OPERATING_STATE",
            "native_artifact_readback_required":True}

def transition(state,*,expected_revision,agent,scope,phase,work_code,next_code,
               artifact_system="NONE",evidence_commit=""):
    validate(state)
    if state["state_revision"]!=expected_revision:
        raise StateConflict("STALE_BASELINE_STOP")
    if agent not in AGENTS or scope not in state["workstreams"]:
        raise ValueError("INVALID_AGENT_OR_SCOPE")
    if phase not in PHASES or artifact_system not in SYSTEMS:
        raise ValueError("INVALID_PHASE_OR_SYSTEM")
    if not CODE.fullmatch(work_code) or not CODE.fullmatch(next_code):
        raise ValueError("UNSAFE_CODE_STOP")
    if evidence_commit and not re.fullmatch(r"[0-9a-f]{40}",evidence_commit):
        raise ValueError("INVALID_EVIDENCE_COMMIT")
    if state["storage_mode"]!="ACTIVE_GPT_CLAUDE" and scope!="CROSS_AGENT_TEST":
        raise StateConflict("PILOT_SCOPE_STOP")
    unit=state["workstreams"][scope]
    if unit.get("owner") not in (None,agent):
        raise StateConflict("FOREIGN_WRITER_STOP")
    if unit.get("owner") is None and unit.get("status") in ("IN_PROGRESS","RECOVERY_OPEN"):
        raise StateConflict("UNKNOWN_WRITER_STOP")
    if phase=="VERIFIED" and not evidence_commit:
        raise StateConflict("VERIFIED_REQUIRES_EVIDENCE_STOP")
    out=copy.deepcopy(state)
    revision=out["state_revision"]+1
    c=out.setdefault("continuity",{"version":1,"streams":{}})
    if c.get("version")!=1:
        raise StateConflict("UNKNOWN_CONTINUITY_VERSION_STOP")
    c["latest_workstream"]=scope
    c["streams"][scope]={"revision":revision,"agent":agent,"phase":phase,
        "work_code":work_code,"next_code":next_code,
        "artifact_system":artifact_system,"evidence_commit":evidence_commit}
    out["state_revision"]=revision
    out["events"]=(out.get("events",[])+[{"revision":revision,
        "event":"CONTEXT_UPDATE","agent":agent,"workstream":scope,"status":phase}])[-20:]
    return validate(out)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["read","publish"])
    p.add_argument("--repo",default="romanhlavac/vzp-architecture")
    p.add_argument("--agent",choices=sorted(AGENTS))
    p.add_argument("--workstream")
    p.add_argument("--phase",choices=sorted(PHASES))
    p.add_argument("--work-code")
    p.add_argument("--next-code")
    p.add_argument("--artifact-system",choices=sorted(SYSTEMS),default="NONE")
    p.add_argument("--evidence-commit",default="")
    p.add_argument("--expected-revision",type=int)
    args=p.parse_args()
    token=os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or ""
    if not token:
        raise RuntimeError("GITHUB_TOKEN_REQUIRED_FOR_CLI; connector may use native fetch/update")
    api=GitHubBackend(args.repo,"main",token)
    state,blob=api.read()
    if args.action=="read":
        print(json.dumps(context_for_turn(state),indent=2))
        return
    if any(x is None for x in (args.agent,args.workstream,args.phase,args.work_code,args.next_code,args.expected_revision)):
        p.error("publish requires agent, scope, phase, codes, and expected revision")
    nxt=transition(state,expected_revision=args.expected_revision,agent=args.agent,
      scope=args.workstream,phase=args.phase,work_code=args.work_code,next_code=args.next_code,
      artifact_system=args.artifact_system,evidence_commit=args.evidence_commit)
    sha=api.write(nxt,blob,f"cross-agent: continuity {args.workstream} rev {nxt['state_revision']}")
    print(json.dumps({"revision":nxt["state_revision"],"commit":sha,"status":"READBACK_PASS"}))

if __name__=="__main__":
    try: main()
    except (ValueError,RuntimeError,StateConflict) as e:
        print(str(e),file=sys.stderr)
        sys.exit(3)
