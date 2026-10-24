import contextlib
import io
import json
import pathlib
import sys
import unittest
from unittest import mock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"cross-agent"))
import prompt_context

class PromptContextTests(unittest.TestCase):
    def setUp(self):
        self.state={"schema_version":"1.0","state_revision":12,
            "storage_mode":"PILOT_NOT_CUTOVER",
            "workstreams":{x:{"owner":None,"status":"READY_FOR_HANDOFF"} for x in (
              "METHOD","SOURCE","CES_1B","CES_DATA","GS","ARCHI","CROSS_AGENT","CROSS_AGENT_TEST")},
            "continuity":{"version":1,"latest_workstream":"CROSS_AGENT_TEST",
             "streams":{"CROSS_AGENT_TEST":{"agent":"GPT","phase":"OPEN",
                "work_code":"AUTO_CONTINUITY_V2_GPT_PILOT","next_code":"CLAUDE_NATIVE_PROMPT_TEST"}}},
            "events":[]}
    def test_hook_reads_latest_without_writing(self):
        output=io.StringIO()
        with mock.patch.object(prompt_context,"read_remote",return_value=(self.state,"a"*40)) as f:
            with contextlib.redirect_stdout(output): prompt_context.main()
        o=json.loads(output.getvalue())
        self.assertEqual(o["hookSpecificOutput"]["hookEventName"],"UserPromptSubmit")
        self.assertIn("CLAUDE_NATIVE_PROMPT_TEST",o["hookSpecificOutput"]["additionalContext"])
        f.assert_called_once()
    def test_hook_fails_closed_without_secret_leak(self):
        output=io.StringIO()
        with mock.patch.object(prompt_context,"read_remote",side_effect=RuntimeError("password=SECRET")):
            with contextlib.redirect_stdout(output): prompt_context.main()
        o=json.loads(output.getvalue())
        self.assertFalse(o["continue"])
        self.assertNotIn("SECRET",output.getvalue())
if __name__=="__main__":unittest.main()
