import copy
from dataclasses import replace
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cross-agent'))
from risk_policy import Operation, Ineligible, classify
from prompt_state import transition, Stop as GuardStop

spec = importlib.util.spec_from_file_location('isolated_copy', ROOT / 'automatizace/miro/isolated_board_copy.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.good = Operation(writes=True, new_private_workspace=True, fresh_bootstrap=True,
            authorized=True, permissions_verified=True, private_verified=True,
            exclusive_writer=True, receipt_available=True)

    def test_read_only_has_no_claim_or_origin(self):
        with patch('prompt_state.transition', side_effect=AssertionError('must not transition')):
            self.assertEqual(classify(Operation()), 'A')

    def test_new_private_workspace(self):
        self.assertEqual(classify(self.good), 'B')

    def test_existing_owned_exclusive_workspace(self):
        self.assertEqual(classify(replace(self.good, new_private_workspace=False,
                                         owned_isolated_workspace=True)), 'B')

    def test_shared_canonical_identity_and_promotion_require_c(self):
        for field in ('canonical_or_shared_target', 'shared_identity_change', 'promotion'):
            with self.subTest(field=field):
                self.assertEqual(classify(replace(self.good, **{field: True})), 'C')

    def test_cannot_adopt_existing_board(self):
        self.assertEqual(classify(replace(self.good, new_private_workspace=False)), 'C')

    def test_missing_each_b_gate_rejects(self):
        for field in ('fresh_bootstrap', 'authorized', 'permissions_verified',
                      'private_verified', 'exclusive_writer', 'receipt_available'):
            with self.subTest(field=field), self.assertRaises(Ineligible):
                classify(replace(self.good, **{field: False}))

    def test_bad_flag_type_rejected(self):
        with self.assertRaises(Ineligible):
            classify(replace(self.good, exclusive_writer='true'))

    def test_no_b_exception_in_shared_guard(self):
        state = json.loads((ROOT / 'cross-agent/state.json').read_text())
        with self.assertRaises(GuardStop):
            transition(state, expected_revision=state['state_revision'],
                actor={'agent':'GPT', 'run_id':'a' * 32}, scope='SOURCE', event='CLAIM')


class Response:
    def __init__(self, data, status=200):
        self.data, self.status = data, status
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return json.dumps(self.data).encode()


class Opener:
    def __init__(self, results):
        self.results, self.calls = list(results), []
    def open(self, request, **kwargs):
        self.calls.append(request)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class ApiTests(unittest.TestCase):
    def test_http_classification_no_put_retry(self):
        for code in (400, 401, 403, 404, 409, 429):
            with self.subTest(code=code):
                opener = Opener([urllib.error.HTTPError('private', code, 'sensitive', {}, None)])
                with self.assertRaisesRegex(m.Stop, f'^HTTP_{code}$'):
                    m.Client('secret', opener).request('PUT', '/v2/boards?copy_from=synthetic')
                self.assertEqual(len(opener.calls), 1)

    def test_timeout_and_5xx_put_are_ambiguous_and_never_retried(self):
        for error in (TimeoutError('private'), urllib.error.HTTPError('private', 503, 'private', {}, None)):
            opener = Opener([error])
            with self.assertRaisesRegex(m.Stop, '^AMBIGUOUS_WRITE$'):
                m.Client('secret', opener).request('PUT', '/v2/boards?copy_from=synthetic')
            self.assertEqual(len(opener.calls), 1)

    def test_get_bounded_retry(self):
        for error in (TimeoutError('private'), urllib.error.HTTPError('private', 429, 'private', {}, None)):
            opener = Opener([error, error, Response({'ok': True})])
            waits = []
            self.assertEqual(m.Client('secret', opener, waits.append).request('GET', '/v2/boards'), {'ok':True})
            self.assertEqual(len(opener.calls), 3)
            self.assertEqual(waits, [1, 2])

    def test_get_auth_and_contract_not_retried(self):
        for code in (400, 401, 403, 409):
            opener = Opener([urllib.error.HTTPError('private', code, 'private', {}, None)])
            with self.assertRaises(m.Stop):
                m.Client('secret', opener).request('GET', '/v2/boards')
            self.assertEqual(len(opener.calls), 1)

    def test_pagination_complete_and_duplicate_rejected(self):
        opener = Opener([Response({'data':[{'id':'1'}], 'cursor':'next'}), Response({'data':[{'id':'2'}], 'total':2})])
        self.assertEqual(len(m.Client('secret', opener).collection('/v2/boards')), 2)
        opener = Opener([Response({'data':[{'id':'1'}], 'cursor':'next'}), Response({'data':[{'id':'1'}]})])
        with self.assertRaisesRegex(m.Stop, 'PAGINATION_STOP'):
            m.Client('secret', opener).collection('/v2/boards')

    def test_no_arbitrary_writes_or_external_redirect(self):
        with self.assertRaises(m.Stop):
            m.Client('secret', Opener([])).request('PATCH', '/v2/boards/synthetic')
        self.assertIsNone(m.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.invalid'))

    def test_offset_pagination_and_total_drift(self):
        pages = [{'data':[{'id':'1'}], 'total':2, 'offset':0},
                 {'data':[{'id':'2'}], 'total':2, 'offset':1}]
        opener = Opener([Response(p) for p in pages])
        self.assertEqual(len(m.Client('secret', opener).collection('/v2/boards', pagination='offset')), 2)
        self.assertIn('offset=1', opener.calls[1].full_url)
        pages[1]['total'] = 3
        with self.assertRaisesRegex(m.Stop, 'PAGINATION_STOP'):
            m.Client('secret', Opener([Response(p) for p in pages])).collection('/v2/boards', pagination='offset')

    def test_unverified_space_inheritance_rejected(self):
        src = {'items':[], 'connectors':[]}
        dest = dict(src, board={'id':'new', 'name':'copy', 'policy':{'sharingPolicy':m.PRIVATE},
                    'owner':{'id':'owner'}, 'project':{'id':'shared-space'}}, members=[{'id':'owner'}])
        with self.assertRaisesRegex(m.Stop, 'PRIVACY_STOP'):
            m.validate_copy(src, dest, 'copy', 'source')

    def test_unique_name_and_bad_identity(self):
        self.assertNotEqual(m.unique_name('100'), m.unique_name('101'))
        with self.assertRaises(m.Stop):
            m.unique_name('private-board-url')

    def test_private_policy_requires_all_fields(self):
        m.privacy({'policy': {'sharingPolicy':m.PRIVATE}})
        for field in m.PRIVATE:
            bad = dict(m.PRIVATE); bad.pop(field)
            with self.assertRaisesRegex(m.Stop, 'PRIVACY_STOP'):
                m.privacy({'policy': {'sharingPolicy':bad}})
            bad[field] = 'edit'
            with self.assertRaises(m.Stop):
                m.privacy({'policy': {'sharingPolicy':bad}})

    def test_native_acceptance_not_implied(self):
        src = {'items':[{'id':'x','type':'frame'}], 'connectors':[]}
        dest = dict(src, board={'id':'new', 'name':'copy', 'policy':{'sharingPolicy':m.PRIVATE}, 'owner':{'id':'owner'}}, members=[{'id':'owner'}])
        m.validate_copy(src, dest, 'copy', 'source')
        dest['members'].append({'id':'other'})
        with self.assertRaisesRegex(m.Stop, 'PRIVACY_STOP'):
            m.validate_copy(src, dest, 'copy', 'source')

    def test_census_mismatch_rejected(self):
        src = {'items':[{'id':'x','type':'frame'}], 'connectors':[]}
        dest = {'items':[], 'connectors':[], 'board':{'id':'new', 'name':'copy', 'policy':{'sharingPolicy':m.PRIVATE}, 'owner':{'id':'owner'}}, 'members':[{'id':'owner'}]}
        with self.assertRaisesRegex(m.Stop, 'CENSUS_STOP'):
            m.validate_copy(src, dest, 'copy', 'source')

    def test_ambiguous_write_reconciles_without_second_put(self):
        client = unittest.mock.Mock()
        client.request.side_effect = m.Stop('AMBIGUOUS_WRITE')
        evidence = {}
        with patch.object(m, 'snapshot', return_value={}), patch.object(m, 'reconcile', side_effect=[[], [{'id':'new'}]]), self.assertRaises(m.Stop):
            m.apply_copy(client, 'source', {}, 'copy', evidence)
        self.assertEqual(client.request.call_count, 1)
        self.assertEqual(evidence['reconciliation_candidates'], [{'id':'new'}])

    def test_existing_identity_stops_without_write(self):
        client = unittest.mock.Mock()
        with patch.object(m, 'reconcile', return_value=[{'id':'existing'}]), self.assertRaisesRegex(m.Stop, 'RECONCILE_REQUIRED'):
            m.apply_copy(client, 'source', {}, 'copy', {})
        client.request.assert_not_called()

    def test_source_drift_stops_before_write(self):
        client = unittest.mock.Mock()
        with patch.object(m, 'reconcile', return_value=[]), patch.object(m, 'snapshot', return_value={'changed':True}), self.assertRaisesRegex(m.Stop, 'SOURCE_CHANGED_STOP'):
            m.apply_copy(client, 'source', {}, 'copy', {})
        client.request.assert_not_called()

    def test_audit_no_mutation_and_no_private_output(self):
        env = {'COPY_PHASE':'audit', 'GITHUB_REPOSITORY':'romanhlavac/vzp-architecture',
               'GITHUB_REF':'refs/heads/main','MIRO_DIAGNOSTIC_BOARD_ID':'synthetic-source',
               'MIRO_DIAGNOSTIC_TOKEN':'synthetic-secret'}
        client = unittest.mock.Mock(); client.request.return_value={'scopes':['boards:read','boards:write'], 'team':{'id':'synthetic-team'}}
        with patch.dict(m.os.environ, env), patch.object(m, 'Client', return_value=client), patch.object(m, 'snapshot', return_value={'board':{'team':{'id':'synthetic-team'}}}), patch.object(m, 'check_git'), patch('sys.stdout', new_callable=io.StringIO) as out:
            m.main()
        self.assertTrue(all(c.args[0]=='GET' for c in client.request.call_args_list))
        self.assertNotIn('synthetic', out.getvalue())

    def test_public_ci_only_audit_and_no_artifacts(self):
        text=(ROOT/'.github/workflows/miro-isolated-copy.yml').read_text()
        self.assertNotIn('push:', text)
        self.assertIn('options: [audit]', text)
        self.assertNotIn('upload-artifact', text)
        self.assertNotIn('MIRO_RECEIPT_CERT_PEM', text)

    def test_work_copy_requires_activation_and_rejects_ci(self):
        with patch.dict(m.os.environ, {'GITHUB_ACTIONS':'true'}), self.assertRaises(m.Stop):
            m.work_copy(None, 'source', {}, 'copy', None, 'folder', 'a'*32, {'status':'ACTIVE'})
        with patch.dict(m.os.environ, {}, clear=True), self.assertRaisesRegex(m.Stop, 'INACTIVE_STOP'):
            m.work_copy(None, 'source', {}, 'copy', None, 'folder', 'a'*32, {'status':'INACTIVE'})

    def test_unverified_private_intent_stops_before_mutation(self):
        store=unittest.mock.Mock()
        store.read.return_value={'content':{},'parent':'folder','private':False,'unique':True}
        with patch.dict(m.os.environ, {}, clear=True), patch.object(m,'reconcile',return_value=[]), patch.object(m,'apply_copy') as mutation, self.assertRaisesRegex(m.Stop,'EVIDENCE_STOP'):
            m.work_copy(None,'source',{},'copy',store,'folder','a'*32,{'status':'ACTIVE'})
        mutation.assert_not_called()

    def test_private_intent_then_mutation_then_outcome(self):
        saved={}; order=[]
        class Store:
            def put_immutable(self, folder, name, value):
                order.append(name.split('_')[1]); saved[name]=copy.deepcopy(value); return name
            def read(self, key):
                return {'content':saved[key],'parent':'folder','private':True,'unique':True}
        def mutate(*args): order.append('MUTATION')
        with patch.dict(m.os.environ, {}, clear=True), patch.object(m,'reconcile',return_value=[]), patch.object(m,'apply_copy',side_effect=mutate):
            m.work_copy(None,'source',{},'copy',Store(),'folder','a'*32,{'status':'ACTIVE'})
        self.assertEqual(order,['INTENT','MUTATION','OUTCOME'])


if __name__ == '__main__':
    unittest.main()
