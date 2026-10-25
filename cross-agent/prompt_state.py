#!/usr/bin/env python3
"""Prompt-driven Git state, strict public metadata, session ownership and CAS.

Native artifacts are NOT covered by Git's single-file compare-and-swap.
No free-text payload or private locator is accepted. An opaque key is resolved
only inside the private project folder. Callers still review classification.
"""
from __future__ import annotations
import argparse
import copy
import datetime as dt
import json
import re
from pathlib import Path

SCOPES = {'METHOD','SOURCE','CES_1B','CES_DATA','GS','ARCHI','CROSS_AGENT','CROSS_AGENT_TEST'}
AGENTS = {'GPT','CLAUDE','CURSOR'}
STATUSES = {'ACTIVE_WORKING','IDENTITY_REVALIDATED','WORKING_DEMO_VISUAL_OPEN',
            'ACTIVATION_UNVERIFIED','LIVE_MASTER','MODEL_MASTER_NOT_VERIFIED',
            'IDLE','IN_PROGRESS','IN_PROGRESS_OPEN','READY_FOR_HANDOFF','RECOVERY_OPEN'}
EVENTS = {'CLAIM','CHECKPOINT_OPEN','HANDOFF_OPEN','CHECKPOINT_PASS','RECOVERY_OPEN','RECONCILE'}
WORK_CODES = {'IMPLEMENTATION','ACCEPTANCE','PROJECT_WORK','RECOVERY'}
NEXT_CODES = {'CONTINUE','CLAUDE_READ','CLAUDE_WRITE','GPT_RESUME','RECONCILE','USER_DECISION'}
MAX_EVENTS = 30

class Stop(RuntimeError):
    pass

def require(ok, code):
    if not ok:
        raise Stop(code)

def keys(value, expected):
    require(isinstance(value,dict) and set(value)==set(expected.split()), 'PUBLIC_SCHEMA_STOP')

def integer(n):
    return type(n) is int and n > 0

def hexvalue(value, length, nullable=False):
    return (nullable and value is None) or (isinstance(value,str) and re.fullmatch('[0-9a-f]{'+str(length)+'}',value) is not None)

def identity(owner):
    keys(owner,'agent run_id')
    require(owner['agent'] in AGENTS and hexvalue(owner['run_id'],32),'INVALID_RUN_STOP')

def record(r):
    keys(r,'revision event actor scope timestamp_utc work_code next_code private_artifact_key evidence_commit native_readback authorization_key')
    identity(r['actor'])
    require(integer(r['revision']) and r['event'] in EVENTS and r['scope'] in SCOPES,'INVALID_EVENT_STOP')
    require(r['work_code'] in WORK_CODES and r['next_code'] in NEXT_CODES,'PUBLIC_CODE_STOP')
    require(hexvalue(r['private_artifact_key'],32,True) and hexvalue(r['authorization_key'],32,True)
            and hexvalue(r['evidence_commit'],40,True),'PRIVATE_LOCATOR_STOP')
    require(type(r['native_readback']) is bool,'INVALID_EVIDENCE_STOP')
    require(isinstance(r['timestamp_utc'],str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',r['timestamp_utc']) is not None,'INVALID_TIME_STOP')
    try: dt.datetime.strptime(r['timestamp_utc'],'%Y-%m-%dT%H:%M:%SZ')
    except ValueError: raise Stop('INVALID_TIME_STOP') from None
    if r['event']=='CHECKPOINT_PASS':
        require(r['native_readback'] and r['evidence_commit'] is not None,'EVIDENCE_REQUIRED_STOP')
    if r['event']=='RECONCILE':
        require(r['authorization_key'] is not None and r['native_readback'],'RECONCILE_AUTHORIZATION_REQUIRED_STOP')

def validate(state):
    keys(state,'schema_version state_revision authority deployment workstreams events')
    require(state['schema_version']=='2.0' and state['authority']=='GIT_OPERATIONAL_STATE','AUTHORITY_STOP')
    # End-to-end PASS is a separately reviewed acceptance report, never implied here.
    require(state['deployment'] in {'IMPLEMENTING','ACTIVE_ACCEPTANCE_PENDING'},'DEPLOYMENT_STOP')
    require(integer(state['state_revision']),'INVALID_REVISION_STOP')
    require(isinstance(state['workstreams'],dict) and set(state['workstreams'])==SCOPES,'SCOPE_STOP')
    for scope,w in state['workstreams'].items():
        keys(w,'status owner checkpoint private_artifact_key')
        require(w['status'] in STATUSES,'INVALID_SCOPE_STOP')
        require(hexvalue(w['private_artifact_key'],32,True),'PRIVATE_LOCATOR_STOP')
        if w['owner'] is not None: identity(w['owner'])
        require(w['status']!='IN_PROGRESS' or w['owner'] is not None,'UNKNOWN_WRITER_STOP')
        require(w['status']!='READY_FOR_HANDOFF' or w['owner'] is None,'INVALID_HANDOFF_STOP')
        if w['checkpoint'] is not None:
            record(w['checkpoint'])
            require(w['checkpoint']['scope']==scope and w['checkpoint']['revision']<=state['state_revision'],'CHECKPOINT_REVISION_STOP')
    require(isinstance(state['events'],list) and len(state['events'])<=MAX_EVENTS,'EVENT_BOUND_STOP')
    previous=0
    for event in state['events']:
        record(event)
        require(previous<event['revision']<=state['state_revision'],'EVENT_ORDER_STOP')
        previous=event['revision']
    if state['events']: require(previous==state['state_revision'],'LAST_EVENT_STOP')
    require(len(json.dumps(state).encode())<40000,'SIZE_STOP')
    return state

def transition(state, *, expected_revision, actor, scope, event, work_code='ACCEPTANCE',
               next_code='CONTINUE', private_artifact_key=None, evidence_commit=None,
               native_readback=False, authorization_key=None, recovery_authorized=False, timestamp_utc=None):
    validate(state)
    identity(actor)
    require(type(expected_revision) is int and expected_revision==state['state_revision'],'STALE_REVISION_STOP')
    require(scope in SCOPES and event in EVENTS,'TRANSITION_STOP')
    current=state['workstreams'][scope]
    owner=current['owner']
    if current['status']=='RECOVERY_OPEN':
        require(event=='RECONCILE','RECOVERY_STOP')
        require(recovery_authorized and authorization_key is not None and native_readback,'RECONCILE_AUTHORIZATION_REQUIRED_STOP')
    else:
        require(event!='RECONCILE','NOT_IN_RECOVERY_STOP')
        if event=='CLAIM': require(owner is None,'FOREIGN_WRITER_STOP')
        else: require(owner==actor,'FOREIGN_WRITER_STOP')
    if event in {'CLAIM','RECOVERY_OPEN'}:
        require(private_artifact_key in (None,current['private_artifact_key']),'UNVERIFIED_CONTEXT_STOP')
    if event=='CHECKPOINT_PASS': require(native_readback and evidence_commit is not None,'EVIDENCE_REQUIRED_STOP')
    if event in {'CHECKPOINT_OPEN','HANDOFF_OPEN','CHECKPOINT_PASS'}:
        require(native_readback,'NATIVE_READBACK_REQUIRED_STOP')
    result=copy.deepcopy(state)
    w=result['workstreams'][scope]
    w['status']={'CLAIM':'IN_PROGRESS','CHECKPOINT_OPEN':'IN_PROGRESS_OPEN',
        'HANDOFF_OPEN':'IN_PROGRESS_OPEN','CHECKPOINT_PASS':'READY_FOR_HANDOFF',
        'RECOVERY_OPEN':'RECOVERY_OPEN','RECONCILE':'IN_PROGRESS_OPEN'}[event]
    w['owner']=None if event in {'HANDOFF_OPEN','CHECKPOINT_PASS','RECONCILE'} else copy.deepcopy(actor)
    if private_artifact_key is not None: w['private_artifact_key']=private_artifact_key
    result['state_revision']+=1
    r={'revision':result['state_revision'],'event':event,'actor':copy.deepcopy(actor),'scope':scope,
       'timestamp_utc':timestamp_utc or dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
       'work_code':work_code,'next_code':next_code,'private_artifact_key':w['private_artifact_key'],
       'evidence_commit':evidence_commit,'native_readback':native_readback,'authorization_key':authorization_key}
    # CLAIM/RECOVERY retain the last saved work checkpoint; events record the claim.
    if event not in {'CLAIM','RECOVERY_OPEN'}: w['checkpoint']=copy.deepcopy(r)
    result['events']=(result['events']+[r])[-MAX_EVENTS:]
    return validate(result)

def verify_transition(before, after, *, recovery_authorized=False):
    validate(before); validate(after)
    require(after['state_revision']==before['state_revision']+1 and after['events'],'REVISION_STEP_STOP')
    r=after['events'][-1]
    kwargs={k:v for k,v in r.items() if k!='revision'}
    expected=transition(before,expected_revision=before['state_revision'],recovery_authorized=recovery_authorized,**kwargs)
    require(expected==after,'UNAUTHORIZED_STATE_DIFF_STOP')
    return after

def save_local(path,state):
    Path(path).write_text(json.dumps(validate(state),indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='command',required=True)
    v=sub.add_parser('validate'); v.add_argument('state')
    t=sub.add_parser('transition'); t.add_argument('state'); t.add_argument('request'); t.add_argument('output')
    c=sub.add_parser('compare'); c.add_argument('before'); c.add_argument('after'); c.add_argument('--recovery-authorized',action='store_true')
    args=ap.parse_args()
    read=lambda p:json.loads(Path(p).read_text())
    if args.command=='validate': validate(read(args.state))
    elif args.command=='compare': verify_transition(read(args.before),read(args.after),recovery_authorized=args.recovery_authorized)
    else: save_local(args.output,transition(read(args.state),**read(args.request)))
    print('PASS')

if __name__=='__main__': main()
