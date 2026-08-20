"""
FastAPI dependency: resolves the current user's DEK (generating and
storing a wrapped one on first use) and returns a UserCipher bound to it.
Routers use this instead of touching crypto.py or models.UserEncryptionKey
directly, keeping the envelope-encryption details in one place.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.auth import get_current_user
from app.core.crypto import generate_dek, wrap_dek, unwrap_dek, UserCipher
from app import models


def get_user_cipher(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> UserCipher:
    key_row = db.query(models.UserEncryptionKey).filter(
        models.UserEncryptionKey.user_id == user.id,
        models.UserEncryptionKey.revoked_at.is_(None),
    ).first()

    if key_row is None:
        plaintext_dek = generate_dek()
        key_row = models.UserEncryptionKey(user_id=user.id, wrapped_dek=wrap_dek(plaintext_dek))
        db.add(key_row)
        db.flush()
    else:
        plaintext_dek = unwrap_dek(key_row.wrapped_dek)

    return UserCipher(plaintext_dek)
