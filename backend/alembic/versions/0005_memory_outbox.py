"""memory privacy and durable notification outbox"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0005_memory_outbox"
down_revision="0004_identity_hardening"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="preference"),
        sa.Column("source", sa.String(30), nullable=False, server_default="user"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_memories_user_id","memories",["user_id"])
    op.create_table("notification_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("recipient_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_notification_outbox_status_next","notification_outbox",["status","next_attempt_at"])

def downgrade():
    op.drop_index("ix_notification_outbox_status_next", table_name="notification_outbox")
    op.drop_table("notification_outbox")
    op.drop_index("ix_memories_user_id", table_name="memories")
    op.drop_table("memories")
