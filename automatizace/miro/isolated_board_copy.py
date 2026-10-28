#!/usr/bin/env python3
"""Fail-closed isolated copy. No locators, payloads or exception text in stdout.

Public CI is read-only. Work persists and verifies private Drive intent/outcome.
Only one PUT per run, no mutation retry, no deletion, sharing or promotion API.
Eligibility is checked per operation; private evidence never enters public CI.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://api.miro.com'
ACTIVATION = Path(__file__).with_name('isolated_copy_activation.json')
PRIVATE = {'access': 'private', 'teamAccess': 'private',
           'organizationAccess': 'private', 'inviteToAccountAndBoardLinkAccess': 'no_access'}
SAFE_CODES = {'HTTP_400', 'HTTP_401', 'HTTP_403', 'HTTP_404', 'HTTP_409', 'HTTP_429',
              'HTTP_5XX', 'HTTP_OTHER', 'AMBIGUOUS_WRITE', 'GET_UNAVAILABLE',
              'EVIDENCE_STOP', 'CONFIG_STOP', 'PRIVACY_STOP',
              'IDENTITY_STOP', 'SOURCE_CHANGED_STOP', 'CENSUS_STOP',
              'PAGINATION_STOP', 'RECONCILE_REQUIRED', 'TOKEN_SCOPE_STOP',
              'INVENTORY_STOP', 'INTERNAL_STOP'}


class Stop(RuntimeError):
    def __init__(self, code):
        self.code = code if code in SAFE_CODES else 'INTERNAL_STOP'
        super().__init__(self.code)


def require(ok, code):
    if not ok:
        raise Stop(code)


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, token, opener=None, sleeper=time.sleep):
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        self.token = token
        self.sleep = sleeper

    def request(self, method, path, data=None):
        require(method in {'GET', 'PUT'} and path.startswith('/'), 'CONFIG_STOP')
        require(method != 'PUT' or path.startswith('/v2/boards?copy_from='), 'CONFIG_STOP')
        req = urllib.request.Request(BASE + path, method=method,
            data=None if data is None else encoded(data), headers={
                'Authorization': 'Bearer ' + self.token, 'Accept': 'application/json',
                'Content-Type': 'application/json'})
        for attempt in range(3 if method == 'GET' else 1):
            try:
                with self.opener.open(req, timeout=40) as response:
                    status = response.status
                    body = json.loads(response.read())
                require(status == (200 if method == 'GET' else 201),
                        'GET_UNAVAILABLE' if method == 'GET' else 'AMBIGUOUS_WRITE')
                return body
            except urllib.error.HTTPError as exc:
                code = 'HTTP_' + str(exc.code)
                if 500 <= exc.code <= 599:
                    code = 'HTTP_5XX'
                if method == 'PUT' and (exc.code >= 500 or exc.code in (408, 504)):
                    raise Stop('AMBIGUOUS_WRITE') from None
                if method == 'GET' and (exc.code == 429 or exc.code >= 500) and attempt < 2:
                    self.sleep(2 ** attempt)
                    continue
                raise Stop(code if code in SAFE_CODES else 'HTTP_OTHER') from None
            except Stop:
                raise
            except Exception:
                if method == 'GET' and attempt < 2:
                    self.sleep(2 ** attempt)
                    continue
                raise Stop('GET_UNAVAILABLE' if method == 'GET' else 'AMBIGUOUS_WRITE') from None

    def collection(self, path, params=None, pagination='cursor'):
        require(pagination in {'cursor', 'offset'}, 'CONFIG_STOP')
        params = dict(params or {})
        params['limit'] = 50
        if pagination == 'offset':
            params['offset'] = 0
        result, cursors, ids = [], set(), set()
        expected_total = None
        for _ in range(1000):
            page = self.request('GET', path + '?' + urllib.parse.urlencode(params))
            require(isinstance(page, dict) and isinstance(page.get('data'), list), 'PAGINATION_STOP')
            for item in page['data']:
                require(isinstance(item, dict) and item.get('id') and item['id'] not in ids,
                        'PAGINATION_STOP')
                ids.add(item['id'])
                result.append(item)
            if pagination == 'offset':
                total = page.get('total')
                require(type(total) is int and total >= len(result) and
                        page.get('offset') == params['offset'] and not page.get('cursor'),
                        'PAGINATION_STOP')
                if expected_total is None:
                    expected_total = total
                require(total == expected_total, 'PAGINATION_STOP')
                if len(result) == total:
                    return result
                require(bool(page['data']), 'PAGINATION_STOP')
                params['offset'] += len(page['data'])
                continue
            cursor = page.get('cursor')
            if not cursor:
                require(not (page.get('links') or {}).get('next'), 'PAGINATION_STOP')
                if type(page.get('total')) is int:
                    require(len(result) == page['total'], 'PAGINATION_STOP')
                return result
            require(isinstance(cursor, str) and cursor not in cursors, 'PAGINATION_STOP')
            cursors.add(cursor)
            params['cursor'] = cursor
        raise Stop('PAGINATION_STOP')


def board_path(board_id):
    return '/v2/boards/' + urllib.parse.quote(board_id, safe='')


def privacy(board):
    policy = (board.get('policy') or {}).get('sharingPolicy') or {}
    require(all(policy.get(k) == v for k, v in PRIVATE.items()), 'PRIVACY_STOP')


def snapshot(client, board_id):
    path = board_path(board_id)
    board = client.request('GET', path)
    require(str(board.get('id')) == board_id, 'IDENTITY_STOP')
    items = client.collection(path + '/items')
    connectors = client.collection(path + '/connectors')
    members = client.collection(path + '/members', pagination='offset')
    tail = client.request('GET', path)
    require(board == tail, 'SOURCE_CHANGED_STOP')
    return {'board': board, 'items': sorted(items, key=lambda x: x['id']),
            'connectors': sorted(connectors, key=lambda x: x['id']),
            'members': sorted(members, key=lambda x: x['id'])}


def census(snap):
    return {'types': dict(collections.Counter(x.get('type') for x in snap['items'])),
            'connectors': len(snap['connectors'])}


def unique_name(run_id):
    require(re.fullmatch(r'[0-9]{1,24}', run_id) is not None, 'CONFIG_STOP')
    return 'Private isolated workspace - ' + run_id


def validate_copy(source, copied, name, source_id):
    board = copied['board']
    require(str(board.get('id')) != source_id and board.get('name') == name, 'IDENTITY_STOP')
    privacy(board)
    # Space/project inheritance cannot be proven private by sharingPolicy alone.
    require(not any(board.get(k) for k in ('project', 'projectId', 'project_id',
                                          'space', 'spaceId', 'space_id')), 'PRIVACY_STOP')
    owner = (board.get('owner') or {}).get('id')
    require(owner and len(copied['members']) == 1 and
            copied['members'][0].get('id') == owner, 'PRIVACY_STOP')
    require(census(source) == census(copied), 'CENSUS_STOP')
    # Census is not semantic equivalence. Deep links, unsupported types, comments,
    # docs, metadata and native rendering require a separate private G1-G4 audit.


def reconcile(client, name):
    boards = client.collection('/v2/boards', {'query': name}, pagination='offset')
    return [b for b in boards if b.get('name') == name]


def apply_copy(client, source_id, before, name, evidence):
    # An existing identity is never adopted as a new exclusive workspace.
    require(not reconcile(client, name), 'RECONCILE_REQUIRED')
    require(snapshot(client, source_id) == before, 'SOURCE_CHANGED_STOP')
    evidence['phase'] = 'WRITE_INTENT'
    try:
        result = client.request('PUT', '/v2/boards?' + urllib.parse.urlencode({'copy_from': source_id}),
            {'name': name, 'policy': {'sharingPolicy': PRIVATE}})
        require(result.get('id') and str(result['id']) != source_id, 'AMBIGUOUS_WRITE')
        evidence['new_board_id'] = str(result['id'])
        after = snapshot(client, source_id)
        copied = snapshot(client, str(result['id']))
        evidence.update(source_after=after, copy=copied)
        require(before == after, 'SOURCE_CHANGED_STOP')
        validate_copy(before, copied, name, source_id)
        evidence.update(phase='COPY_VERIFIED_API_ONLY', native_acceptance='G1_G4_OPEN')
        return evidence
    except Stop as exc:
        evidence.update(phase='STOP_RECONCILE', stop_code=exc.code)
        if exc.code == 'AMBIGUOUS_WRITE':
            # Read-only resolution; never duplicate the PUT, even if no match is
            # visible yet. Provider search may be eventually consistent.
            try:
                evidence['reconciliation_candidates'] = reconcile(client, name)
            except Stop:
                evidence['reconciliation_status'] = 'OPEN'
        raise


def main():
    os.umask(0o077)
    phase = os.environ.get('COPY_PHASE', 'audit')
    require(phase == 'audit', 'CONFIG_STOP')
    require(os.environ.get('GITHUB_REPOSITORY') == 'romanhlavac/vzp-architecture' and
            os.environ.get('GITHUB_REF') == 'refs/heads/main', 'CONFIG_STOP')
    source_id = os.environ.get('MIRO_DIAGNOSTIC_BOARD_ID', '').strip()
    token = os.environ.get('MIRO_DIAGNOSTIC_TOKEN', '').strip()
    require(source_id and token, 'CONFIG_STOP')
    client = Client(token)
    auth = client.request('GET', '/v1/oauth-token')
    scopes = auth.get('scopes', auth.get('scope', []))
    if isinstance(scopes, str):
        scopes = scopes.replace(',', ' ').split()
    require(isinstance(scopes, list) and {'boards:read', 'boards:write'} <= set(scopes), 'TOKEN_SCOPE_STOP')
    print('SOURCE_INVENTORY_START', flush=True)
    before = snapshot(client, source_id)
    auth_team = auth.get('team') or {}
    board_team = before['board'].get('team') or {}
    require(auth_team.get('id') and auth_team.get('id') == board_team.get('id'), 'IDENTITY_STOP')
    print('SOURCE_INDEPENDENT_VERIFICATION_START', flush=True)
    require(before == snapshot(client, source_id), 'SOURCE_CHANGED_STOP')
    print('AUDIT_READ_ONLY_PASS; API_INVENTORY_ONLY; NATIVE_G1_G4_OPEN; NO_CI_MUTATION')


def work_copy(client, source_id, before, name, store, folder, operation_key, activation, *, operation):
    """Work-only orchestration; store is an authorized private Drive adapter.

    put_immutable returns an ID; read returns content, parent, private and unique.
    Those properties must come from native service read-back, not local flags.
    No adapter credentials, file IDs or receipt bodies are printed or returned to CI.
    """
    require(not os.environ.get('GITHUB_ACTIONS'), 'CONFIG_STOP')
    # Qualification belongs to this operation, not another agent's Git transport.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cross-agent'))
    from risk_policy import classify
    require(activation == {'schema_version': 2, 'status': 'PER_OPERATION',
            'policy_version': '2.3.1', 'evidence_transport': 'PRIVATE_DRIVE'}, 'CONFIG_STOP')
    require(classify(operation) == 'B', 'CONFIG_STOP')
    require(re.fullmatch('[0-9a-f]{32}', operation_key) is not None, 'IDENTITY_STOP')
    def persist(kind, value):
        receipt_name = 'VZP_' + kind + '_' + operation_key + '.json'
        file_id = store.put_immutable(folder, receipt_name, value)
        back = store.read(file_id)
        require(back['content'] == value and back['parent'] == folder and
                back['private'] is True and back['unique'] is True, 'EVIDENCE_STOP')
        return file_id
    evidence = {'operation_key': operation_key, 'name': name,
                'source_board_id': source_id, 'source_before': before,
                'phase': 'INTENT_NO_WRITE', 'native_acceptance': 'G1_G4_OPEN'}
    require(not reconcile(client, name), 'RECONCILE_REQUIRED')
    persist('INTENT', evidence)
    # A native evidence adapter must snapshot values, never retain mutable references.
    try:
        apply_copy(client, source_id, before, name, evidence)
    finally:
        persist('OUTCOME', evidence)
    return evidence


if __name__ == '__main__':
    try:
        main()
    except Stop as exc:
        print(exc.code, flush=True)
        raise SystemExit(1)
    except Exception:
        print('INTERNAL_STOP', flush=True)
        raise SystemExit(1)
