"""Verify each changed state snapshot, not only the final shape. No network writes."""
import json, os, subprocess
from prompt_state import validate, verify_transition, require

def git(*args): return subprocess.check_output(['git',*args],text=True)
def state(ref): return json.loads(git('show',ref+':cross-agent/state.json'))
validate(json.load(open('cross-agent/state.json')))
before=os.getenv('BEFORE_SHA','')
head=os.getenv('GITHUB_SHA','HEAD')
if before and set(before)!={'0'}:
 for commit in git('rev-list','--reverse',before+'..'+head).split():
  parent=git('rev-parse',commit+'^').strip()
  old,new=state(parent),state(commit)
  if old==new: continue
  if old.get('schema_version')=='1.0':
   require(parent=='f8e506e1a357a2e0f9b884bc83c89c39b8bb74ba' and old['state_revision']==14 and new['state_revision']==15,'MIGRATION_BASELINE_STOP')
   require(not new['events'] and all(w['owner'] is None for w in new['workstreams'].values()),'MIGRATION_OWNER_STOP')
   validate(new)
  else:
   event=new['events'][-1]
   # The owner authorized isolated recovery fixtures. Business recovery needs
   # an explicitly reviewed implementation; a private key is not proof by itself.
   # CI validates public structure only, never attests private user mandate.
   allow=event['event'] in {'RECONCILE','OWNER_AUTHORIZED_RELEASE'}
   verify_transition(old,new,recovery_authorized=allow,origin_verified=True)
print('STATE_SCHEMA_AND_TRANSITIONS_PASS')
