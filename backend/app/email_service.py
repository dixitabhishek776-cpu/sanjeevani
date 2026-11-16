"""
Sends real verification emails via Resend's free tier (100/day, 3,000/month,
no card, no domain-verification needed since it sends from Resend's own
onboarding@resend.dev sender for testing/demo volumes).

Gmail SMTP (SMTP_USER + SMTP_PASSWORD, a Google "App password") is used when
set: it can email ANY address with no domain needed. Otherwise Resend is used,
but Resend's onboarding sender only delivers to the account owner.

Set RESEND_API_KEY in the environment to enable. If unset, callers should
treat send_verification_email() returning False as "email delivery isn't
configured" and fail open (don't block registration/login on it) — a demo
project's registration flow shouldn't be hard-blocked by an email provider
being unconfigured.
"""
import os
import logging
import smtplib
import ssl
from email.message import EmailMessage
from html import escape

import requests

logger = logging.getLogger("sanjeevani.email")

RESEND_API_URL = "https://api.resend.com/emails"
FROM_ADDRESS = "Sanjeevani <onboarding@resend.dev>"


def email_configured() -> bool:
    """True if any email transport is set up."""
    return bool(os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD")) or bool(os.getenv("RESEND_API_KEY"))


def _send(to_email: str, subject: str, html: str) -> bool:
    """Sends one HTML email via Gmail SMTP if configured, else Resend."""
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    if smtp_user and smtp_pass:
        try:
            msg = EmailMessage()
            msg["From"] = f"Sanjeevani <{smtp_user}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.set_content("Please view this email in an HTML-capable mail app.")
            msg.add_alternative(html, subtype="html")
            host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            with smtplib.SMTP_SSL(host, int(os.getenv("SMTP_PORT", "465")),
                                  context=ssl.create_default_context(), timeout=15) as server:
                server.login(smtp_user, smtp_pass.replace(" ", ""))
                server.send_message(msg)
            return True
        except Exception:
            logger.exception("SMTP send failed")
            return False
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.info("No email transport configured; skipping email send.")
        return False
    try:
        resp = requests.post(
            RESEND_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": FROM_ADDRESS, "to": [to_email], "subject": subject, "html": html},
            timeout=10,
        )
        if resp.status_code >= 300:
            logger.warning("Resend send failed: %s %s", resp.status_code, resp.text[:200])
        return resp.status_code < 300
    except Exception:
        logger.exception("Resend send failed")
        return False


def send_verification_email(to_email: str, verify_link: str) -> bool:
    if not email_configured():
        logger.info("No email transport set; skipping verification email send.")
        return False
    html = f"""
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
                """
    return _send(to_email, "Verify your Sanjeevani account", html)


def send_admin_alert_email(concern_level: str, explanation: str, contributing_factors, user_id: str) -> bool:
    """Notifies the app administrator by email the moment a high/immediate
    concern-level safety alert is created, so a real person actually finds
    out in near-real-time instead of relying on someone proactively
    checking the Reviewer dashboard. Set SANJEEVANI_ADMIN_EMAIL to enable."""
    admin_email = os.getenv("SANJEEVANI_ADMIN_EMAIL")
    if not email_configured() or not admin_email:
        logger.info("Email transport or SANJEEVANI_ADMIN_EMAIL not set; skipping admin alert email.")
        return False
    factors_text = escape(", ".join(contributing_factors or []) or "none listed")
    html = (
        '<div style="font-family:sans-serif;max-width:560px;margin:auto;padding:24px;">'
        '<h2 style="color:#b91c1c;">⚠️ ' + escape(concern_level.upper()) + ' concern-level alert</h2>'
        '<p><strong>User ID:</strong> ' + escape(str(user_id)) + '</p>'
        '<p><strong>Contributing factors:</strong> ' + factors_text + '</p>'
        '<p><strong>Explanation:</strong> ' + escape(explanation or "") + '</p>'
        '<p style="color:#8A968D;font-size:12px;">Open the Reviewer dashboard in the app to '
        'review and respond. This is an automated notification from Sanjeevani\'s safety system.</p>'
        '</div>'
    )
    return _send(admin_email, "⚠️ Sanjeevani safety alert: " + concern_level.upper(), html)


def send_reminder_email(to_email: str, name: str, app_url: str) -> bool:
    """Daily opt-in check-in reminder. Callers should only send this to
    users who enabled it AND haven't already logged a mood entry today
    (see scripts/send_daily_reminders.py) — no point nagging someone
    who already checked in."""
    if not email_configured():
        return False
    display_name = escape(name or "there")
    html = f"""
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
                """
    return _send(to_email, "A moment for yourself? 🌱", html)
