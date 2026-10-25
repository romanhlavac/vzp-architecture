import copy, json, pathlib, sys, unittest
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cross-agent'))
from prompt_state import validate, transition, verify_transition, Stop
from state_cli import GitHubBackend, StateConflict

class PromptStateTests(unittest.TestCase):
 def setUp(self):
  self.state=json.loads((ROOT/'cross-agent/state.json').read_text())
  # Independent synthetic fixture, never a claim that Claude executed anything.
  self.state['state_revision']=1; self.state['events']=[]
  for w in self.state['workstreams'].values():
   w.update(status='IDLE',owner=None,checkpoint=None,private_artifact_key=None)
  self.actor={'agent':'GPT','run_id':'1'*32}
 def move(self,s,event,**kw):
  return transition(s,expected_revision=s['state_revision'],actor=self.actor,scope='CROSS_AGENT_TEST',event=event,**kw)
 def test_live_schema(self): validate(json.loads((ROOT/'cross-agent/state.json').read_text()))
 def test_claim_open_handoff_preserves_unfinished(self):
  claimed=self.move(self.state,'CLAIM')
  opened=self.move(claimed,'CHECKPOINT_OPEN',native_readback=True)
  self.assertEqual(opened['workstreams']['CROSS_AGENT_TEST']['owner'],self.actor)
  handed=self.move(opened,'HANDOFF_OPEN',native_readback=True,next_code='CLAUDE_READ')
  w=handed['workstreams']['CROSS_AGENT_TEST']
  self.assertEqual(w['status'],'IN_PROGRESS_OPEN'); self.assertIsNone(w['owner'])
  verify_transition(opened,handed)
  self.assertEqual(self.state['state_revision'],1)
 def test_stale_revision(self):
  with self.assertRaisesRegex(Stop,'STALE_REVISION_STOP'):
   transition(self.state,expected_revision=0,actor=self.actor,scope='CROSS_AGENT_TEST',event='CLAIM')
 def test_same_agent_foreign_session(self):
  s=self.move(self.state,'CLAIM'); other={'agent':'GPT','run_id':'2'*32}
  with self.assertRaisesRegex(Stop,'FOREIGN_WRITER_STOP'):
   transition(s,expected_revision=2,actor=other,scope='CROSS_AGENT_TEST',event='HANDOFF_OPEN',native_readback=True)
 def test_recovery_requires_explicit_authorized_reconcile(self):
  s=self.move(self.move(self.state,'CLAIM'),'RECOVERY_OPEN')
  for event in ['CLAIM','CHECKPOINT_OPEN','HANDOFF_OPEN','CHECKPOINT_PASS']:
   with self.assertRaisesRegex(Stop,'RECOVERY_STOP'):self.move(s,event,native_readback=True,evidence_commit='a'*40)
  with self.assertRaisesRegex(Stop,'RECONCILE_AUTHORIZATION_REQUIRED_STOP'):self.move(s,'RECONCILE')
  new=self.move(s,'RECONCILE',native_readback=True,recovery_authorized=True,authorization_key='a'*32)
  verify_transition(s,new,recovery_authorized=True)
  self.assertEqual(new['workstreams']['CROSS_AGENT_TEST']['status'],'IN_PROGRESS_OPEN')
 def test_unverified_ready_blocked(self):
  s=self.move(self.state,'CLAIM')
  with self.assertRaisesRegex(Stop,'EVIDENCE_REQUIRED_STOP'):self.move(s,'CHECKPOINT_PASS')
 def test_unknown_fields_and_free_text_rejected(self):
  for mutation in [lambda s:s.update(note='private'),lambda s:s['workstreams']['METHOD'].update(url='private')]:
   s=copy.deepcopy(self.state);mutation(s)
   with self.assertRaises(Stop):validate(s)
  with self.assertRaisesRegex(Stop,'PUBLIC_CODE_STOP'):self.move(self.state,'CLAIM',work_code='BUSINESS_DESCRIPTION')
  with self.assertRaisesRegex(Stop,'PRIVATE_LOCATOR_STOP'):self.move(self.move(self.state,'CLAIM'),'CHECKPOINT_OPEN',native_readback=True,private_artifact_key='private-drive-id')
 def test_cross_scope_tampering(self):
  s=self.move(self.state,'CLAIM');s['workstreams']['METHOD']['status']='IN_PROGRESS_OPEN'
  with self.assertRaisesRegex(Stop,'UNAUTHORIZED_STATE_DIFF_STOP'):verify_transition(self.state,s)
 def test_backend_stale_sha_no_put(self):
  api=GitHubBackend('example/repo','test','synthetic-test-only')
  with mock.patch.object(api,'read',return_value=(self.state,'a'*40)), mock.patch.object(api,'request') as request:
   with self.assertRaisesRegex(StateConflict,'GITHUB_SHA_CONFLICT_STOP'):
    api.write(self.move(self.state,'CLAIM'),'b'*40,'cross-agent: checkpoint')
   request.assert_not_called()
 def test_backend_readback_detects_drift(self):
  s=self.move(self.state,'CLAIM');api=GitHubBackend('example/repo','test','synthetic-test-only')
  with mock.patch.object(api,'read',side_effect=[(self.state,'a'*40),(self.state,'c'*40)]),mock.patch.object(api,'request',return_value={'commit':{'sha':'d'*40},'content':{'sha':'b'*40}}):
   with self.assertRaisesRegex(StateConflict,'WRITE_READBACK_MISMATCH_STOP'):api.write(s,'a'*40,'cross-agent: checkpoint')
 def test_legacy_transition_cannot_mutate_new_state(self):
  from state_cli import perform_transition
  with self.assertRaisesRegex(StateConflict,'LEGACY_WRITER_DISABLED'):
   perform_transition(self.state,'CLAIM','GPT','CROSS_AGENT_TEST',1)
