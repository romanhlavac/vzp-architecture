import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transport_guard import qualify

class TransportMetadataGateTests(unittest.TestCase):
    def evidence(self):
        flags = {
            "transport": "B",
            "fresh_baseline": True,
            "transition_verified": True,
            "scope_diff_verified": True,
            "remote_readback": True,
            "server_stale_rejection": True,
            "privacy_review": True,
            "direct_parent": True,
            "non_force": True,
            "no_retry_rebase_merge": True,
            "history_protection_verified": True,
            "candidate_commit_inspected": True,
        }
        return flags

    def test_missing_message_fails(self):
        with self.assertRaises(ValueError):
            qualify(self.evidence())

    def test_leaking_session_fails(self):
        evidence = self.evidence()
        evidence["candidate_commit_message"] = (
            "cross-agent: CLAIM CROSS_AGENT_TEST rev 60 (CLAUDE)\n\n"
            "Claude-Session: https://claude.ai/code/session_example\n"
        )
        with self.assertRaises(ValueError):
            qualify(evidence)

    def test_correct_single_line_accepted(self):
        evidence = self.evidence()
        evidence["candidate_commit_message"] = (
            "cross-agent: HANDOFF_OPEN CROSS_AGENT_TEST rev 61 (CLAUDE)\n"
        )
        self.assertEqual(qualify(evidence), "SERVER_SIDE_STALE_WRITE_REJECTION_PASS")

    def test_only_attestation_not_proof(self):
        evidence = self.evidence()
        evidence["candidate_commit_message"] = (
            "cross-agent: HANDOFF_OPEN CROSS_AGENT_TEST rev 61 (CLAUDE)\n"
        )
        evidence["candidate_commit_inspected"] = False
        with self.assertRaises(ValueError):
            qualify(evidence)
