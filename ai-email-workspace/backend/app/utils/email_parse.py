from __future__ import annotations

import email
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import Any

from app.utils.sanitize import html_to_text


def _get_addresses(msg: Message, header: str) -> list[str]:
    values = msg.get_all(header, [])
    addresses: list[str] = []
    for value in values:
        for _, addr in email.utils.getaddresses([value]):
            if addr:
                addresses.append(addr)
    return addresses


def _get_body(msg: Message) -> tuple[str, str | None]:
    body_text = ""
    body_html = None
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get("Content-Disposition", "")
            if "attachment" in disposition:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if content_type == "text/plain":
                body_text += text
            elif content_type == "text/html":
                body_html = text
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            body_text = payload.decode(charset, errors="replace")
    if body_html and not body_text:
        body_text = html_to_text(body_html)
    return body_text.strip(), body_html


def parse_rfc822(raw_bytes: bytes) -> dict[str, Any]:
    msg = email.message_from_bytes(raw_bytes)
    body_text, body_html = _get_body(msg)
    sent_at = msg.get("Date")
    sent_dt = None
    if sent_at:
        try:
            sent_dt = parsedate_to_datetime(sent_at)
        except (TypeError, ValueError):
            sent_dt = None
    return {
        "message_id": msg.get("Message-ID"),
        "in_reply_to": msg.get("In-Reply-To"),
        "references": msg.get("References"),
        "subject": msg.get("Subject"),
        "sent_at": sent_dt,
        "from_name": email.utils.parseaddr(msg.get("From", ""))[0],
        "from_email": email.utils.parseaddr(msg.get("From", ""))[1],
        "to": _get_addresses(msg, "To"),
        "cc": _get_addresses(msg, "Cc"),
        "bcc": _get_addresses(msg, "Bcc"),
        "body_text": body_text,
        "body_html": body_html,
    }
