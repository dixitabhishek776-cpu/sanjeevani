"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("type", sa.String(30)),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("display_name", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "user_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("long_term_memory_enabled", sa.Boolean, server_default=sa.false()),
        sa.Column("voice_emotion_enabled", sa.Boolean, server_default=sa.false()),
        sa.Column("wearable_integration_enabled", sa.Boolean, server_default=sa.false()),
        sa.Column("research_participation_opt_in", sa.Boolean, server_default=sa.false()),
        sa.Column("emergency_contacts_enabled", sa.Boolean, server_default=sa.false()),
        sa.Column("notification_settings", postgresql.JSONB, server_default="{}"),
    )

    op.create_table(
        "user_encryption_keys",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("wrapped_dek", sa.LargeBinary, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "chats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chats.id", ondelete="CASCADE")),
        sa.Column("sender", sa.String(10), nullable=False),
        sa.Column("content_encrypted", sa.LargeBinary, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_messages_chat_created", "messages", ["chat_id", "created_at"])

    op.create_table(
        "mood_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("mood_score", sa.SmallInteger),
        sa.Column("tags", postgresql.ARRAY(sa.String)),
        sa.Column("note_encrypted", sa.LargeBinary, nullable=True),
        sa.Column("logged_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("mood_score BETWEEN 1 AND 10", name="ck_mood_score_range"),
    )
    op.create_index("ix_mood_user_logged", "mood_entries", ["user_id", "logged_at"])

    op.create_table(
        "journals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("content_encrypted", sa.LargeBinary, nullable=False),
        sa.Column("prompt_used", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "safety_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("concern_level", sa.String(10), nullable=False),
        sa.Column("contributing_factors", postgresql.JSONB, nullable=False),
        sa.Column("explanation", sa.Text, nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("concern_level IN ('low','moderate','high','immediate')", name="ck_concern_level"),
    )
    op.create_index("ix_safety_user_level_created", "safety_assessments", ["user_id", "concern_level", "created_at"])

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("safety_assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("safety_assessments.id")),
        sa.Column("status", sa.String(20), server_default="pending_review"),
        sa.Column("assigned_reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes_encrypted", sa.LargeBinary, nullable=True),
    )
    op.create_index("ix_alerts_status", "alerts", ["status", "safety_assessment_id"])

    op.create_table(
        "emergency_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(100)),
        sa.Column("phone_encrypted", sa.LargeBinary),
        sa.Column("relationship", sa.String(50)),
        sa.Column("consent_given_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50)),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "habits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(150)),
        sa.Column("cadence", sa.String(20)),
        sa.Column("streak_count", sa.SmallInteger, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(150)),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("target_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )


def downgrade():
    op.drop_table("goals")
    op.drop_table("habits")
    op.drop_table("audit_logs")
    op.drop_table("emergency_contacts")
    op.drop_table("alerts")
    op.drop_table("safety_assessments")
    op.drop_table("journals")
    op.drop_table("mood_entries")
    op.drop_table("messages")
    op.drop_table("chats")
    op.drop_table("user_encryption_keys")
    op.drop_table("user_preferences")
    op.drop_table("users")
    op.drop_table("organizations")
