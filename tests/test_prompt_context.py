import contextlib, io, json, pathlib, sys, unittest
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cross-agent'))
import prompt_context
class PromptContextTests(unittest.TestCase):
 def test_fresh_read_every_call(self):
  state=json.loads((ROOT/'cross-agent/state.json').read_text())
  with mock.patch.object(prompt_context,'read_remote',return_value=(state,'a'*40)) as read:
   for _ in range(2):
    out=io.StringIO()
    with contextlib.redirect_stdout(out): prompt_context.main()
    self.assertEqual(json.loads(out.getvalue())['status'],'READ_PASS')
   self.assertEqual(read.call_count,2)
 def test_fail_closed(self):
  with mock.patch.object(prompt_context,'read_remote',side_effect=RuntimeError('PRIVATE')):
   out=io.StringIO()
   with contextlib.redirect_stdout(out): prompt_context.main()
   self.assertNotIn('PRIVATE',out.getvalue())
   self.assertFalse(json.loads(out.getvalue())['write_allowed'])
