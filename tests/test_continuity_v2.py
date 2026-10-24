import copy
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"cross-agent"))
from continuity_v2 import transition,context_for_turn,StateConflict
from state_cli import validate

KEYS=("METHOD","SOURCE","CES_1B","CES_DATA","GS","ARCHI","CROSS_AGENT","CROSS_AGENT_TEST")
class ContinuityV2Test(unittest.TestCase):
    def setUp(self):
        self.state={"schema_version":"1.0","state_revision":11,
                    "storage_mode":"PILOT_NOT_CUTOVER",
                    "workstreams":{k:{"owner":None,"status":"READY_FOR_HANDOFF"} for k in KEYS},
                    "events":[],"acceptance":{}}
    def update(self,**kwargs):
        return transition(self.state,expected_revision=11,agent="GPT",
          scope="CROSS_AGENT_TEST",phase="OPEN",
          work_code="SYNC_PILOT",next_code="CLAUDE_READ",**kwargs)
    def test_context_empty(self):
        self.assertIsNone(context_for_turn(self.state)["last"])
    def test_roundtrip(self):
        result=self.update()
        self.assertEqual(result["state_revision"],12)
        self.assertEqual(context_for_turn(result)["last"]["next_code"],"CLAUDE_READ")
        self.assertEqual(self.state["state_revision"],11)
    def test_stale_revision(self):
        with self.assertRaisesRegex(StateConflict,"STALE_BASELINE_STOP"):
            transition(self.state,expected_revision=10,agent="GPT",scope="CROSS_AGENT_TEST",
              phase="OPEN",work_code="SYNC_PILOT",next_code="CLAUDE_READ")
    def test_foreign_writer(self):
        self.state["workstreams"]["CROSS_AGENT_TEST"]["owner"]="CLAUDE"
        with self.assertRaisesRegex(StateConflict,"FOREIGN_WRITER_STOP"): self.update()
    def test_pilot_scope(self):
        with self.assertRaisesRegex(StateConflict,"PILOT_SCOPE_STOP"):
            transition(self.state,expected_revision=11,agent="GPT",scope="CES_1B",
              phase="OPEN",work_code="SYNC_PILOT",next_code="CLAUDE_READ")
    def test_no_false_verified(self):
        with self.assertRaisesRegex(StateConflict,"VERIFIED_REQUIRES_EVIDENCE_STOP"):
            transition(self.state,expected_revision=11,agent="GPT",scope="CROSS_AGENT_TEST",
              phase="VERIFIED",work_code="SYNC_PILOT",next_code="CLAUDE_READ")
    def test_no_free_text(self):
        with self.assertRaisesRegex(ValueError,"UNSAFE_CODE_STOP"):
            transition(self.state,expected_revision=11,agent="GPT",scope="CROSS_AGENT_TEST",
              phase="OPEN",work_code="private descriptive work",next_code="CLAUDE_READ")
    def test_invalid_sha(self):
        with self.assertRaisesRegex(ValueError,"INVALID_EVIDENCE_COMMIT"): self.update(evidence_commit="abc")
    def test_unknown_schema(self):
        self.state["continuity"]={"version":99,"streams":{}}
        with self.assertRaisesRegex(StateConflict,"UNKNOWN_CONTINUITY_VERSION_STOP"): self.update()
    def test_bounded_events(self):
        self.state["events"]=[{"revision":i} for i in range(20)]
        self.assertEqual(len(self.update()["events"]),20)
if __name__=="__main__":unittest.main()
