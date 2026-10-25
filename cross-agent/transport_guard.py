"""Validate transport qualification evidence; not server enforcement or a push client."""
def qualify(e):
    if e.get("transport") not in ("A","B"): raise ValueError("TRANSPORT_STOP")
    required=("fresh_baseline","transition_verified","scope_diff_verified","remote_readback","server_stale_rejection","privacy_review")
    if e["transport"]=="B": required+=("direct_parent","non_force","no_retry_rebase_merge","history_protection_verified")
    if any(e.get(k) is not True for k in required): raise ValueError("TRANSPORT_EVIDENCE_INCOMPLETE_STOP")
    return "SERVER_SIDE_STALE_WRITE_REJECTION_PASS"
