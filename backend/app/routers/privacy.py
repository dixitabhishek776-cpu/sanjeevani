"""
Privacy Dashboard endpoints (Ch.1 Sec.1, Ch.2 Sec.8: consent management,
data export, right-to-erasure). Every consent change and every export/
delete action is audit-logged, since these are exactly the actions a
compliance review will want to trace.
"""
import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.auth import get_current_user, verify_password
from app.core.crypto import UserCipher
from app.core.encryption_dep import get_user_cipher

router = APIRouter(prefix="/v1/privacy", tags=["privacy"])


def _log_audit(db: Session, actor_id, action: str, target_type: str, target_id, metadata: dict):
    db.add(models.AuditLog(
        actor_id=actor_id, action=action, target_type=target_type,
        target_id=target_id, audit_metadata=metadata,
    ))


@router.get("/preferences", response_model=schemas.UserPreferencesOut)
def get_preferences(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    prefs = db.query(models.UserPreferences).filter(models.UserPreferences.user_id == user.id).first()
    if not prefs:
        # Defensive default — every user should have a row from registration,
        # but never assume opt-in if one is somehow missing.
        prefs = models.UserPreferences(user_id=user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.patch("/preferences", response_model=schemas.UserPreferencesOut)
def update_preferences(
    payload: schemas.UserPreferencesUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    prefs = db.query(models.UserPreferences).filter(models.UserPreferences.user_id == user.id).first()
    if not prefs:
        prefs = models.UserPreferences(user_id=user.id)
        db.add(prefs)
        db.flush()

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(prefs, field, value)

    if changes:
        _log_audit(db, user.id, "consent_preferences_updated", "user_preferences", user.id, changes)

    db.commit()
    db.refresh(prefs)
    return prefs


@router.get("/export", response_model=schemas.DataExportOut)
def export_my_data(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    cipher: UserCipher = Depends(get_user_cipher),
):
    """GDPR/CCPA-style data export — returns everything decrypted, in one
    JSON payload, for the user's own account only."""
    prefs = db.query(models.UserPreferences).filter(models.UserPreferences.user_id == user.id).first()
    moods = db.query(models.MoodEntry).filter(models.MoodEntry.user_id == user.id).all()
    journals = db.query(models.Journal).filter(models.Journal.user_id == user.id).all()
    chats = db.query(models.Chat).filter(models.Chat.user_id == user.id).all()
    chat_ids = [c.id for c in chats]
    messages = db.query(models.Message).filter(models.Message.chat_id.in_(chat_ids)).all() if chat_ids else []
    memories = db.query(models.Memory).filter(models.Memory.user_id == user.id).all()

    _log_audit(db, user.id, "data_export_requested", "user", user.id, {})
    db.commit()

    return schemas.DataExportOut(
        user={"id": str(user.id), "email": user.email, "display_name": user.display_name},
        preferences=schemas.UserPreferencesOut.model_validate(prefs).model_dump() if prefs else {},
        mood_entries=[
            {"mood_score": m.mood_score, "tags": m.tags,
             "note": cipher.decrypt(m.note_encrypted) if m.note_encrypted else None,
             "logged_at": m.logged_at.isoformat()}
            for m in moods
        ],
        journals=[
            {"content": cipher.decrypt(j.content_encrypted), "created_at": j.created_at.isoformat()}
            for j in journals
        ],
        messages=[
            {"sender": m.sender, "content": cipher.decrypt(m.content_encrypted),
             "created_at": m.created_at.isoformat()}
            for m in messages
        ],
        memories=[
            {"id": str(m.id), "content": cipher.decrypt(m.content_encrypted), "category": m.category, "source": m.source, "active": m.active, "created_at": m.created_at.isoformat()}
            for m in memories
        ],
    )


@router.get("/consents", response_model=list[schemas.ConsentRecordOut])
def list_consents(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.ConsentRecord).filter(models.ConsentRecord.user_id == user.id).order_by(models.ConsentRecord.created_at.desc()).all()


@router.post("/consents", response_model=schemas.ConsentRecordOut, status_code=201)
def record_consent(payload: schemas.ConsentUpdateIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    row = models.ConsentRecord(user_id=user.id, consent_type=payload.consent_type.strip().lower(), version=payload.version.strip(), granted=payload.granted)
    db.add(row)
    _log_audit(db, user.id, "consent_recorded", "consent", row.id, {"consent_type": row.consent_type, "version": row.version, "granted": row.granted})
    db.commit(); db.refresh(row)
    return row


@router.post("/delete-account", status_code=202)
def delete_account(
    payload: schemas.AccountDeletionIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not verify_password(payload.password, user.password_hash):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid password")
    if user.deleted_at is not None:
        return {"status": "already_deleted"}

    now = dt.datetime.now(dt.timezone.utc)
    user.deleted_at = now
    key_row = db.query(models.UserEncryptionKey).filter(models.UserEncryptionKey.user_id == user.id).first()
    if key_row:
        key_row.revoked_at = now
    db.query(models.RefreshToken).filter(models.RefreshToken.user_id == user.id, models.RefreshToken.revoked_at.is_(None)).update({"revoked_at": now}, synchronize_session=False)
    _log_audit(db, user.id, "account_deletion_requested", "user", user.id, {"confirmation": True})
    db.commit()
    return {"status": "deletion_processed"}
