import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lock_origin import validate_origin, conflict_details, verified_claim
from prompt_state import Stop
import test_lock_provenance


class OriginRecordTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_lock_provenance.ProvenanceTests(); self.fixture.setUp()
        self.origin = dict(key='c'*32, scope=self.fixture.scope,
                           actor=self.fixture.a, created_utc='2026-10-26T00:00:00Z',
                           request_id='d'*32, purpose='Synthetic isolated test', platform='Unit test')
    def validate(self, r):
        return validate_origin(r, key='c'*32, scope=self.fixture.scope, actor=self.fixture.a)
    def test_missing_optional_metadata_is_valid(self):
        self.validate(self.origin)
    def test_required_metadata_types_identity(self):
        for key in self.origin:
            r=copy.deepcopy(self.origin); del r[key]
            with self.subTest(key=key),self.assertRaises(Stop):self.validate(r)
        for delta in ({'request_id':1},{'created_utc':'2026-02-30T00:00:00Z'},
                      {'purpose':None},{'scope':'GS'},{'chat_id':123}):
            with self.subTest(delta=delta),self.assertRaises(Stop):self.validate(dict(self.origin,**delta))
    def test_readback_mismatch_does_not_claim(self):
        with self.assertRaises(Stop):
            verified_claim(self.fixture.base,saved_origin=self.origin,readback_origin={},
                           key='c'*32,actor=self.fixture.a,scope=self.fixture.scope,
                           expected_revision=self.fixture.base['state_revision'])
        self.assertIsNone(self.fixture.base['workstreams'][self.fixture.scope]['owner'])
    def test_conflict_legacy_and_verified_navigation(self):
        s=self.fixture.claim()
        with self.assertRaises(Stop):conflict_details(s,self.fixture.scope)
        self.origin['chat_url']='https://example.invalid/synthetic-private-chat'
        d=conflict_details(s,self.fixture.scope,self.origin)
        self.assertEqual(d['origin']['chat_url'],self.origin['chat_url'])
        del s['workstreams'][self.fixture.scope]['claim_origin_key']
        self.assertEqual(conflict_details(s,self.fixture.scope)['origin_status'],'LEGACY_ORIGIN_UNAVAILABLE')
