from celery import shared_task


@shared_task
def ingest_account(account_id: int) -> int:
    # Local import keeps service modules out of task import paths for FastAPI startup.
    from app.services.ingest import ingest_account_service

    return ingest_account_service(account_id)


@shared_task
def embed_message(message_id: int) -> int:
    # Local import keeps service modules out of task import paths for FastAPI startup.
    from app.services.embedding import embed_message_service

    return embed_message_service(message_id)
