from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "inboxia",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.jobs"],
)

celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])
