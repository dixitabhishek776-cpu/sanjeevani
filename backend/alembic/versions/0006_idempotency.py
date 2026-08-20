"""add idempotency records for retry-safe chat requests"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_idempotency"
down_revision = "0005_memory_outbox"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "idempotency_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("status_code", sa.SmallInteger(), nullable=False, server_default="200"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "key", name="uq_idempotency_user_key"),
    )
    op.create_index("ix_idempotency_records_user_id", "idempotency_records", ["user_id"])

def downgrade():
    op.drop_index("ix_idempotency_records_user_id", table_name="idempotency_records")
    op.drop_table("idempotency_records")
