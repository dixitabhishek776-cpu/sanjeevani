import uuid
import datetime as dt

from sqlalchemy import (
    Column, String, Boolean, ForeignKey, DateTime, SmallInteger, UniqueConstraint,
    CheckConstraint, LargeBinary, Numeric, Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return uuid.uuid4()


class UserEncryptionKey(Base):
    """Stores each user's Data Encryption Key, wrapped by the Master Key.
    See app/core/crypto.py for the envelope-encryption design (Ch.1 Sec.6)."""
    __tablename__ = "user_encryption_keys"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    wrapped_dek = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)
    revoked_at = Column(DateTime(timezone=True), nullable=True)  # crypto-shredding: set on account deletion


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name = Column(String(150), nullable=False)
    type = Column(String(30))  # university, corporate, hospital, ngo


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    display_name = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)
    role = Column(String(20), nullable=False, default="user")
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_count = Column(SmallInteger, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    preferences = relationship("UserPreferences", uselist=False, back_populates="user")


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    long_term_memory_enabled = Column(Boolean, default=False)
    voice_emotion_enabled = Column(Boolean, default=False)
    wearable_integration_enabled = Column(Boolean, default=False)
    research_participation_opt_in = Column(Boolean, default=False)
    emergency_contacts_enabled = Column(Boolean, default=False)
    notification_settings = Column(JSONB, default=dict)

    user = relationship("User", back_populates="preferences")


class Chat(Base):
    __tablename__ = "chats"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    started_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    title = Column(String(150), nullable=True)
    language = Column(String(20), nullable=True)


class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"))
    sender = Column(String(10), nullable=False)  # 'user' | 'ai'
    content_encrypted = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)


class MoodEntry(Base):
    __tablename__ = "mood_entries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    mood_score = Column(SmallInteger)
    tags = Column(ARRAY(String))
    note_encrypted = Column(LargeBinary, nullable=True)
    logged_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)

    __table_args__ = (CheckConstraint("mood_score BETWEEN 1 AND 10"),)


class Journal(Base):
    __tablename__ = "journals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    content_encrypted = Column(LargeBinary, nullable=False)
    prompt_used = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)


class SafetyAssessment(Base):
    __tablename__ = "safety_assessments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    concern_level = Column(String(10), nullable=False)  # low, moderate, high, immediate
    contributing_factors = Column(JSONB, nullable=False)
    explanation = Column(Text, nullable=False)
    confidence = Column(Numeric(4, 3))
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)

    __table_args__ = (
        CheckConstraint("concern_level IN ('low','moderate','high','immediate')"),
    )


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    safety_assessment_id = Column(UUID(as_uuid=True), ForeignKey("safety_assessments.id"))
    status = Column(String(20), default="pending_review")
    assigned_reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes_encrypted = Column(LargeBinary, nullable=True)


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String(100))
    phone_encrypted = Column(LargeBinary)
    relationship_label = Column("relationship", String(50))
    consent_given_at = Column(DateTime(timezone=True), nullable=True)
    email_encrypted = Column(LargeBinary, nullable=True)
    active = Column(Boolean, default=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50))
    target_id = Column(UUID(as_uuid=True), nullable=True)
    audit_metadata = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)


class Habit(Base):
    __tablename__ = "habits"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(150))
    cadence = Column(String(20))
    streak_count = Column(SmallInteger, default=0)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)


class NotificationEvent(Base):
    __tablename__ = "notification_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True)
    channel = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)
    error = Column(Text, nullable=True)


class Goal(Base):
    __tablename__ = "goals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(150))
    status = Column(String(20), default="active")
    target_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)




class Memory(Base):
    __tablename__ = "memories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content_encrypted = Column(LargeBinary, nullable=False)
    category = Column(String(50), nullable=False, default="preference")
    source = Column(String(30), nullable=False, default="user")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True)
    channel = Column(String(30), nullable=False)
    recipient_encrypted = Column(LargeBinary, nullable=True)
    subject = Column(String(255), nullable=False)
    body_encrypted = Column(LargeBinary, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    attempts = Column(SmallInteger, nullable=False, default=0)
    next_attempt_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    processing_at = Column(DateTime(timezone=True), nullable=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

class ConsentRecord(Base):
    __tablename__ = "consent_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String(80), nullable=False)
    version = Column(String(40), nullable=False)
    granted = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)

class InterventionCatalog(Base):
    __tablename__ = "intervention_catalog"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    slug = Column(String(100), nullable=False, unique=True)
    title = Column(String(200), nullable=False)
    indication = Column(String(100), nullable=False)
    evidence_source = Column(String(500), nullable=False)
    content = Column(JSONB, nullable=False)
    active = Column(Boolean, default=True)
    reviewed_by = Column(String(200), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)


class VerificationToken(Base):
    __tablename__ = "verification_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(128), nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_encrypted = Column(LargeBinary, nullable=False)
    status_code = Column(SmallInteger, nullable=False, default=200)
    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)

    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint("user_id", "key", name="uq_idempotency_user_key"),
    )
