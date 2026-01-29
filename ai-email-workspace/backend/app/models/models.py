from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    accounts = relationship("MailAccount", back_populates="user")


class MailAccount(Base):
    __tablename__ = "mail_accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kind = Column(String(32), default="imap", nullable=False)
    imap_host = Column(String(255), nullable=False)
    imap_user = Column(String(255), nullable=False)
    imap_password = Column(String(255), nullable=False)
    smtp_host = Column(String(255), nullable=False)
    smtp_user = Column(String(255), nullable=False)
    smtp_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="accounts")
    folders = relationship("Folder", back_populates="account")
    threads = relationship("Thread", back_populates="account")


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("mail_accounts.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    last_uid = Column(Integer, default=0)

    account = relationship("MailAccount", back_populates="folders")
    messages = relationship("Message", back_populates="folder")


class Thread(Base):
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("mail_accounts.id"), nullable=False, index=True)
    thread_key = Column(String(255), nullable=False, index=True)
    subject_norm = Column(String(255), nullable=False)
    last_date = Column(DateTime(timezone=True))

    account = relationship("MailAccount", back_populates="threads")
    messages = relationship("Message", back_populates="thread")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("mail_accounts.id"), nullable=False, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=False)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=False, index=True)
    message_id_header = Column(String(255), unique=True, index=True)
    in_reply_to = Column(String(255))
    references = Column(Text)
    subject = Column(String(255))
    sent_at = Column(DateTime(timezone=True), index=True)
    from_name = Column(String(255))
    from_email = Column(String(255))
    to_json = Column(JSON, default=list)
    cc_json = Column(JSON, default=list)
    bcc_json = Column(JSON, default=list)
    body_text = Column(Text)
    body_html = Column(Text)
    raw_rfc822 = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    folder = relationship("Folder", back_populates="messages")
    thread = relationship("Thread", back_populates="messages")
    embeddings = relationship("Embedding", back_populates="message")


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    model = Column(String(128), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    vector = Column(Vector(1536))

    message = relationship("Message", back_populates="embeddings")


Index("ix_messages_account_sent", Message.account_id, Message.sent_at)
Index("ix_threads_account_key", Thread.account_id, Thread.thread_key)
Index("ix_embeddings_vector", Embedding.vector, postgresql_using="ivfflat")
