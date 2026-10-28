"""Risk classification only; never calls or relaxes the shared transition guard.

Evidence flags are caller attestations, not authorization or native proof.
The current normative protocol remains authoritative until coordinated cutover.
"""
from dataclasses import dataclass


class Ineligible(ValueError):
    pass


@dataclass(frozen=True)
class Operation:
    writes: bool = False
    new_private_workspace: bool = False
    owned_isolated_workspace: bool = False
    canonical_or_shared_target: bool = False
    shared_identity_change: bool = False
    promotion: bool = False
    fresh_bootstrap: bool = False
    authorized: bool = False
    permissions_verified: bool = False
    private_verified: bool = False
    exclusive_writer: bool = False
    receipt_available: bool = False


def classify(op: Operation) -> str:
    if any(type(value) is not bool for value in vars(op).values()):
        raise Ineligible('INVALID_ATTESTATION')
    if not op.writes:
        return 'A'
    if op.canonical_or_shared_target or op.shared_identity_change or op.promotion:
        return 'C'
    if not (op.new_private_workspace or op.owned_isolated_workspace):
        return 'C'
    checks = ('fresh_bootstrap', 'authorized', 'permissions_verified',
              'private_verified', 'exclusive_writer', 'receipt_available')
    if not all(getattr(op, key) for key in checks):
        raise Ineligible('ISOLATION_UNVERIFIED_STOP')
    return 'B'
