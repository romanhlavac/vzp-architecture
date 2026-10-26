"""Private origin validation and conflict data. Never publish this payload to Git.

The caller resolves exactly one immutable file inside the canonical private
folder and verifies its complete read-back before calling verified_claim.
No function in this module writes to Drive or Git or asserts user authorization.
"""
import datetime as dt
from prompt_state import require, hexvalue, identity, SCOPES, transition


def validate_origin(record, *, key, scope, actor):
    require(isinstance(record, dict), 'ORIGIN_SCHEMA_STOP')
    required = {'key', 'scope', 'actor', 'created_utc', 'request_id', 'purpose', 'platform'}
    optional = {'chat_title', 'chat_id', 'chat_url', 'message_id', 'message_url'}
    require(required <= record.keys() <= required | optional, 'ORIGIN_SCHEMA_STOP')
    identity(record['actor'])
    require(hexvalue(key, 32) and record['key'] == key and scope in SCOPES
            and record['scope'] == scope and record['actor'] == actor, 'ORIGIN_IDENTITY_STOP')
    require(hexvalue(record['request_id'], 32), 'ORIGIN_REQUEST_STOP')
    require(all(isinstance(record[k], str) and record[k].strip()
                for k in ('purpose', 'platform')), 'ORIGIN_DESCRIPTION_STOP')
    try:
        require(isinstance(record['created_utc'], str), 'ORIGIN_TIME_STOP')
        dt.datetime.strptime(record['created_utc'], '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        require(False, 'ORIGIN_TIME_STOP')
    for k in optional & record.keys():
        require(record[k] is None or isinstance(record[k], str), 'ORIGIN_SCHEMA_STOP')
    return record


def verified_claim(state, *, saved_origin, readback_origin, key, actor, scope,
                   expected_revision, **kwargs):
    """Use only after provider-confirmed create + independent complete read-back."""
    validate_origin(saved_origin, key=key, scope=scope, actor=actor)
    require(saved_origin == readback_origin, 'ORIGIN_READBACK_STOP')
    return transition(state, expected_revision=expected_revision, actor=actor,
                      scope=scope, event='CLAIM', claim_origin_key=key,
                      origin_verified=True, **kwargs)


def conflict_details(state, scope, origin=None):
    """Private UI data; absence of historical origin never invents a chat."""
    w = state['workstreams'][scope]
    result = {'scope': scope, 'owner': w['owner'], 'status': w['status'],
              'checkpoint': w['checkpoint'], 'origin_status': 'LEGACY_ORIGIN_UNAVAILABLE',
              'recommendation': 'Ask the owning agent to release; explicit project-owner mandate permits controlled release in another session.'}
    key = w.get('claim_origin_key')
    if key:
        require(origin is not None, 'ORIGIN_LOOKUP_STOP')
        validate_origin(origin, key=key, scope=scope, actor=w['owner'])
        result.update(origin_status='VERIFIED', origin=origin)
    return result
