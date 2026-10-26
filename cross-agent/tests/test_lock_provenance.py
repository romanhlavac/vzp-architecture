import copy, json, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prompt_state import transition, verify_transition, validate, Stop

class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.base=json.loads((Path(__file__).resolve().parents[1]/'state.json').read_text())
        self.scope='CROSS_AGENT_TEST'
        self.base['workstreams'][self.scope]['owner']=None
        self.a={'agent':'GPT','run_id':'a'*32}
        self.b={'agent':'CLAUDE','run_id':'b'*32}
    def move(self,s,event,actor=None,**kw):
        return transition(s,expected_revision=s['state_revision'],scope=self.scope,actor=actor or self.a,event=event,**kw)
    def claim(self):
        return self.move(self.base,'CLAIM',claim_origin_key='c'*32,origin_verified=True)
    def release_args(self,s):
        return dict(expected_revision=s['state_revision'],scope=self.scope,actor=self.b,event='OWNER_AUTHORIZED_RELEASE',expected_owner=self.a,authorization_key='d'*32,private_artifact_key='e'*32,native_readback=True,recovery_authorized=True,work_code='RECOVERY')
    def test_origin_required(self):
        for kw in ({},{'claim_origin_key':'c'*32},{'claim_origin_key':'https://private','origin_verified':True},{'claim_origin_key':'c'*32,'origin_verified':1}):
            with self.subTest(kw=kw),self.assertRaises(Stop):self.move(self.base,'CLAIM',**kw)
    def test_optional_chat_metadata_not_public(self):
        s=self.claim();validate(s)
        self.assertEqual(s['workstreams'][self.scope]['claim_origin_key'],'c'*32)
        verify_transition(self.base,s,origin_verified=True)
        s['workstreams'][self.scope]['chat_url']='https://private'
        with self.assertRaises(Stop):validate(s)
    def test_origin_immutable(self):
        with self.assertRaises(Stop):self.move(self.claim(),'CHECKPOINT_OPEN',claim_origin_key='f'*32,native_readback=True)
    def test_release_preserves_work(self):
        s=self.claim();before=copy.deepcopy(s);r=transition(s,**self.release_args(s))
        w=r['workstreams'][self.scope]
        self.assertIsNone(w['owner']);self.assertEqual(w['status'],'IN_PROGRESS_OPEN')
        self.assertEqual(w['checkpoint'],s['workstreams'][self.scope]['checkpoint'])
        self.assertEqual(w['private_artifact_key'],s['workstreams'][self.scope]['private_artifact_key'])
        self.assertEqual(s,before);verify_transition(s,r,recovery_authorized=True)
    def test_release_missing_or_wrong_evidence(self):
        s=self.claim();good=self.release_args(s)
        for delta in ({'expected_owner':self.b},{'expected_owner':None},{'recovery_authorized':False},{'recovery_authorized':1},{'native_readback':False},{'authorization_key':None},{'private_artifact_key':None},{'expected_revision':s['state_revision']-1}):
            with self.subTest(delta=delta),self.assertRaises(Stop):transition(s,**dict(good,**delta))
    def test_race_and_delayed_writer(self):
        s=self.claim();args=self.release_args(s);r=transition(s,**args)
        with self.assertRaises(Stop):transition(r,**args)
        with self.assertRaises(Stop):self.move(r,'HANDOFF_OPEN',native_readback=True)
        with self.assertRaises(Stop):self.move(s,'CLAIM',actor=self.b,claim_origin_key='f'*32,origin_verified=True)
    def test_other_scope_tamper(self):
        s=self.claim();r=transition(s,**self.release_args(s));r['workstreams']['GS']['status']='IDLE'
        with self.assertRaises(Stop):verify_transition(s,r,recovery_authorized=True)
    def test_legacy_read_and_release(self):
        s=self.claim();del s['workstreams'][self.scope]['claim_origin_key'];validate(s)
        r=transition(s,**self.release_args(s));self.assertIsNone(r['workstreams'][self.scope]['owner'])
    def test_symmetric_actors(self):
        self.a,self.b=self.b,self.a;self.test_release_preserves_work()
    def test_unpublished_origin_not_active(self):
        before=copy.deepcopy(self.base);self.claim();self.assertEqual(before,self.base)

if __name__=='__main__':unittest.main()
