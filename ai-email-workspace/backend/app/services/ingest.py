from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from imapclient import IMAPClient
from sqlalchemy.orm import Session

from app.models.models import Folder, MailAccount, Message
from app.tasks.jobs import embed_message
from app.utils.email_parse import parse_rfc822
from app.utils.threading import find_or_create_thread, update_thread_last_date


def _parse_references(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.replace("\n", " ").split() if item.strip()]


def _ensure_folders(db: Session, account_id: int, names: List[str]) -> List[Folder]:
    existing = {f.name: f for f in db.query(Folder).filter(Folder.account_id == account_id).all()}
    folders: List[Folder] = []
    for name in names:
        folder = existing.get(name)
        if not folder:
            folder = Folder(account_id=account_id, name=name, last_uid=0)
            db.add(folder)
            db.flush()
        folders.append(folder)
    return folders


def ingest_account_messages(db: Session, account_id: int) -> int:
    account = db.query(MailAccount).filter(MailAccount.id == account_id).first()
    if not account:
        return 0
    ingested = 0
    with IMAPClient(account.imap_host) as client:
        client.login(account.imap_user, account.imap_password)
        folders = [name.decode() if isinstance(name, bytes) else name for _, _, name in client.list_folders()]
        db_folders = _ensure_folders(db, account_id, folders)
        for folder in db_folders:
            client.select_folder(folder.name)
            uids = client.search(["UID", f"{folder.last_uid + 1}:*"])
            if not uids:
                continue
            fetch = client.fetch(uids, [b"RFC822"])
            for uid, data in fetch.items():
                raw = data[b"RFC822"]
                parsed = parse_rfc822(raw)
                references = _parse_references(parsed.get("references"))
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
                embed_message.delay(message.id)
                ingested += 1
            folder.last_uid = max(uids)
            db.commit()
    return ingested
