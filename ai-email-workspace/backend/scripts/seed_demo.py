import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# When executed as a standalone script, ensure the app package is importable.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.models.base import Base
from app.models.models import Embedding, Folder, MailAccount, Message, User
from app.providers.stub import LocalStubProvider
from app.services.auth import hash_password
from app.utils.chunking import build_embedding_content, chunk_body
from app.utils.threading import find_or_create_thread, update_thread_last_date


def ensure_folder(db, account_id: int, name: str) -> Folder:
    folder = (
        db.query(Folder)
        .filter(Folder.account_id == account_id, Folder.name == name)
        .first()
    )
    if not folder:
        folder = Folder(account_id=account_id, name=name)
        db.add(folder)
        db.flush()
    return folder


def seed_message(
    db,
    provider: LocalStubProvider,
    account_id: int,
    folder: Folder,
    subject: str,
    from_email: str,
    to_emails: list[str],
    body_text: str,
    sent_at: datetime,
    message_id: str,
    references: list[str] | None = None,
):
    thread = find_or_create_thread(
        db,
        account_id=account_id,
        subject=subject,
        from_email=from_email,
        to_emails=to_emails,
        sent_at=sent_at,
        references=references or [],
    )
    message = Message(
        account_id=account_id,
        folder_id=folder.id,
        thread_id=thread.id,
        message_id_header=message_id,
        subject=subject,
        sent_at=sent_at,
        from_email=from_email,
        to_json=to_emails,
        body_text=body_text,
    )
    db.add(message)
    db.flush()
    update_thread_last_date(thread, sent_at)
    content_list = [
        build_embedding_content(
            message.subject,
            message.sent_at.isoformat() if message.sent_at else "",
            message.from_email,
            ", ".join(message.to_json or []),
            chunk,
        )
        for chunk in chunk_body(message.body_text or "")
    ]
    vectors = provider.embed(content_list)
    db.query(Embedding).filter(Embedding.message_id == message.id).delete()
    for idx, (content, vector) in enumerate(zip(content_list, vectors)):
        db.add(
            Embedding(
                message_id=message.id,
                model=provider.__class__.__name__,
                chunk_index=idx,
                content=content,
                vector=vector,
            )
        )


def main():
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    email = os.getenv("DEMO_EMAIL", "demo@inboxia.local")
    password = os.getenv("DEMO_PASSWORD", "password")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, password_hash=hash_password(password))
        db.add(user)
        db.flush()
    account = db.query(MailAccount).filter(MailAccount.user_id == user.id).first()
    if not account:
        account = MailAccount(
            user_id=user.id,
            kind="imap",
            imap_host=os.getenv("DEMO_IMAP_HOST", "imap.example.com"),
            imap_user=os.getenv("DEMO_IMAP_USER", "demo"),
            imap_password=os.getenv("DEMO_IMAP_PASSWORD", "demo"),
            smtp_host=os.getenv("DEMO_SMTP_HOST", "smtp.example.com"),
            smtp_user=os.getenv("DEMO_SMTP_USER", "demo"),
            smtp_password=os.getenv("DEMO_SMTP_PASSWORD", "demo"),
        )
        db.add(account)
        db.flush()
    existing_message = (
        db.query(Message).filter(Message.account_id == account.id).first()
    )
    if existing_message:
        db.commit()
        print("Demo data already seeded")
        return
    inbox = ensure_folder(db, account.id, "Inbox")
    ensure_folder(db, account.id, "Sent")
    ensure_folder(db, account.id, "Archive")
    provider = LocalStubProvider()
    now = datetime.now(timezone.utc)
    seed_message(
        db,
        provider,
        account.id,
        inbox,
        subject="Welcome to Inboxia",
        from_email="founders@inboxia.local",
        to_emails=[email],
        body_text=(
            "Hi there,\n\nWelcome to Inboxia! This demo inbox shows how threads, "
            "messages, and AI chat work together.\n\nBest,\nInboxia Team"
        ),
        sent_at=now - timedelta(days=2),
        message_id="demo-1@inboxia.local",
    )
    seed_message(
        db,
        provider,
        account.id,
        inbox,
        subject="GPU cluster availability",
        from_email="ops@inboxia.local",
        to_emails=[email],
        body_text=(
            "We reserved the RTX workstation for your local LLM runs. "
            "It has 60GB VRAM. Please confirm your scheduled time slot."
        ),
        sent_at=now - timedelta(days=1, hours=3),
        message_id="demo-2@inboxia.local",
    )
    seed_message(
        db,
        provider,
        account.id,
        inbox,
        subject="Project Phoenix kickoff notes",
        from_email="pm@inboxia.local",
        to_emails=[email],
        body_text=(
            "Kickoff summary:\n- Goals: launch by end of month.\n"
            "- Risks: model latency.\n- Next steps: finalize UX, add auth flow."
        ),
        sent_at=now - timedelta(hours=6),
        message_id="demo-3@inboxia.local",
    )
    db.commit()
    print("Seeded demo user, account, and inbox messages")


if __name__ == "__main__":
    main()
