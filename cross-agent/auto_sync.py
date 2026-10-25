#!/usr/bin/env python3
"""Safe GPT/Claude Code public-metadata state bridge.

SessionStart: authenticated or public GitHub read, inject fresh state metadata.
Stop: opt-in scoped CHECKPOINT_OPEN. Never claim READY for unverified work.
Finish: explicit native acceptance required, then CHECKPOINT_PASS.

This is not chat/transcript sync, a general lock service, or a way to bypass
client data classifications. Git pushes are fast-forward, never force/rebase.
"""
from __future__ import annotations
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request

from state_cli import validate, perform_transition, StateConflict

REPO = 'romanhlavac/vzp-architecture'
STATE_PATH = 'cross-agent/state.json'
REMOTE = f'https://github.com/{REPO}.git'
KNOWN_WORKSTREAMS = frozenset(('METHOD', 'SOURCE', 'CES_1B', 'CES_DATA', 'GS', 'ARCHI', 'CROSS_AGENT', 'CROSS_AGENT_TEST'))


def read_remote():
    req = urllib.request.Request(
        f'https://api.github.com/repos/{REPO}/contents/{STATE_PATH}?ref=main',
        headers={'Accept': 'application/vnd.github+json',
                 'Cache-Control': 'no-cache', 'User-Agent': 'vzp-agent-continuity/1.0'},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        result = json.load(response)
    data = validate(json.loads(base64.b64decode(result['content'])))
    return data, result['sha']


def select_stop_event(state, scope, agent='CLAUDE'):
    """Pure guard. A STOP hook never records a successful native acceptance."""
    if not scope:
        return None
    if scope not in KNOWN_WORKSTREAMS:
        raise ValueError('INVALID_WORKSTREAM')
    if state['storage_mode'] != 'ACTIVE_GPT_CLAUDE' and scope != 'CROSS_AGENT_TEST':
        return None
    current = state['workstreams'][scope]
    if current['owner'] not in (None, agent):
        raise StateConflict('WRITER_CONFLICT_STOP')
    if current['owner'] is None:
        return None
    if current['status'] != 'IN_PROGRESS':
        return None
    return 'CHECKPOINT_OPEN'


def choose_event(action, state, scope, evidence):
    if scope not in KNOWN_WORKSTREAMS:
        raise ValueError('INVALID_WORKSTREAM')
    if state['storage_mode'] != 'ACTIVE_GPT_CLAUDE' and scope != 'CROSS_AGENT_TEST':
        raise StateConflict('PILOT_SCOPE_STOP')
    if action == 'stop':
        return select_stop_event(state, scope)
    if action == 'finish':
        if not evidence:
            raise StateConflict('NATIVE_READBACK_EVIDENCE_REQUIRED')
        if state['workstreams'][scope]['owner'] != 'CLAUDE':
            raise StateConflict('WRITER_CONFLICT_STOP')
        return 'CHECKPOINT_PASS'
    raise ValueError('INVALID_ACTION')


def _call(*cmd, timeout=70, capture=False):
    if capture:
        return subprocess.check_output(cmd, text=True, timeout=timeout, stderr=subprocess.PIPE).strip()
    subprocess.run(cmd, check=True, timeout=timeout, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def publish(action, scope, evidence=False, expected_revision=None):
    """Isolated checkout, single FF commit, fresh remote clone readback.

    An interrupted push is never blindly retried; caller reconciles first.
    Failure never silently steals a foreign scope or rewrites another file.
    """
    if expected_revision is None:
        raise StateConflict('EXPECTED_REVISION_REQUIRED')
    with tempfile.TemporaryDirectory(prefix='vzp-gh-sync-') as temp:
        root = Path(temp) / 'write'
        _call('git', 'clone', '--quiet', '--depth', '1', '--branch', 'main', REMOTE, str(root))
        path = root / STATE_PATH
        state = validate(json.loads(path.read_text(encoding='utf-8')))
        if state['state_revision'] != expected_revision:
            raise StateConflict('STALE_BASELINE_STOP')
        event = choose_event(action, state, scope, evidence)
        if event is None:
            return {'status': 'NO_WRITE', 'revision': state['state_revision']}
        new = perform_transition(state, event, 'CLAUDE', scope, expected_revision)
        path.write_text(json.dumps(new, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        _call('git', '-C', str(root), 'add', '--', STATE_PATH)
        _call('git', '-C', str(root), '-c', 'user.name=VZP-Claude-Agent',
              '-c', 'user.email=vzp-agent@users.noreply.github.com',
              'commit', '--quiet', '-m', f'cross-agent: {event} {scope} rev {new["state_revision"]}')
        local_sha = _call('git', '-C', str(root), 'rev-parse', 'HEAD', capture=True)
        # Never force-push, rebase or auto-retry a non-fast-forward conflict.
        _call('git', '-C', str(root), 'push', '--quiet', 'origin', 'HEAD:refs/heads/main')
        readback = Path(temp) / 'readback'
        _call('git', 'clone', '--quiet', '--depth', '1', '--branch', 'main', REMOTE, str(readback))
        remote_sha = _call('git', '-C', str(readback), 'rev-parse', 'HEAD', capture=True)
        actual = validate(json.loads((readback / STATE_PATH).read_text(encoding='utf-8')))
        if remote_sha != local_sha or actual != new:
            raise StateConflict('READBACK_MISMATCH_STOP')
        return {'status': 'COMMITTED_READBACK_PASS', 'revision': actual['state_revision'],
                'commit': remote_sha, 'event': event}


def context():
    try:
        state, blob = read_remote()
        message = (f'VZP GH fresh read: rev={state["state_revision"]}, blob={blob}, '
                   f'mode={state["storage_mode"]}; '
                   f'test={state["workstreams"]["CROSS_AGENT_TEST"]["status"]}; '
                   'private Google Drive project instructions, full manifest/kernel/index, '
                   'current canonical GD operational state and target native artifact '
                   'MUST all be fresh-read independently before substantive work. '
                   'Never publish confidential data to public GitHub. '
                   'GitHub remains pilot until authorized cutover.')
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': message}}))
        return 0
    except Exception as exc:
        print(json.dumps({'continue': False, 'stopReason':
                         f'BOOTSTRAP INCOMPLETE (GitHub {type(exc).__name__}). '
                         'No shared writes; reconcile access first.'}))
        return 0


def main(argv=None):
    print("SUPERSEDED_NO_HOOKS_NO_WRITE")
    return 0

def legacy_main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=('context', 'stop', 'finish'))
    ap.add_argument('--workstream', default=os.getenv('VZP_WORKSTREAM', ''))
    ap.add_argument('--expected-revision', type=int, default=None)
    args = ap.parse_args(argv)
    if args.action == 'context':
        return context()
    if os.getenv('VZP_AUTO_SYNC_ENABLED') != '1':
        print(json.dumps({'status': 'DISABLED_NO_WRITE'}))
        return 0
    if not args.workstream:
        print(json.dumps({'status': 'UNSCOPED_NO_WRITE'}))
        return 0
    try:
        expected = args.expected_revision
        if expected is None and os.getenv('VZP_EXPECTED_STATE_REVISION'):
            expected = int(os.environ['VZP_EXPECTED_STATE_REVISION'])
        result = publish(args.action, args.workstream,
                         evidence=os.getenv('VZP_NATIVE_READBACK_PASS') == '1',
                         expected_revision=expected)
        print(json.dumps(result))
        return 0
    except (StateConflict, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        # Avoid leaking subprocess stderr, auth headers, credentials, or private content.
        reason = str(exc) if isinstance(exc, StateConflict) else type(exc).__name__
        print(f'STOP_RECONCILE: {reason}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
