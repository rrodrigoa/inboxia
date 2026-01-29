import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.models import MailAccount, User
from app.services.ingest_fixture import ingest_fixture_dir
from app.services.auth import hash_password


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Integration tests disabled unless RUN_INTEGRATION_TESTS=1",
)
def test_fixture_ingest():
    database_url = os.getenv("DATABASE_URL")
    assert database_url, "DATABASE_URL required"
    engine = create_engine(database_url)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    user = User(email="demo@example.com", password_hash=hash_password("password"))
    db.add(user)
    db.flush()
    account = MailAccount(
        user_id=user.id,
        kind="imap",
        imap_host="example",
        imap_user="demo",
        imap_password="demo",
        smtp_host="smtp",
        smtp_user="demo",
        smtp_password="demo",
    )
    db.add(account)
    db.commit()

    fixture_dir = Path(__file__).parent / "fixtures"
    count = ingest_fixture_dir(db, account.id, "Inbox", fixture_dir)
    assert count == 2
