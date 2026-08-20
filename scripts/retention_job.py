"""Optional retention job. Disabled unless SANJEEVANI_RETENTION_ENABLED=1.
Only purges records belonging to already-deleted accounts and old notification events/outbox rows.
It deliberately does not delete active users' journals/chats without an explicit reviewed policy.
"""
import os
from datetime import datetime, timedelta, timezone
from app.database import SessionLocal
from app import models

def main():
    if os.getenv("SANJEEVANI_RETENTION_ENABLED") != "1":
        print("retention disabled"); return
    days=int(os.getenv("SANJEEVANI_DELETED_ACCOUNT_RETENTION_DAYS","30")); cutoff=datetime.now(timezone.utc)-timedelta(days=days)
    db=SessionLocal()
    try:
        deleted=db.query(models.User).filter(models.User.deleted_at.isnot(None),models.User.deleted_at < cutoff).all()
        ids=[u.id for u in deleted]
        if ids:
            # FK cascades handle user-owned records when the deployment chooses hard deletion.
            for u in deleted: db.delete(u)
        outbox_cutoff=datetime.now(timezone.utc)-timedelta(days=14)
        db.query(models.NotificationOutbox).filter(models.NotificationOutbox.status.in_(["sent","dead_letter"]),models.NotificationOutbox.created_at < outbox_cutoff).delete(synchronize_session=False)
        db.commit(); print(f"hard-deleted {len(ids)} deleted accounts; purged old outbox records")
    finally: db.close()
if __name__=="__main__": main()
