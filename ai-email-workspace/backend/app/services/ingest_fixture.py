from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from app.models.models import Folder, MailAccount, Message
from app.services.embedding import embed_message_by_id
from app.utils.email_parse import parse_rfc822
from app.utils.threading import find_or_create_thread, update_thread_last_date


def ingest_fixture_dir(db: Session, account_id: int, folder_name: str, fixture_dir: Path) -> int:
    account = db.query(MailAccount).filter(MailAccount.id == account_id).first()
    if not account:
        return 0
    folder = (
        db.query(Folder)
        .filter(Folder.account_id == account_id, Folder.name == folder_name)
        .first()
    )
    if not folder:
        folder = Folder(account_id=account_id, name=folder_name)
        db.add(folder)
        db.flush()
    ingested = 0
    for path in sorted(fixture_dir.glob("*.eml")):
        raw = path.read_bytes()
        parsed = parse_rfc822(raw)
        references = []
        if parsed.get("references"):
            references.extend(parsed["references"].split())
        if parsed.get("in_reply_to"):
            references.append(parsed["in_reply_to"])
        sent_at = parsed.get("sent_at") or datetime.now(timezone.utc)
        thread = find_or_create_thread(
            db,
            account_id=account.id,
            subject=parsed.get("subject"),
            from_email=parsed.get("from_email"),
            to_emails=parsed.get("to") or [],
            sent_at=sent_at,
            references=references,
        )
        message = Message(
            account_id=account.id,
            folder_id=folder.id,
            thread_id=thread.id,
            message_id_header=parsed.get("message_id"),
            in_reply_to=parsed.get("in_reply_to"),
            references=" ".join(references),
            subject=parsed.get("subject"),
            sent_at=sent_at,
            from_name=parsed.get("from_name"),
            from_email=parsed.get("from_email"),
            to_json=parsed.get("to"),
            cc_json=parsed.get("cc"),
            bcc_json=parsed.get("bcc"),
            body_text=parsed.get("body_text"),
            body_html=parsed.get("body_html"),
            raw_rfc822=raw.decode("utf-8", errors="replace"),
        )
        db.add(message)
        update_thread_last_date(thread, sent_at)
        db.flush()
        embed_message_by_id(db, message.id)
        ingested += 1
    db.commit()
    return ingested
