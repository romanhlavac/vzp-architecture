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
    def test_missing_recovery_evidence(self):
        good=dict(expected_revision=base["state_revision"], actor=gpt, scope="CES_1B",
                  event="ORPHAN_RECONCILE", work_code="RECOVERY",
                  authorization_key="b"*32, private_artifact_key="c"*32,
                  native_readback=True, recovery_authorized=True)
        for delta in ({"native_readback":False}, {"authorization_key":None},
                      {"private_artifact_key":None}, {"recovery_authorized":False},
                      {"work_code":"IMPLEMENTATION"},
                      {"expected_revision":base["state_revision"]-1}):
            with self.subTest(delta=delta), self.assertRaises(Stop):
                transition(base, **dict(good, **delta))
    def test_foreign_handoff_rejected(self):
        with self.assertRaisesRegex(Stop,"FOREIGN_WRITER_STOP"):
            transition(base, expected_revision=base["state_revision"], actor=gpt,
                       scope="CES_1B", event="HANDOFF_OPEN", native_readback=True)
    def test_recovery_requires_existing_owner(self):
        altered=copy.deepcopy(base)
        altered["workstreams"]["CES_1B"]["owner"]=None
        altered["workstreams"]["CES_1B"]["status"]="IN_PROGRESS_OPEN"
        with self.assertRaises(Stop):
            transition(altered, expected_revision=altered["state_revision"],actor=gpt,
                       scope="CES_1B",event="ORPHAN_RECONCILE",work_code="RECOVERY",
                       authorization_key="b"*32,private_artifact_key="c"*32,
                       native_readback=True,recovery_authorized=True)
    def test_orphan_integrity_and_no_silent_replay(self):
        result=transition(base, expected_revision=base["state_revision"],actor=gpt,
                          scope="CES_1B",event="ORPHAN_RECONCILE",work_code="RECOVERY",
                          authorization_key="b"*32,private_artifact_key="c"*32,
                          native_readback=True,recovery_authorized=True)
        with self.assertRaises(Stop):
            verify_transition(base,result,recovery_authorized=False)
        altered=copy.deepcopy(result)
        altered["workstreams"]["GS"]["status"]="IDLE"
        with self.assertRaises(Stop):
            verify_transition(base,altered,recovery_authorized=True)
    def test_finalization_requires_evidence_and_owner(self):
        active=transition(base,expected_revision=base["state_revision"],
                          actor=gpt,scope="METHOD",event="CLAIM")
        for kwargs in ({"private_artifact_key":None,"native_readback":True},
                       {"private_artifact_key":"c"*32,"native_readback":False}):
            with self.assertRaises(Stop):
                finalize_phase(active,expected_revision=active["state_revision"],
                               actor=gpt,scope="METHOD",**kwargs)
        with self.assertRaises(Stop):
            finalize_phase(active,expected_revision=active["state_revision"],
                           actor={"agent":"GPT","run_id":"d"*32},scope="METHOD",
                           private_artifact_key="c"*32,native_readback=True)
    def test_completed_checkpoint_needs_commit(self):
        active=transition(base,expected_revision=base["state_revision"],
                          actor=gpt,scope="METHOD",event="CLAIM")
        kwargs=dict(expected_revision=active["state_revision"],actor=gpt,
                    scope="METHOD",completed=True,
                    private_artifact_key="c"*32,native_readback=True)
        with self.assertRaises(Stop):
            finalize_phase(active,**kwargs)
        result=finalize_phase(active,evidence_commit="e"*40,**kwargs)
        self.assertEqual(result["workstreams"]["METHOD"]["status"],"READY_FOR_HANDOFF")
        self.assertIsNone(result["workstreams"]["METHOD"]["owner"])
        verify_transition(active,result)
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
