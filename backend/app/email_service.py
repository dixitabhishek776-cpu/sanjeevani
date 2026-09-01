"""
Sends real verification emails via Resend's free tier (100/day, 3,000/month,
no card, no domain-verification needed since it sends from Resend's own
onboarding@resend.dev sender for testing/demo volumes).

Set RESEND_API_KEY in the environment to enable. If unset, callers should
treat send_verification_email() returning False as "email delivery isn't
configured" and fail open (don't block registration/login on it) — a demo
project's registration flow shouldn't be hard-blocked by an email provider
being unconfigured.
"""
import os
import logging

import requests

logger = logging.getLogger("sanjeevani.email")

RESEND_API_URL = "https://api.resend.com/emails"
FROM_ADDRESS = "Sanjeevani <onboarding@resend.dev>"


def send_verification_email(to_email: str, verify_link: str) -> bool:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.info("RESEND_API_KEY not set; skipping verification email send.")
        return False
    try:
        resp = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": FROM_ADDRESS,
                "to": [to_email],
                "subject": "Verify your Sanjeevani account",
                "html": f"""
                <div style="font-family:sans-serif;max-width:480px;margin:auto;
                            padding:24px;">
                  <h2 style="color:#2E3A32;">🌱 Sanjeevani</h2>
                  <p>Welcome! Please verify your email to activate your account.</p>
                  <p>
                    <a href="{verify_link}"
                       style="background:#6E8B7A;color:white;padding:10px 20px;
                              border-radius:8px;text-decoration:none;
                              display:inline-block;">
                      Verify my email
                    </a>
                  </p>
                  <p style="color:#8A968D;font-size:12px;">
                    This link expires in 24 hours. If you didn't create a
                    Sanjeevani account, you can safely ignore this email.
                  </p>
                </div>
                """,
            },
            timeout=10,
        )
        if resp.status_code >= 300:
            logger.warning("Resend send failed: %s %s", resp.status_code, resp.text[:200])
        return resp.status_code < 300
    except Exception:
        logger.exception("Verification email send failed")
        return False


def send_reminder_email(to_email: str, name: str, app_url: str) -> bool:
    """Daily opt-in check-in reminder. Callers should only send this to
    users who enabled it AND haven't already logged a mood entry today
    (see scripts/send_daily_reminders.py) — no point nagging someone
    who already checked in."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        return False
    display_name = name or "there"
    try:
        resp = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": FROM_ADDRESS,
                "to": [to_email],
                "subject": "A moment for yourself? 🌱",
                "html": f"""
                <div style="font-family:sans-serif;max-width:480px;margin:auto;
                            padding:24px;">
                  <h2 style="color:#2E3A32;">🌱 Sanjeevani</h2>
                  <p>Hi {display_name}, just a gentle nudge — you haven't
                     checked in today.</p>
                  <p>
                    <a href="{app_url}"
                       style="background:#6E8B7A;color:white;padding:10px 20px;
                              border-radius:8px;text-decoration:none;
                              display:inline-block;">
                      Log your mood
                    </a>
                  </p>
                  <p style="color:#8A968D;font-size:12px;">
                    You're getting this because you opted in to daily
                    reminders in your Sanjeevani privacy settings. You can
                    turn this off any time from there.
                  </p>
                </div>
                """,
            },
            timeout=10,
        )
        return resp.status_code < 300
    except Exception:
        logger.exception("Reminder email send failed")
        return False
