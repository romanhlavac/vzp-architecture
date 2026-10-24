import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cross-agent"))
from state_cli import perform_transition, StateConflict, validate

class TestState(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.live = json.loads((ROOT / "cross-agent" / "state.json").read_text())
        cls.base = copy.deepcopy(cls.live)
        cls.base["state_revision"] = 3
        cls.base["workstreams"]["CROSS_AGENT_TEST"] = {"status": "IDLE", "owner": None}
        cls.base["events"] = []

    def test_baseline(self):
        self.assertGreaterEqual(validate(self.live)["state_revision"], 1)

    def test_claim_checkpoint(self):
        s = perform_transition(self.base, "CLAIM", "GPT", "CROSS_AGENT_TEST", 3)
        self.assertEqual(s["workstreams"]["CROSS_AGENT_TEST"]["owner"], "GPT")
        new = perform_transition(s, "CHECKPOINT_PASS", "GPT", "CROSS_AGENT_TEST", 4)
        self.assertEqual(new["workstreams"]["CROSS_AGENT_TEST"]["status"], "READY_FOR_HANDOFF")
        self.assertIsNone(new["workstreams"]["CROSS_AGENT_TEST"]["owner"])
        self.assertEqual(new["state_revision"], 5)

    def test_stale_revision_stop(self):
        with self.assertRaisesRegex(StateConflict, "STALE_BASELINE_STOP"):
            perform_transition(self.base, "CLAIM", "GPT", "CROSS_AGENT_TEST", 2)

    def test_foreign_writer_stop(self):
        s = perform_transition(self.base, "CLAIM", "GPT", "CROSS_AGENT_TEST", 3)
        with self.assertRaisesRegex(StateConflict, "WRITER_CONFLICT_STOP"):
            perform_transition(s, "CHECKPOINT_PASS", "CLAUDE", "CROSS_AGENT_TEST", 4)
        with self.assertRaisesRegex(StateConflict, "WRITER_CONFLICT_STOP"):
            perform_transition(s, "CLAIM", "CURSOR", "CROSS_AGENT_TEST", 4)

    def test_public_data_firewall(self):
        bad = copy.deepcopy(self.base)
        bad["events"].append({"revision": 3, "event": "LEAK", "url": "https://drive.google.com/file/d/sensitive"})
        with self.assertRaisesRegex(ValueError, "PUBLIC_METADATA_POLICY_STOP"):
            validate(bad)

    def test_invalid_agent_scope(self):
        with self.assertRaisesRegex(ValueError, "INVALID_TRANSITION_INPUT"):
            perform_transition(self.base, "CLAIM", "UNKNOWN_AGENT", "CROSS_AGENT_TEST", 3)

if __name__ == "__main__": unittest.main()
