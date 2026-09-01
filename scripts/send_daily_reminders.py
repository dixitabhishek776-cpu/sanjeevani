"""
Sends daily check-in reminder emails to users who opted in and haven't
logged a mood entry yet today.

Run by a scheduled GitHub Actions workflow (.github/workflows/daily-
reminder.yml) since Streamlit Cloud has no built-in cron — this script
connects directly to the same Postgres database the app uses.

Required environment variables: DATABASE_URL, RESEND_API_KEY.
Optional: SANJEEVANI_APP_URL (defaults to the deployed Streamlit URL).
"""
import os
import sys
import datetime as dt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app import models
from backend.app import email_service


def main():
    database_url = os.environ["DATABASE_URL"]
    app_url = os.getenv("SANJEEVANI_APP_URL", "https://sanjeevani-w3yji9hmnzsljkkqtkrxpe.streamlit.app")

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    today = dt.datetime.now(dt.timezone.utc).date()
    sent, skipped = 0, 0
    try:
        prefs_rows = db.query(models.UserPreferences).all()
        for prefs in prefs_rows:
            settings = prefs.notification_settings or {}
            if not settings.get("daily_reminder_enabled"):
                continue
            user = db.query(models.User).filter(
                models.User.id == prefs.user_id, models.User.deleted_at.is_(None)
            ).first()
            if not user:
                continue
            already_logged = (
                db.query(models.MoodEntry)
                .filter(
                    models.MoodEntry.user_id == user.id,
                    models.MoodEntry.logged_at >= dt.datetime.combine(today, dt.time.min, dt.timezone.utc),
                )
                .first()
            )
            if already_logged:
                skipped += 1
                continue
            ok = email_service.send_reminder_email(user.email, user.display_name, app_url)
            if ok:
                sent += 1
            else:
                skipped += 1
    finally:
        db.close()

    print(f"Daily reminders: sent={sent} skipped={skipped}")


if __name__ == "__main__":
    main()
