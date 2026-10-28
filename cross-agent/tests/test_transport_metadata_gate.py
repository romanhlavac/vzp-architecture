"""Real local Git object fixtures, never a claim of Claude runtime execution."""
import copy
import datetime
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prompt_state import transition, Stop
from prepublish_message import git, snapshot, inspect_candidate, canonical_message, STATE_PATH
from publish_state import create_candidate, publish, server_gates, github
from transport_guard import qualify


class GitHubEndpointTests(unittest.TestCase):
    def test_repository_endpoint_has_no_trailing_slash(self):
        with patch('publish_state.subprocess.run') as run:
            run.return_value.returncode = 0
            run.return_value.stdout = b'{}'
            for path, expected in (('', 'repos/example/repository'),
                                   ('rules/branches/test%2Ffixture',
                                    'repos/example/repository/rules/branches/test%2Ffixture')):
                github('example/repository', path)
                run.assert_called_with(['gh', 'api', expected], capture_output=True)


class TransportMetadataGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        git(self.repo, 'init', '-q')
        self.env = {'GIT_AUTHOR_NAME':'Cross-agent','GIT_AUTHOR_EMAIL':'cross-agent@users.noreply.github.com',
                    'GIT_COMMITTER_NAME':'Cross-agent','GIT_COMMITTER_EMAIL':'cross-agent@users.noreply.github.com'}
        state = json.loads((Path(__file__).resolve().parents[1] / 'state.json').read_text())
        state['state_revision'] = 1
        state['events'] = []
        for w in state['workstreams'].values():
            w.update(status='IDLE', owner=None, checkpoint=None, private_artifact_key=None)
            w.pop('claim_origin_key', None)
        (self.repo / 'cross-agent').mkdir()
        (self.repo / STATE_PATH).write_text(json.dumps(state))
        git(self.repo, 'add', STATE_PATH)
        tree = git(self.repo, 'write-tree').decode().strip()
        head = git(self.repo, 'commit-tree', tree, data=b'fixture\n', extra_env=self.env).decode().strip()
        self.before = snapshot(self.repo, head)
        self.baseline = dict(head=head, blob=self.before['blob'], revision=1, owner=None)
        self.request = dict(expected_revision=1, actor={'agent':'GPT','run_id':'1'*32},
                            scope='CROSS_AGENT_TEST', event='CLAIM', claim_origin_key='a'*32,
                            origin_verified=True, timestamp_utc='2026-10-26T00:00:00Z')
        self.candidate = create_candidate(self.repo, self.before, self.request)
        self.after = snapshot(self.repo, self.candidate)
        self.evidence = dict.fromkeys(('fresh_baseline transition_verified scope_diff_verified '
            'server_stale_rejection privacy_review write_permission non_force '
            'no_retry_rebase_merge history_protection_verified').split(), True)
        self.evidence['transport'] = 'B'
        self.args = dict(repo=self.repo, candidate=self.candidate, baseline=self.baseline, request=self.request)

    def commit(self, message=None, parents=None, state=None, extra_path=False):
        payload = json.dumps(state or self.after['state']).encode()
        blob = git(self.repo, 'hash-object', '-w', '--stdin', data=payload).decode().strip()
        git(self.repo, 'read-tree', self.baseline['head'])
        git(self.repo, 'update-index', '--cacheinfo', f'100644,{blob},{STATE_PATH}')
        if extra_path:
            git(self.repo, 'update-index', '--add', '--cacheinfo', f'100644,{blob},unexpected.json')
        tree = git(self.repo, 'write-tree').decode().strip()
        args = [arg for p in (parents if parents is not None else [self.baseline['head']]) for arg in ('-p', p)]
        return git(self.repo, 'commit-tree', tree, *args,
                   data=message if message is not None else canonical_message(self.after['state']).encode(),
                   extra_env=self.env).decode().strip()

    def test_actual_object_pre_and_post_are_separate(self):
        self.assertEqual(qualify(self.evidence, **self.args), 'PREPUBLICATION_PASS')
        self.assertEqual(qualify(dict(self.evidence,remote_readback=True), **self.args,
            phase='postpublish',readback=self.after),'SERVER_SIDE_STALE_WRITE_REJECTION_PASS')
        with self.assertRaisesRegex(ValueError,'PREMATURE_READBACK'):
            qualify(dict(self.evidence,remote_readback=True), **self.args)
        for rb in (None, self.before):
            with self.assertRaises(ValueError):
                qualify(dict(self.evidence,remote_readback=True), **self.args, phase='postpublish',readback=rb)

    def test_real_message_body_trailers_subject_and_mismatch(self):
        good = canonical_message(self.after['state']).encode()
        cases = [good+b'\nClaude-Session: https://example.invalid/session\n',
                 good+b'\nCo-Authored-By: Fixture <fixture@example.invalid>\n',
                 good+b'\nSigned-off-by: Fixture\n',good+b'extra\n',
                 b'https://example.invalid/session\n',good.replace(b'rev 2',b'rev 3'),
                 good.replace(b'(GPT)',b'(CLAUDE)'),good.replace(b'CROSS_AGENT_TEST',b'CES_1B')]
        for message in cases:
            with self.subTest(message=message), self.assertRaises(ValueError):
                qualify(self.evidence, **dict(self.args,candidate=self.commit(message=message)))

    def test_spoofed_flags_or_text_never_qualify(self):
        for extra in ({'candidate_commit_inspected':True},
                      {'candidate_commit_message':canonical_message(self.after['state'])}):
            with self.assertRaisesRegex(ValueError,'CALLER_COMMIT_ATTESTATION'):
                qualify(dict(self.evidence,**extra), **self.args)
        with self.assertRaisesRegex(ValueError,'COMMIT_OBJECT_REQUIRED'):
            qualify(self.evidence)

    def test_wrong_parent_merge_and_path(self):
        for sha in (self.commit(parents=[self.candidate]),
                    self.commit(parents=[self.baseline['head'],self.candidate]),
                    self.commit(extra_path=True)):
            with self.assertRaises(ValueError):
                inspect_candidate(self.repo,sha,self.baseline,self.request)

    def test_state_scope_revision_owner_and_request_mismatch(self):
        for change in ('scope','revision','owner','request'):
            state = copy.deepcopy(self.after['state']); request = copy.deepcopy(self.request)
            if change=='scope': state['workstreams']['CES_1B']['status']='IN_PROGRESS_OPEN'
            if change=='revision': state['state_revision']+=1
            if change=='owner': state['workstreams']['CROSS_AGENT_TEST']['owner']['run_id']='2'*32
            if change=='request': request['actor']['run_id']='2'*32
            with self.subTest(change=change), self.assertRaises((ValueError,Stop)):
                inspect_candidate(self.repo,self.commit(state=state),self.baseline,request)

    def test_all_required_transport_invariants(self):
        for key in self.evidence.keys()-{'transport'}:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,'WRITE_BLOCKED'):
                qualify(dict(self.evidence,**{key:False}), **self.args)

    def test_git_replace_cannot_hide_bad_message(self):
        bad=self.commit(message=b'private text\n')
        git(self.repo,'replace',bad,self.candidate)
        with self.assertRaisesRegex(ValueError,'PREPUBLICATION_METADATA'):
            inspect_candidate(self.repo,bad,self.baseline,self.request)

    def test_publisher_inspects_before_push_and_reads_back(self):
        calls=[]
        def network_git(repo,*args,**kwargs):
            calls.append(args)
            if 'ls-remote' in args:
                return (self.baseline['head']+'\trefs/heads/test/fixture\n').encode()
            if 'push' in args: return b''
            return git(repo,*args,**kwargs)
        with patch('publish_state.fetch_snapshot',side_effect=[self.before,self.after]), \
             patch('publish_state.server_gates',return_value={}), \
             patch('publish_state.create_candidate',return_value=self.candidate), \
             patch('publish_state.git',side_effect=network_git):
            result=publish(self.repo,'example/repo','test/fixture',self.before['head'],
                self.before['blob'],self.request,self.evidence)
        pushes=[c for c in calls if 'push' in c]
        self.assertEqual(len(pushes),1)
        self.assertEqual(pushes[0][-1],self.candidate+':refs/heads/test/fixture')
        self.assertNotIn('--force',pushes[0]);self.assertEqual(result['revision'],2)

    def test_publisher_rejects_tampered_object_before_any_push(self):
        bad=self.commit(message=b'private\n')
        with patch('publish_state.fetch_snapshot',return_value=self.before), \
             patch('publish_state.server_gates',return_value={}), \
             patch('publish_state.create_candidate',return_value=bad), \
             patch('publish_state.git') as network:
            with self.assertRaisesRegex(ValueError,'PREPUBLICATION_METADATA'):
                publish(self.repo,'example/repo','test/fixture',self.before['head'],
                    self.before['blob'],self.request,self.evidence)
            self.assertFalse(any('push' in c.args for c in network.call_args_list))

    def test_publisher_freezes_missing_timestamp_across_publication(self):
        real_datetime = datetime.datetime
        class Clock(real_datetime):
            current = real_datetime(2026, 10, 28, tzinfo=datetime.timezone.utc)
            @classmethod
            def now(cls, tz=None):
                return cls.current
        for timestamp in ('missing', None, '2026-10-26T00:00:00Z'):
            with self.subTest(timestamp=timestamp):
                request = dict(self.request)
                if timestamp == 'missing':
                    request.pop('timestamp_utc')
                else:
                    request['timestamp_utc'] = timestamp
                original = copy.deepcopy(request)
                published = []
                Clock.current = real_datetime(2026, 10, 28, tzinfo=datetime.timezone.utc)
                def network_git(repo, *args, **kwargs):
                    if 'ls-remote' in args:
                        return (self.before['head']+'\trefs/heads/test/fixture\n').encode()
                    if 'push' in args:
                        published.append(args[-1].split(':')[0])
                        Clock.current += datetime.timedelta(seconds=10)
                        return b''
                    return git(repo, *args, **kwargs)
                def fetch(*args):
                    return snapshot(self.repo, published[0]) if published else self.before
                with patch('publish_state.dt.datetime', Clock), \
                     patch('publish_state.fetch_snapshot', side_effect=fetch), \
                     patch('publish_state.server_gates', return_value={}), \
                     patch('publish_state.git', side_effect=network_git):
                    result = publish(self.repo, 'example/repo', 'test/fixture',
                                     self.before['head'], self.before['blob'], request, self.evidence)
                self.assertEqual(len(published), 1)
                self.assertEqual(result['readback'], 'SERVER_SIDE_STALE_WRITE_REJECTION_PASS')
                self.assertEqual(request, original)
                event = snapshot(self.repo, published[0])['state']['events'][-1]
                expected = timestamp if isinstance(timestamp, str) and timestamp != 'missing' else '2026-10-28T00:00:00Z'
                self.assertEqual(event['timestamp_utc'], expected)

    def test_wrong_baseline_blob_revision_and_owner(self):
        for delta in ({'blob':'f'*40},{'revision':99},{'owner':self.request['actor']}):
            with self.subTest(delta=delta), self.assertRaisesRegex(ValueError,'BASELINE_STOP'):
                inspect_candidate(self.repo,self.candidate,dict(self.baseline,**delta),self.request)

    def test_remote_race_and_push_failure_never_retry(self):
        for race in (True,False):
            calls=[]
            def network_git(repo,*args,**kw):
                calls.append(args)
                if 'ls-remote' in args:
                    return ((('f'*40) if race else self.before['head'])+'\trefs/heads/test/fixture\n').encode()
                if 'push' in args: raise ValueError('GIT_OPERATION_STOP_EXIT_1')
                return git(repo,*args,**kw)
            with patch('publish_state.fetch_snapshot',return_value=self.before) as fetch, \
                 patch('publish_state.server_gates',return_value={}), \
                 patch('publish_state.create_candidate',return_value=self.candidate), \
                 patch('publish_state.git',side_effect=network_git):
                with self.assertRaises(ValueError):
                    publish(self.repo,'example/repo','test/fixture',self.before['head'],
                        self.before['blob'],self.request,self.evidence)
                self.assertEqual(fetch.call_count,1)
                self.assertEqual(len([c for c in calls if 'push' in c]),0 if race else 1)

    def test_effective_rules_with_bypass_do_not_qualify(self):
        rules=[{'type':t,'ruleset_id':1} for t in ('deletion','non_fast_forward')]
        for delta in ({'bypass_actors':[{'actor_id':1}]},{'current_user_can_bypass':'always'},
                      {'enforcement':'evaluate'}):
            detail=dict(enforcement='active',bypass_actors=[],current_user_can_bypass='never')
            detail.update(delta)
            with patch('publish_state.github',side_effect=[{'permissions':{'push':True}},rules,detail,detail]):
                with self.assertRaisesRegex(ValueError,'WRITE_BLOCKED_HISTORY'):
                    server_gates('example/repo','test/fixture')

    def test_server_permissions_and_protection_fail_closed(self):
        with patch('publish_state.github',return_value={'permissions':{'push':False}}):
            with self.assertRaisesRegex(ValueError,'WRITE_BLOCKED_PERMISSION'):
                server_gates('example/repo','test/fixture')
        with patch('publish_state.github',side_effect=[{'permissions':{'push':True}},[]]):
            with self.assertRaisesRegex(ValueError,'WRITE_BLOCKED_HISTORY'):
                server_gates('example/repo','test/fixture')

if __name__=='__main__': unittest.main()
