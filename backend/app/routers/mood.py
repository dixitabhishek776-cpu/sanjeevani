from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.auth import get_current_user
from app.core.crypto import UserCipher
from app.core.encryption_dep import get_user_cipher

router = APIRouter(prefix="/v1/mood", tags=["mood"])


@router.post("", response_model=schemas.MoodEntryOut, status_code=201)
def log_mood(
    payload: schemas.MoodEntryIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    cipher: UserCipher = Depends(get_user_cipher),
):
    entry = models.MoodEntry(
        user_id=user.id,
        mood_score=payload.mood_score,
        tags=payload.tags,
        note_encrypted=cipher.encrypt(payload.note) if payload.note else None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("", response_model=List[schemas.MoodEntryOut])
def list_moods(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.MoodEntry)
        .filter(models.MoodEntry.user_id == user.id)
        .order_by(models.MoodEntry.logged_at.desc())
        .limit(100)
        .all()
    )
