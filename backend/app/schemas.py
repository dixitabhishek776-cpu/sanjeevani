from typing import Optional, List
from uuid import UUID
import datetime as dt

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    display_name: Optional[str]
    role: str
    email_verified_at: Optional[dt.datetime] = None

    class Config:
        from_attributes = True


class EmailVerificationRequest(BaseModel):
    token: str = Field(min_length=20)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=12, max_length=128)

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class RefreshTokenIn(BaseModel):
    refresh_token: str = Field(min_length=20)


class ChatMessageIn(BaseModel):
    chat_id: Optional[UUID] = None
    content: str = Field(min_length=1, max_length=4000)


class SafetyInfoOut(BaseModel):
    concern_level: str
    resources_shown: bool

class InterventionOut(BaseModel):
    slug: str
    title: str
    steps: List[str]
    evidence_source: str


class ChatMessageOut(BaseModel):
    message_id: UUID
    chat_id: UUID
    ai_response: str
    resources_text: Optional[str] = None
    safety: SafetyInfoOut
    intervention: Optional[InterventionOut] = None


class MoodEntryIn(BaseModel):
    mood_score: int = Field(ge=1, le=10)
    tags: List[str] = []
    note: Optional[str] = None


class MoodEntryOut(BaseModel):
    id: UUID
    mood_score: int
    tags: List[str]
    logged_at: dt.datetime

    class Config:
        from_attributes = True


class JournalEntryIn(BaseModel):
    content: str = Field(min_length=1)
    prompt_used: Optional[str] = None


class JournalEntryOut(BaseModel):
    id: UUID
    content: str
    prompt_used: Optional[str] = None
    created_at: dt.datetime


class AlertOut(BaseModel):
    id: UUID
    status: str
    concern_level: str
    explanation: str
    created_at: dt.datetime


class UserPreferencesOut(BaseModel):
    long_term_memory_enabled: bool
    voice_emotion_enabled: bool
    wearable_integration_enabled: bool
    research_participation_opt_in: bool
    emergency_contacts_enabled: bool

    class Config:
        from_attributes = True


class UserPreferencesUpdate(BaseModel):
    long_term_memory_enabled: Optional[bool] = None
    voice_emotion_enabled: Optional[bool] = None
    wearable_integration_enabled: Optional[bool] = None
    research_participation_opt_in: Optional[bool] = None
    emergency_contacts_enabled: Optional[bool] = None


class DataExportOut(BaseModel):
    user: dict
    preferences: dict
    mood_entries: List[dict]
    journals: List[dict]
    messages: List[dict]
    memories: List[dict] = []

class ChatSummaryOut(BaseModel):
    id: UUID
    title: Optional[str]
    started_at: dt.datetime
    ended_at: Optional[dt.datetime]
    message_count: int

class ChatHistoryMessageOut(BaseModel):
    id: UUID
    sender: str
    content: str
    created_at: dt.datetime

class EmergencyContactIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=5, max_length=40)
    email: Optional[EmailStr] = None
    relationship_label: Optional[str] = Field(default=None, max_length=50)
    consent: bool = False

class EmergencyContactOut(BaseModel):
    id: UUID
    name: str
    phone_masked: str
    email_masked: Optional[str]
    relationship_label: Optional[str]
    consent_given_at: Optional[dt.datetime]
    active: bool

class WeeklySummaryOut(BaseModel):
    period_start: dt.datetime
    period_end: dt.datetime
    mood_average: Optional[float]
    mood_count: int
    journal_count: int
    chat_count: int
    elevated_safety_events: int
    highlights: List[str]


class AccountDeletionIn(BaseModel):
    password: str = Field(min_length=1, max_length=128)
    confirmation: str = Field(pattern="^DELETE MY ACCOUNT$")

class ConsentUpdateIn(BaseModel):
    consent_type: str = Field(min_length=1, max_length=80)
    version: str = Field(min_length=1, max_length=40)
    granted: bool

class ConsentRecordOut(BaseModel):
    id: UUID
    consent_type: str
    version: str
    granted: bool
    created_at: dt.datetime

    class Config:
        from_attributes = True


class MemoryIn(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    category: str = Field(default="preference", min_length=1, max_length=50)

class MemoryOut(BaseModel):
    id: UUID
    content: str
    category: str
    source: str
    created_at: dt.datetime

class MemoryUpdate(BaseModel):
    content: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    category: Optional[str] = Field(default=None, min_length=1, max_length=50)


class IdempotencyRecordOut(BaseModel):
    status_code: int
    response: dict
