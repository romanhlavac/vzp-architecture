"""Validate generated Git commit messages before publication; no hooks."""
import re

_PATTERN = re.compile(
    r"cross-agent: (CLAIM|CHECKPOINT_OPEN|CHECKPOINT_PASS|HANDOFF_OPEN|RECOVERY_OPEN|RECONCILE|OWNER_AUTHORIZED_RELEASE) "
    r"(METHOD|SOURCE|CES_1B|CES_DATA|GS|ARCHI|CROSS_AGENT|CROSS_AGENT_TEST) "
    r"rev ([1-9][0-9]*) \((GPT|CLAUDE|CURSOR)\)"
)

def validate_message(message: str):
    """Accept only one canonical subject; refuse trailers, URLs and extra text."""
    value = message.removesuffix("\n")
    if not message.endswith("\n") or not _PATTERN.fullmatch(value):
        raise ValueError("PREPUBLICATION_METADATA_STOP")
    return value

import json
import os
import subprocess
from prompt_state import transition, verify_transition, validate, hexvalue

STATE_PATH = 'cross-agent/state.json'


def canonical_message(state):
    validate(state)
    e = state['events'][-1]
    value = f"cross-agent: {e['event']} {e['scope']} rev {e['revision']} ({e['actor']['agent']})\n"
    validate_message(value)
    return value


def git(repo, *args, data=None, extra_env=None):
    # Read stored objects, never replace refs or injected object/index directories.
    # Do not echo stderr: it can contain private metadata.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_NO_REPLACE_OBJECTS='1', GIT_TERMINAL_PROMPT='0')
    env.update(extra_env or {})
    result = subprocess.run(['git', '--no-replace-objects', '-c', 'core.hooksPath=/dev/null', '-C', str(repo), *args],
                            input=data, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=env)
    if result.returncode:
        raise ValueError(f'GIT_OPERATION_STOP_EXIT_{result.returncode}')
    return result.stdout


def snapshot(repo, head):
    if not hexvalue(head, 40):
        raise ValueError('COMMIT_ID_STOP')
    entry = git(repo, 'ls-tree', head, '--', STATE_PATH).decode().strip().split()
    if len(entry) != 4 or entry[:2] != ['100644', 'blob'] or entry[3] != STATE_PATH:
        raise ValueError('STATE_FILE_MODE_STOP')
    raw = git(repo, 'cat-file', 'blob', entry[2])
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('DUPLICATE_JSON_KEY_STOP')
            result[key] = value
        return result
    state = validate(json.loads(raw, object_pairs_hook=unique))
    return {'head': head, 'blob': entry[2], 'state': state, 'bytes': raw}


def inspect_candidate(repo, candidate, baseline, request):
    """Read actual immutable objects; never accept message/inspected attestations.

    baseline and request are independently read/authorized operator inputs.
    Private origin/read-back and release mandate remain external evidence gates.
    """
    if not hexvalue(candidate, 40) or not hexvalue(baseline['head'], 40):
        raise ValueError('COMMIT_ID_STOP')
    raw = git(repo, 'cat-file', 'commit', candidate)
    headers, message = raw.split(b'\n\n', 1)
    lines = headers.splitlines()
    if [line.split(b' ', 1)[0] for line in lines] != [b'tree', b'parent', b'author', b'committer']:
        raise ValueError('COMMIT_HEADERS_STOP')
    for line in lines[2:]:
        if not re.fullmatch(rb'(author|committer) Cross-agent <cross-agent@users.noreply.github.com> [0-9]+ [+-][0-9]{4}', line):
            raise ValueError('COMMIT_IDENTITY_METADATA_STOP')
    parents = [line[7:].decode('ascii') for line in headers.splitlines()
               if line.startswith(b'parent ')]
    if parents != [baseline['head']]:
        raise ValueError('DIRECT_PARENT_STOP')
    text = message.decode('utf-8', errors='strict')
    validate_message(text)
    paths = git(repo, 'diff-tree', '--no-commit-id', '--name-only', '--no-renames',
                '-r', '-z', baseline['head'], candidate).split(b'\0')
    if paths != [STATE_PATH.encode(), b'']:
        raise ValueError('CHANGED_PATHS_STOP')
    before = snapshot(repo, baseline['head'])
    scope = request['scope']
    if (before['blob'] != baseline['blob']
            or before['state']['state_revision'] != baseline['revision']
            or before['state']['workstreams'][scope]['owner'] != baseline['owner']):
        raise ValueError('BASELINE_STOP')
    after = snapshot(repo, candidate)
    expected = transition(before['state'], **request)
    verify_transition(before['state'], after['state'],
                      origin_verified=request.get('origin_verified', False),
                      recovery_authorized=request.get('recovery_authorized', False))
    if after['state'] != expected:
        raise ValueError('REQUEST_TRANSITION_MISMATCH_STOP')
    if text != canonical_message(after['state']):
        raise ValueError('MESSAGE_TRANSITION_MISMATCH_STOP')
    return after
