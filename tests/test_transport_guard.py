import sys
import pathlib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "cross-agent"))
from transport_guard import qualify

class TransportTests(unittest.TestCase):
    def test_every_b_invariant_required(self):
        keys = (
            "fresh_baseline transition_verified scope_diff_verified "
            "remote_readback server_stale_rejection privacy_review "
            "direct_parent non_force no_retry_rebase_merge "
            "history_protection_verified candidate_commit_inspected"
        ).split()
        evidence = dict.fromkeys(keys, True)
        evidence["transport"] = "B"
        evidence["candidate_commit_message"] = (
            "cross-agent: CLAIM CROSS_AGENT_TEST rev 60 (CLAUDE)\n"
        )
        self.assertEqual(qualify(evidence), "SERVER_SIDE_STALE_WRITE_REJECTION_PASS")
        for key in keys:
            bad = dict(evidence)
            bad[key] = False
            with self.subTest(key=key), self.assertRaises(ValueError):
                qualify(bad)

    def test_missing_candidate_message_blocked(self):
        evidence = dict.fromkeys(
            "fresh_baseline transition_verified scope_diff_verified "
            "remote_readback server_stale_rejection privacy_review "
            "direct_parent non_force no_retry_rebase_merge "
            "history_protection_verified candidate_commit_inspected".split(), True
        )
        evidence["transport"] = "B"
        with self.assertRaises(ValueError):
            qualify(evidence)

    def test_a_does_not_require_http_code(self):
        evidence = dict.fromkeys(
            "fresh_baseline transition_verified scope_diff_verified "
            "remote_readback server_stale_rejection privacy_review".split(), True
        )
        evidence["transport"] = "A"
        self.assertEqual(qualify(evidence), "SERVER_SIDE_STALE_WRITE_REJECTION_PASS")
