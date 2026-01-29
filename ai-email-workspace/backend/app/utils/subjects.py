import re


SUBJECT_PREFIX_RE = re.compile(r"^(re|fw|fwd):\s*", re.IGNORECASE)


def normalize_subject(subject: str | None) -> str:
    if not subject:
        return "(no subject)"
    cleaned = subject.strip()
    while SUBJECT_PREFIX_RE.match(cleaned):
        cleaned = SUBJECT_PREFIX_RE.sub("", cleaned).strip()
    return cleaned.lower()
