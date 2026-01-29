"""create tables

Revision ID: 0001_create_tables
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0001_create_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "mail_accounts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("imap_host", sa.String(length=255), nullable=False),
        sa.Column("imap_user", sa.String(length=255), nullable=False),
        sa.Column("imap_password", sa.String(length=255), nullable=False),
        sa.Column("smtp_host", sa.String(length=255), nullable=False),
        sa.Column("smtp_user", sa.String(length=255), nullable=False),
        sa.Column("smtp_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "folders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("mail_accounts.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("last_uid", sa.Integer, server_default="0"),
    )
    op.create_index("ix_folders_account", "folders", ["account_id"])

    op.create_table(
        "threads",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("mail_accounts.id"), nullable=False),
        sa.Column("thread_key", sa.String(length=255), nullable=False),
        sa.Column("subject_norm", sa.String(length=255), nullable=False),
        sa.Column("last_date", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_threads_account_key", "threads", ["account_id", "thread_key"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("mail_accounts.id"), nullable=False),
        sa.Column("folder_id", sa.Integer, sa.ForeignKey("folders.id"), nullable=False),
        sa.Column("thread_id", sa.Integer, sa.ForeignKey("threads.id"), nullable=False),
        sa.Column("message_id_header", sa.String(length=255)),
        sa.Column("in_reply_to", sa.String(length=255)),
        sa.Column("references", sa.Text),
        sa.Column("subject", sa.String(length=255)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("from_name", sa.String(length=255)),
        sa.Column("from_email", sa.String(length=255)),
        sa.Column("to_json", sa.JSON, server_default="[]"),
        sa.Column("cc_json", sa.JSON, server_default="[]"),
        sa.Column("bcc_json", sa.JSON, server_default="[]"),
        sa.Column("body_text", sa.Text),
        sa.Column("body_html", sa.Text),
        sa.Column("raw_rfc822", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_messages_account_sent", "messages", ["account_id", "sent_at"])
    op.create_index("ix_messages_thread", "messages", ["thread_id"])
    op.create_index("ix_messages_message_id_header", "messages", ["message_id_header"], unique=True)

    op.create_table(
        "embeddings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("message_id", sa.Integer, sa.ForeignKey("messages.id"), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("vector", Vector(1536)),
    )
    op.create_index("ix_embeddings_message", "embeddings", ["message_id"])
    op.create_index("ix_embeddings_vector", "embeddings", ["vector"], postgresql_using="ivfflat")


def downgrade() -> None:
    op.drop_index("ix_embeddings_vector", table_name="embeddings")
    op.drop_index("ix_embeddings_message", table_name="embeddings")
    op.drop_table("embeddings")
    op.drop_index("ix_messages_message_id_header", table_name="messages")
    op.drop_index("ix_messages_thread", table_name="messages")
    op.drop_index("ix_messages_account_sent", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_threads_account_key", table_name="threads")
    op.drop_table("threads")
    op.drop_index("ix_folders_account", table_name="folders")
    op.drop_table("folders")
    op.drop_table("mail_accounts")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
