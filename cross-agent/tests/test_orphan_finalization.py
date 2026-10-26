"""Cross-agent lifecycle smoke checks."""
from __future__ import annotations
import copy, json, sys, unittest
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from prompt_state import Stop, transition, finalize_phase, verify_transition
base = json.loads((root / "state.json").read_text())
gpt = {"agent":"GPT", "run_id":"a"*32}
class LifecycleTests(unittest.TestCase):
    def test_orphan_requires_approval(self):
        with self.assertRaises(Stop):
            transition(base, expected_revision=base["state_revision"], actor=gpt,
                       scope="CES_1B", event="ORPHAN_RECONCILE")
    def test_orphan_authorized_and_verified(self):
        result = transition(base, expected_revision=base["state_revision"], actor=gpt,
            scope="CES_1B", event="ORPHAN_RECONCILE", work_code="RECOVERY",
            authorization_key="b"*32, private_artifact_key="c"*32,
            native_readback=True, recovery_authorized=True)
        self.assertIsNone(result["workstreams"]["CES_1B"]["owner"])
        self.assertEqual(result["workstreams"]["CES_1B"]["status"], "IN_PROGRESS_OPEN")
        verify_transition(base,result,recovery_authorized=True)
    def test_normal_finalization(self):
        active = transition(base, expected_revision=base["state_revision"], actor=gpt,
                            scope="METHOD", event="CLAIM")
        out = finalize_phase(active, expected_revision=active["state_revision"],
                             actor=gpt, scope="METHOD", native_readback=True,
                             private_artifact_key="c"*32)
        self.assertIsNone(out["workstreams"]["METHOD"]["owner"])
        verify_transition(active,out)
if __name__ == "__main__":
    unittest.main()
