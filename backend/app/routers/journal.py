from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.core.auth import get_current_user
from app.core.crypto import UserCipher
from app.core.encryption_dep import get_user_cipher

router = APIRouter(prefix="/v1/journals", tags=["journals"])


@router.post("", response_model=schemas.JournalEntryOut, status_code=201)
def create_journal(
    payload: schemas.JournalEntryIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    cipher: UserCipher = Depends(get_user_cipher),
):
    entry = models.Journal(
        user_id=user.id,
        content_encrypted=cipher.encrypt(payload.content),
        prompt_used=payload.prompt_used,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return schemas.JournalEntryOut(
        id=entry.id,
        content=payload.content,
        prompt_used=entry.prompt_used,
        created_at=entry.created_at,
    )


@router.get("", response_model=List[schemas.JournalEntryOut])
def list_journals(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    cipher: UserCipher = Depends(get_user_cipher),
):
    entries = (
        db.query(models.Journal)
        .filter(models.Journal.user_id == user.id)
        .order_by(models.Journal.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        schemas.JournalEntryOut(
            id=e.id,
            content=cipher.decrypt(e.content_encrypted),
            prompt_used=e.prompt_used,
            created_at=e.created_at,
        )
        for e in entries
    ]


@router.delete("/{journal_id}", status_code=204)
def delete_journal(
    journal_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    entry = db.query(models.Journal).filter(
        models.Journal.id == journal_id, models.Journal.user_id == user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    db.delete(entry)
    db.commit()
