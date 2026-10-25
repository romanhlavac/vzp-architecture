import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"cross-agent"))
from transport_guard import qualify
class TransportTests(unittest.TestCase):
 def test_every_b_invariant_required(self):
  keys="fresh_baseline transition_verified scope_diff_verified remote_readback server_stale_rejection privacy_review direct_parent non_force no_retry_rebase_merge history_protection_verified".split()
  e=dict.fromkeys(keys,True);e["transport"]="B"
  self.assertEqual(qualify(e),"SERVER_SIDE_STALE_WRITE_REJECTION_PASS")
  for k in keys:
   bad=dict(e);bad[k]=False
   with self.assertRaises(ValueError):qualify(bad)
 def test_a_does_not_require_http_code(self):
  e=dict.fromkeys("fresh_baseline transition_verified scope_diff_verified remote_readback server_stale_rejection privacy_review".split(),True);e["transport"]="A"
  self.assertEqual(qualify(e),"SERVER_SIDE_STALE_WRITE_REJECTION_PASS")
