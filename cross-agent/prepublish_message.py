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
