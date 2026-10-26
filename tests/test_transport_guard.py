import sys
import pathlib
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'cross-agent'))
from transport_guard import qualify

class TransportTests(unittest.TestCase):
    def evidence(self,transport='A'):
        e=dict.fromkeys(('fresh_baseline transition_verified scope_diff_verified '
                        'server_stale_rejection privacy_review write_permission').split(),True)
        e['transport']=transport
        return e
    def test_a_prepublication_does_not_claim_future_readback(self):
        self.assertEqual(qualify(self.evidence()),'PREPUBLICATION_PASS')
        with self.assertRaises(ValueError): qualify(self.evidence(),phase='postpublish')
        self.assertEqual(qualify(dict(self.evidence(),remote_readback=True),phase='postpublish'),
                         'SERVER_SIDE_STALE_WRITE_REJECTION_PASS')
    def test_b_boolean_evidence_cannot_replace_object(self):
        e=dict(self.evidence('B'),non_force=True,no_retry_rebase_merge=True,
               history_protection_verified=True,candidate_commit_inspected=True,
               candidate_commit_message='cross-agent: CLAIM CROSS_AGENT_TEST rev 2 (GPT)\n')
        with self.assertRaisesRegex(ValueError,'CALLER_COMMIT_ATTESTATION'): qualify(e)
    def test_a_missing_permission_blocked(self):
        with self.assertRaisesRegex(ValueError,'WRITE_BLOCKED'):
            qualify(dict(self.evidence(),write_permission=False))
