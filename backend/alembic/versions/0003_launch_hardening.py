"""launch hardening tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0003_launch_hardening"
down_revision="0002_safety_features"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table("refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_table("consent_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("consent_type", sa.String(80), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_consent_records_user_id", "consent_records", ["user_id"])
    op.create_table("intervention_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("indication", sa.String(100), nullable=False),
        sa.Column("evidence_source", sa.String(500), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true()),
        sa.Column("reviewed_by", sa.String(200)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
    )

def downgrade():
    op.drop_table("intervention_catalog")
    op.drop_index("ix_consent_records_user_id", table_name="consent_records")
    op.drop_table("consent_records")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
