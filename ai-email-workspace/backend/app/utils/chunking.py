from __future__ import annotations

from typing import List


def chunk_body(body: str, max_chars: int = 4000) -> List[str]:
    if len(body) <= max_chars:
        return [body]
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current: list[str] = []
    current_len = 0
    for paragraph in paragraphs:
        if current_len + len(paragraph) + 2 > max_chars and current:
            chunks.append("\n\n".join(current))
            current = [paragraph]
            current_len = len(paragraph)
        else:
            current.append(paragraph)
            current_len += len(paragraph) + 2
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def build_embedding_content(
    subject: str | None,
    sent_at: str | None,
    from_email: str | None,
    to_line: str | None,
    body: str,
) -> str:
    header = (
        f"Subject: {subject or ''}\n"
        f"Date: {sent_at or ''}\n"
        f"From: {from_email or ''}\n"
        f"To: {to_line or ''}\n\n"
    )
    return f"{header}Body: {body}"
