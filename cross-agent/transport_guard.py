"""Pre-publication permission is separate from completed transport read-back.

Private/server evidence comes from the runtime; candidate facts always come
from Git objects. This is not a server enforcement hook.
"""
from prepublish_message import inspect_candidate


def qualify(e, *, repo=None, candidate=None, baseline=None, request=None,
            phase='prepublish', readback=None):
    if e.get('transport') not in ('A', 'B') or phase not in ('prepublish', 'postpublish'):
        raise ValueError('TRANSPORT_STOP')
    required = ('fresh_baseline', 'transition_verified', 'scope_diff_verified',
                'server_stale_rejection', 'privacy_review', 'write_permission')
    if e['transport'] == 'B':
        required += ('non_force', 'no_retry_rebase_merge', 'history_protection_verified')
    if any(e.get(k) is not True for k in required):
        raise ValueError('WRITE_BLOCKED_TRANSPORT_EVIDENCE_INCOMPLETE_STOP')
    if 'candidate_commit_inspected' in e or 'candidate_commit_message' in e:
        raise ValueError('CALLER_COMMIT_ATTESTATION_STOP')
    actual = None
    if e['transport'] == 'B':
        if repo is None or candidate is None or baseline is None or request is None:
            raise ValueError('COMMIT_OBJECT_REQUIRED_STOP')
        actual = inspect_candidate(repo, candidate, baseline, request)
    if phase == 'prepublish':
        if e.get('remote_readback') is True or readback is not None:
            raise ValueError('PREMATURE_READBACK_STOP')
        return 'PREPUBLICATION_PASS'
    if e.get('remote_readback') is not True:
        raise ValueError('REMOTE_READBACK_REQUIRED_STOP')
    if actual is not None and (readback is None or readback != actual):
        raise ValueError('REMOTE_READBACK_MISMATCH_STOP')
    return 'SERVER_SIDE_STALE_WRITE_REJECTION_PASS'
