import importlib


def test_task_and_service_imports():
    importlib.import_module("app.tasks.jobs")
    importlib.import_module("app.services.ingest")
    importlib.import_module("app.services.embedding")


def test_embed_message_task_eager(monkeypatch):
    from app.services import embedding
    from app.tasks import jobs
    from app.tasks.celery_app import celery_app

    called = {}

    def fake_service(message_id: int) -> int:
        called["message_id"] = message_id
        return 1

    monkeypatch.setattr(embedding, "embed_message_service", fake_service)
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    result = jobs.embed_message.delay(123)
    assert result.get() == 1
    assert called["message_id"] == 123
