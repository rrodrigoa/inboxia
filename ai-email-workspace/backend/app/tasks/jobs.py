from celery import shared_task
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.services.embedding import embed_message_by_id
from app.services.ingest import ingest_account_messages


def _with_session(func):
    def wrapper(*args, **kwargs):
        db: Session = SessionLocal()
        try:
            return func(db, *args, **kwargs)
        finally:
            db.close()

    return wrapper


@shared_task
@_with_session
def ingest_account(db: Session, account_id: int) -> int:
    return ingest_account_messages(db, account_id)


@shared_task
@_with_session
def embed_message(db: Session, message_id: int) -> int:
    return embed_message_by_id(db, message_id)
