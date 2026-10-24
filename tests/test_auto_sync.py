import copy
import json
import pathlib
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cross-agent'))
try:
    from auto_sync import choose_event, select_stop_event, main
except ImportError as err:
    raise RuntimeError('Copy this overlay into repository root, alongside cross-agent/state_cli.py') from err


class AutoSyncTests(unittest.TestCase):
    def setUp(self):
        self.state = {
            'storage_mode': 'PILOT_NOT_CUTOVER',
            'workstreams': {
                'CROSS_AGENT_TEST': {'owner': None, 'status': 'READY_FOR_HANDOFF'},
                'CES_1B': {'owner': None, 'status': 'WORKING_DEMO_VISUAL_OPEN'},
            },
        }

    def test_without_scope_no_write(self):
        self.assertIsNone(select_stop_event(self.state, ''))

    def test_pilot_cannot_auto_publish_business(self):
        self.state['workstreams']['CES_1B'] = {'owner': 'CLAUDE', 'status': 'IN_PROGRESS'}
        self.assertIsNone(select_stop_event(self.state, 'CES_1B'))

    def test_stop_checkpoints_only_owned_active_scope(self):
        self.state['workstreams']['CROSS_AGENT_TEST'] = {'owner': 'CLAUDE', 'status': 'IN_PROGRESS'}
        self.assertEqual(choose_event('stop', self.state, 'CROSS_AGENT_TEST', False), 'CHECKPOINT_OPEN')
        self.state['workstreams']['CROSS_AGENT_TEST']['status'] = 'IN_PROGRESS_OPEN'
        self.assertIsNone(choose_event('stop', self.state, 'CROSS_AGENT_TEST', False))

    def test_foreign_owner_no_change(self):
        self.state['workstreams']['CROSS_AGENT_TEST'] = {'owner': 'GPT', 'status': 'IN_PROGRESS'}
        from state_cli import StateConflict
        with self.assertRaisesRegex(StateConflict, 'WRITER_CONFLICT_STOP'):
            select_stop_event(self.state, 'CROSS_AGENT_TEST')

    def test_no_finish_without_native_readback(self):
        from state_cli import StateConflict
        self.state['workstreams']['CROSS_AGENT_TEST'] = {'owner': 'CLAUDE', 'status': 'IN_PROGRESS_OPEN'}
        with self.assertRaisesRegex(StateConflict, 'NATIVE_READBACK_EVIDENCE_REQUIRED'):
            choose_event('finish', self.state, 'CROSS_AGENT_TEST', False)
        self.assertEqual(choose_event('finish', self.state, 'CROSS_AGENT_TEST', True), 'CHECKPOINT_PASS')

    def test_pilot_blocks_finish_business(self):
        from state_cli import StateConflict
        self.state['workstreams']['CES_1B'] = {'owner': 'CLAUDE', 'status': 'IN_PROGRESS'}
        with self.assertRaisesRegex(StateConflict, 'PILOT_SCOPE_STOP'):
            choose_event('finish', self.state, 'CES_1B', True)

    def test_disabled_has_zero_mutations(self):
        with mock.patch.dict('os.environ', {'VZP_AUTO_SYNC_ENABLED': '0'}):
            with mock.patch('auto_sync.publish', side_effect=AssertionError('Must not publish')):
                self.assertEqual(main(['stop', '--workstream', 'CROSS_AGENT_TEST']), 0)


if __name__ == '__main__':
    unittest.main()
