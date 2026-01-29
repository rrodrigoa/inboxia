from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.models import Message, Thread
from app.utils.subjects import normalize_subject


def _email_set(addresses: Iterable[str]) -> str:
    normalized = sorted({addr.strip().lower() for addr in addresses if addr})
    return ",".join(normalized)


def derive_thread_key(subject: str | None, from_email: str | None, to_emails: Iterable[str], sent_at: datetime) -> str:
    subject_norm = normalize_subject(subject)
    day_bucket = sent_at.astimezone(timezone.utc).strftime("%Y-%m-%d")
    participants = _email_set([from_email or "", *to_emails])
    return f"{subject_norm}|{participants}|{day_bucket}"


def find_thread_by_references(db: Session, account_id: int, references: list[str]) -> Thread | None:
    if not references:
        return None
    match = (
        db.query(Message)
        .filter(Message.account_id == account_id, Message.message_id_header.in_(references))
        .first()
    )
    if match:
        return match.thread
    return None


def find_or_create_thread(
    db: Session,
    account_id: int,
    subject: str | None,
    from_email: str | None,
    to_emails: Iterable[str],
    sent_at: datetime,
    references: list[str],
) -> Thread:
    thread = find_thread_by_references(db, account_id, references)
    subject_norm = normalize_subject(subject)
    if thread:
        return thread
    thread_key = derive_thread_key(subject, from_email, to_emails, sent_at)
    thread = (
        db.query(Thread)
        .filter(Thread.account_id == account_id, Thread.thread_key == thread_key)
        .first()
    )
    if thread:
        return thread
    thread = Thread(
        account_id=account_id,
        thread_key=thread_key,
        subject_norm=subject_norm,
        last_date=sent_at,
    )
    db.add(thread)
    db.flush()
    return thread


def update_thread_last_date(thread: Thread, sent_at: datetime) -> None:
    if not thread.last_date or sent_at > thread.last_date:
        thread.last_date = sent_at
