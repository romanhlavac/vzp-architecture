"""Check transport attestation and actual candidate message before publication.

This is a pre-push quality gate; it cannot itself prove the runtime or server ruleset.
"""
from prepublish_message import validate_message

def qualify(e):
    if e.get("transport") not in ("A", "B"):
        raise ValueError("TRANSPORT_STOP")
    required = (
        "fresh_baseline", "transition_verified", "scope_diff_verified",
        "remote_readback", "server_stale_rejection", "privacy_review"
    )
    if e["transport"] == "B":
        required += (
            "direct_parent", "non_force", "no_retry_rebase_merge",
            "history_protection_verified", "candidate_commit_inspected"
        )
        message = e.get("candidate_commit_message")
        if not isinstance(message, str):
            raise ValueError("COMMIT_METADATA_NOT_INSPECTED_STOP")
        validate_message(message)
    if any(e.get(key) is not True for key in required):
        raise ValueError("TRANSPORT_EVIDENCE_INCOMPLETE_STOP")
    return "SERVER_SIDE_STALE_WRITE_REJECTION_PASS"
