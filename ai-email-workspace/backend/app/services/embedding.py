from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.models import Embedding, Message
from app.providers.factory import get_provider
from app.utils.chunking import build_embedding_content, chunk_body


def embed_message_by_id(db: Session, message_id: int) -> int:
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        return 0
    provider = get_provider()
    chunks = chunk_body(message.body_text or "")
    content_list = [
        build_embedding_content(
            message.subject,
            message.sent_at.isoformat() if message.sent_at else "",
            message.from_email,
            ", ".join(message.to_json or []),
            chunk,
        )
        for chunk in chunks
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
    db.commit()
    return len(content_list)


def embed_message_service(message_id: int) -> int:
    """Embed a message in a dedicated DB session.

    This stays in the service layer so Celery tasks can remain thin wrappers
    without importing Celery from services.
    """
    db = SessionLocal()
    try:
        return embed_message_by_id(db, message_id)
    finally:
        db.close()
