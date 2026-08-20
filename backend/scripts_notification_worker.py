"""Durable notification worker. Run as a separate process/container.
Never executes emergency dispatch; it only delivers authorized Sanjeevani notifications.
"""
import os, time, logging
from datetime import datetime, timezone, timedelta
from app.database import SessionLocal, engine
from app import models
from app.core.crypto import UserCipher, unwrap_dek
from app.services import notifications
from sqlalchemy import select, update

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"))
log=logging.getLogger("sanjeevani-notification-worker")


def claim(db):
    now=datetime.now(timezone.utc)
    # PostgreSQL workers use row locks so multiple worker replicas cannot
    # deliver the same notification concurrently.
    stale_before = now - timedelta(minutes=int(os.getenv("SANJEEVANI_NOTIFICATION_LEASE_MINUTES", "10")))
    # Recover work claimed by a worker that crashed after marking it processing.
    db.query(models.NotificationOutbox).filter(
        models.NotificationOutbox.status == "processing",
        models.NotificationOutbox.processing_at < stale_before,
    ).update({"status": "pending", "next_attempt_at": now}, synchronize_session=False)
    db.commit()
    q=(db.query(models.NotificationOutbox)
       .filter(models.NotificationOutbox.status=="pending", models.NotificationOutbox.next_attempt_at<=now)
       .order_by(models.NotificationOutbox.created_at.asc())
       .with_for_update(skip_locked=True))
    row=q.first()
    if not row:
        return None
    row.status="processing"; row.processing_at=now; row.attempts=(row.attempts or 0)+1; db.commit(); return row


def run_once():
    db=SessionLocal(); row=None
    try:
        row=claim(db)
        if not row: return False
        user_id=row.user_id
        key_row=db.query(models.UserEncryptionKey).filter(models.UserEncryptionKey.user_id==user_id, models.UserEncryptionKey.revoked_at.is_(None)).first()
        if not key_row: raise RuntimeError("user encryption key unavailable")
        cipher=UserCipher(unwrap_dek(key_row.wrapped_dek))
        recipient=cipher.decrypt(row.recipient_encrypted) if row.recipient_encrypted else None
        body=cipher.decrypt(row.body_encrypted)
        ok=notifications.send(subject=row.subject,body=body,to=recipient)
        now=datetime.now(timezone.utc)
        if ok:
            row.status="sent"; row.sent_at=now; row.processing_at=None; row.last_error=None
        else:
            row.status="pending" if row.attempts < 5 else "dead_letter"
            row.processing_at=None; row.last_error="notification provider unavailable"
            row.next_attempt_at=now+timedelta(seconds=min(300,2**row.attempts*5))
        db.commit()
        return True
    except Exception as exc:
        log.exception("notification delivery failed")
        if row:
            row.status="pending" if row.attempts < 5 else "dead_letter"
            row.last_error=str(exc)[:500]
            row.processing_at=None
            row.next_attempt_at=datetime.now(timezone.utc)+timedelta(seconds=min(300,2**row.attempts*5))
            db.commit()
        return True
    finally:
        db.close()

if __name__=="__main__":
    while True:
        run_once()
        time.sleep(float(os.getenv("SANJEEVANI_WORKER_POLL_SECONDS","2")))
