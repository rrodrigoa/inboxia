import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base
from app.models.models import MailAccount, User
from app.services.auth import hash_password


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
    db.commit()
    print("Seeded demo user and account")


if __name__ == "__main__":
    main()
