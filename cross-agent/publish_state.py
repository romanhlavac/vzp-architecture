#!/usr/bin/env python3
"""Transport B: create, inspect, push exact SHA, independently fetch/read back.

No hooks, force, retry, merge or rebase. Uses existing git/gh authentication.
Private request/evidence files stay outside the repository. Run this module
from the reviewed checkout even when the target branch has older code.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile
import sys
from urllib.parse import quote

from prepublish_message import git, snapshot, canonical_message, STATE_PATH
from prompt_state import transition, verify_transition
from transport_guard import qualify


def github(repo, path):
    endpoint = f'repos/{repo}' + (f'/{path}' if path else '')
    result = subprocess.run(['gh', 'api', endpoint], capture_output=True)
    if result.returncode:
        raise ValueError(f'WRITE_BLOCKED_GITHUB_READ_EXIT_{result.returncode}')
    return json.loads(result.stdout)


def server_gates(repository, branch):
    info = github(repository, '')
    if (info.get('permissions') or {}).get('push') is not True:
        raise ValueError('WRITE_BLOCKED_PERMISSION_STOP')
    rules = github(repository, 'rules/branches/' + quote(branch, safe=''))
    required = {'deletion', 'non_fast_forward'}
    protected = set()
    for rule in rules:
        if rule.get('type') not in required:
            continue
        # Fail closed on uninspectable inherited/org rules or bypass permissions.
        detail = github(repository, f"rulesets/{int(rule['ruleset_id'])}")
        if (detail.get('enforcement') == 'active'
                and detail.get('bypass_actors') == []
                and detail.get('current_user_can_bypass') == 'never'):
            protected.add(rule['type'])
    if protected != required:
        raise ValueError('WRITE_BLOCKED_HISTORY_PROTECTION_STOP')
    return {'write_permission': True, 'history_protection_verified': True,
            'server_stale_rejection': True}


def fetch_snapshot(repo, url, branch):
    git(repo, 'fetch', '--no-tags', url, 'refs/heads/' + branch)
    head = git(repo, 'rev-parse', 'FETCH_HEAD').decode().strip()
    return snapshot(repo, head)


def create_candidate(repo, before, request):
    after = transition(before['state'], **request)
    verify_transition(before['state'], after,
                      origin_verified=request.get('origin_verified', False),
                      recovery_authorized=request.get('recovery_authorized', False))
    payload = (json.dumps(after, indent=2) + '\n').encode()
    blob = git(repo, 'hash-object', '-w', '--stdin', data=payload).decode().strip()
    with tempfile.TemporaryDirectory() as tmp:
        env = {'GIT_INDEX_FILE': str(Path(tmp) / 'index')}
        git(repo, 'read-tree', before['head'], extra_env=env)
        git(repo, 'update-index', '--cacheinfo', f'100644,{blob},{STATE_PATH}', extra_env=env)
        tree = git(repo, 'write-tree', extra_env=env).decode().strip()
    # Explicit metadata; no git commit wrapper/template/trailer/signing hooks.
    env = {'GIT_AUTHOR_NAME': 'Cross-agent', 'GIT_AUTHOR_EMAIL': 'cross-agent@users.noreply.github.com',
           'GIT_COMMITTER_NAME': 'Cross-agent', 'GIT_COMMITTER_EMAIL': 'cross-agent@users.noreply.github.com'}
    return git(repo, '-c', 'commit.gpgSign=false', 'commit-tree', tree, '-p', before['head'],
               data=canonical_message(after).encode(), extra_env=env).decode().strip()


def publish(repo, repository, branch, expected_head, expected_blob, request, evidence):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('REPOSITORY_STOP')
    git(repo, 'check-ref-format', 'refs/heads/' + branch)
    url = f'https://github.com/{repository}.git'
    before = fetch_snapshot(repo, url, branch)
    if before['head'] != expected_head or before['blob'] != expected_blob:
        raise ValueError('STALE_BASELINE_STOP')
    baseline = {'head': before['head'], 'blob': before['blob'],
                'revision': before['state']['state_revision'],
                'owner': before['state']['workstreams'][request['scope']]['owner']}
    gates = server_gates(repository, branch)
    candidate = create_candidate(repo, before, request)
    e = dict(evidence, **gates, transport='B', fresh_baseline=True,
             transition_verified=True, scope_diff_verified=True,
             non_force=True, no_retry_rebase_merge=True)
    args = dict(repo=repo, candidate=candidate, baseline=baseline, request=request)
    qualify(e, **args)
    live = git(repo, 'ls-remote', '--refs', url, 'refs/heads/' + branch).decode().split()
    if live != [expected_head, 'refs/heads/' + branch]:
        raise ValueError('STALE_REMOTE_HEAD_STOP')
    # Explicit exact refspec. Never publish moving HEAD or implicit tags/submodules.
    git(repo, '-c', 'push.followTags=false', '-c', 'push.recurseSubmodules=no',
        '-c', 'push.pushOption=', 'push', '--porcelain', url,
        candidate + ':refs/heads/' + branch)
    # Any uncertain failure propagates. No refresh/rebuild/retry.
    readback = fetch_snapshot(repo, url, branch)
    verdict = qualify(dict(e, remote_readback=True), **args,
                      phase='postpublish', readback=readback)
    state = readback['state']
    return {'commit': candidate, 'blob': readback['blob'], 'revision': state['state_revision'],
            'scope': request['scope'], 'owner': state['workstreams'][request['scope']]['owner'],
            'transport': 'B', 'readback': verdict}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('repo-dir', 'repository', 'branch', 'expected-head', 'expected-blob', 'request', 'evidence'):
        p.add_argument('--' + name, required=True)
    a = p.parse_args()
    try:
        result = publish(a.repo_dir, a.repository, a.branch, a.expected_head, a.expected_blob,
                         json.loads(Path(a.request).read_text()), json.loads(Path(a.evidence).read_text()))
        print(json.dumps(result, sort_keys=True))
    except (ValueError, RuntimeError, KeyError, OSError, TypeError) as error:
        # Never print Git stderr, private request fields or rejected messages.
        code = str(error)
        print(code if re.fullmatch(r'[A-Z0-9_]+', code) else 'PUBLICATION_STOP', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
