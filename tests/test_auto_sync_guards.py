import contextlib
import copy
import io
import json
import pathlib
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cross-agent'))
import auto_sync
from state_cli import StateConflict, perform_transition


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.state = json.loads((ROOT / 'tests/fixtures/legacy_state.json').read_text())
        self.state['workstreams']['CROSS_AGENT_TEST'] = {'owner': 'CLAUDE', 'status': 'IN_PROGRESS'}

    def test_missing_revision_does_not_clone(self):
        with mock.patch('auto_sync._call') as call:
            with self.assertRaisesRegex(StateConflict, 'EXPECTED_REVISION_REQUIRED'):
                auto_sync.publish('stop', 'CROSS_AGENT_TEST')
            call.assert_not_called()

    def test_stale_revision_cannot_commit_or_push(self):
        calls = []
        def clone_only(*args, **kwargs):
            calls.append(args)
            self.assertEqual(args[1], 'clone')
            root = pathlib.Path(args[-1])
            (root / 'cross-agent').mkdir(parents=True)
            (root / auto_sync.STATE_PATH).write_text(json.dumps(self.state))
        with mock.patch('auto_sync._call', side_effect=clone_only):
            with self.assertRaisesRegex(StateConflict, 'STALE_BASELINE_STOP'):
                auto_sync.publish('stop', 'CROSS_AGENT_TEST', expected_revision=self.state['state_revision'] - 1)
        self.assertEqual(len(calls), 1)

    def test_open_preserves_owner_and_never_marks_ready(self):
        before = copy.deepcopy(self.state)
        event = auto_sync.choose_event('stop', before, 'CROSS_AGENT_TEST', False)
        result = perform_transition(before, event, 'CLAUDE', 'CROSS_AGENT_TEST', before['state_revision'])
        self.assertEqual(result['workstreams']['CROSS_AGENT_TEST'], {'owner': 'CLAUDE', 'status': 'IN_PROGRESS_OPEN'})
        self.assertEqual(self.state, before)

    def test_sessionstart_uses_model_context_field(self):
        out = io.StringIO()
        with mock.patch('auto_sync.read_remote', return_value=(self.state, 'test-blob')), contextlib.redirect_stdout(out):
            self.assertEqual(auto_sync.context(), 0)
        result = json.loads(out.getvalue())['hookSpecificOutput']
        self.assertEqual(result['hookEventName'], 'SessionStart')
        self.assertIn('rev=', result['additionalContext'])

    def test_bootstrap_error_stops_session_without_details(self):
        out = io.StringIO()
        with mock.patch('auto_sync.read_remote', side_effect=RuntimeError('DO_NOT_EXPOSE')), contextlib.redirect_stdout(out):
            auto_sync.context()
        result = json.loads(out.getvalue())
        self.assertFalse(result['continue'])
        self.assertNotIn('DO_NOT_EXPOSE', out.getvalue())

    def test_unknown_mode_cannot_write_business_scope(self):
        self.state['storage_mode'] = 'UNKNOWN'
        with self.assertRaisesRegex(StateConflict, 'PILOT_SCOPE_STOP'):
            auto_sync.choose_event('finish', self.state, 'METHOD', True)

    def test_finish_foreign_writer_stops(self):
        self.state['workstreams']['CROSS_AGENT_TEST']['owner'] = 'GPT'
        with self.assertRaisesRegex(StateConflict, 'WRITER_CONFLICT_STOP'):
            auto_sync.choose_event('finish', self.state, 'CROSS_AGENT_TEST', True)

    def test_hooks_are_disabled(self):
        config = json.loads((ROOT / '.claude/settings.json').read_text())
        self.assertFalse(config.get('hooks'))

    def test_git_errors_do_not_escape_to_stderr(self):
        with mock.patch('auto_sync.subprocess.run') as run:
            auto_sync._call('git', 'push')
        self.assertEqual(run.call_args.kwargs['stderr'], auto_sync.subprocess.PIPE)

if __name__ == '__main__':
    unittest.main()
