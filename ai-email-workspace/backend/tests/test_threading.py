from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.models.models import Message, Thread
from app.utils.threading import find_or_create_thread


def test_thread_assignment_with_reference(mocker):
    db = MagicMock()
    thread = Thread(id=1, account_id=1, thread_key="k", subject_norm="s")
    message = Message(id=1, account_id=1, thread_id=1, message_id_header="<abc>")
    message.thread = thread

    query = MagicMock()
    query.filter.return_value.first.return_value = message
    db.query.return_value = query

    result = find_or_create_thread(
        db,
        account_id=1,
        subject="Hello",
        from_email="a@example.com",
        to_emails=["b@example.com"],
        sent_at=datetime.now(timezone.utc),
        references=["<abc>"],
    )

    assert result == thread
