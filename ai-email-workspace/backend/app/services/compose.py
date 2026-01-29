from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import List

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import Folder, MailAccount, Message
from app.providers.factory import get_provider
from app.utils.threading import find_or_create_thread, update_thread_last_date


def draft_email(to: List[str], subject_hint: str, instructions: str) -> tuple[str, str]:
    provider = get_provider()
    prompt = (
        "Write a concise email draft.\n"
        f"To: {', '.join(to)}\n"
        f"Subject hint: {subject_hint}\n"
        f"Instructions: {instructions}\n"
        "Return a subject line and body separated by a blank line."
    )
    response = provider.chat(prompt)
    if "\n\n" in response:
        subject, body = response.split("\n\n", 1)
    else:
        subject, body = subject_hint, response
    return subject.strip(), body.strip()


def send_email(
    db: Session,
    account_id: int,
    to: List[str],
    subject: str,
    body: str,
) -> Message:
    account = db.query(MailAccount).filter(MailAccount.id == account_id).first()
    if not account:
        raise ValueError("Account not found")
    msg = EmailMessage()
    msg["From"] = account.smtp_user
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(account.smtp_host, 587) as smtp:
        smtp.starttls()
        smtp.login(account.smtp_user, account.smtp_password)
        smtp.send_message(msg)

    sent_folder = (
        db.query(Folder)
        .filter(Folder.account_id == account_id, Folder.name == "Sent")
        .first()
    )
    if not sent_folder:
        sent_folder = Folder(account_id=account_id, name="Sent")
        db.add(sent_folder)
        db.flush()

    sent_at = datetime.now(timezone.utc)
    thread = find_or_create_thread(
        db,
        account_id=account_id,
        subject=subject,
        from_email=account.smtp_user,
        to_emails=to,
        sent_at=sent_at,
        references=[],
    )
    message = Message(
        account_id=account_id,
        folder_id=sent_folder.id,
        thread_id=thread.id,
        subject=subject,
        from_email=account.smtp_user,
        to_json=to,
        body_text=body,
        sent_at=sent_at,
    )
    update_thread_last_date(thread, message.sent_at)
    db.add(message)
    db.commit()
    return message
