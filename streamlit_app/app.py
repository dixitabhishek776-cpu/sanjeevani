"""
Sanjeevani — Streamlit single-deployment version.

This reuses the existing backend/app package (models, database, agents,
encryption, rate limiter) directly as a Python library — no HTTP layer,
no JWT, no CORS, no separate frontend/backend deployment. Streamlit's
own per-browser session_state replaces the JWT/refresh-token dance
entirely, which is what eliminates the class of auth bugs the
Render+Vercel split kept hitting.

This is still a PORTFOLIO DEMO, not a certified mental-health service —
see the banner rendered on every page.
"""
import os
import requests
import sys
import datetime as dt
import hashlib
import secrets
import pyotp
import qrcode
import io
import hmac
import base64
from streamlit_cookies_manager import EncryptedCookieManager
import logging
from statistics import mean

import streamlit as st
import pandas as pd

# --- Make the existing backend/app package importable ---
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import models  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.core.auth import hash_password, verify_password  # noqa: E402
from app import email_service  # noqa: E402
from app.core.crypto import generate_dek, wrap_dek, unwrap_dek, UserCipher  # noqa: E402
from app.agents.emotion_agent import EmotionAnalysisAgent  # noqa: E402
from app.agents.safety_agent import SafetyIntelligenceAgent, decision_router  # noqa: E402
from app.agents.conversation_agent import ConversationAgent  # noqa: E402
from app.services import rate_limiter, crisis_resources  # noqa: E402
from app.incident_log import record_incident, recent_incidents  # noqa: E402

logging.basicConfig(level=os.getenv("SANJEEVANI_LOG_LEVEL", "INFO"))
logger = logging.getLogger("sanjeevani.streamlit")

emotion_agent = EmotionAnalysisAgent()
safety_agent = SafetyIntelligenceAgent()
conversation_agent = ConversationAgent()

st.set_page_config(page_title="Sanjeevani", page_icon="🌱", layout="centered")

# ---------------------------------------------------------------------------
# DB session (one per Streamlit script run — cheap, pool_pre_ping handles
# stale connections between runs)
# ---------------------------------------------------------------------------

def get_db():
    return SessionLocal()


def get_cipher(db, user) -> UserCipher:
    """Same envelope-encryption flow as backend/app/core/encryption_dep.py,
    called directly instead of through a FastAPI dependency."""
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


def safe_decrypt(cipher: UserCipher, ciphertext) -> str:
    """Decrypts, but never crashes the page. If SANJEEVANI_MASTER_KEY was
    ever rotated, entries encrypted under the old key can no longer be
    decrypted — that's an expected, permanent consequence of key rotation
    (by design: the app never has the old key sitting around "just in
    case"). Rather than letting that throw and crash the whole page, show
    a clear inline message for just that one entry."""
    if not ciphertext:
        return ""
    try:
        return cipher.decrypt(ciphertext)
    except Exception:
        return "⚠️ Could not decrypt this entry (it may have been saved under a since-rotated encryption key)."


def transcribe_audio(audio_bytes: bytes) -> str:
    """Voice input: sends recorded audio to Groq's free Whisper endpoint
    (2,000 requests/day free, no card) and returns the transcribed text.
    Returns "" on any failure — caller shows a friendly message rather
    than crashing the chat page over a transcription hiccup."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return ""
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": ("audio.wav", audio_bytes, "audio/wav")},
            data={"model": "whisper-large-v3-turbo"},
            timeout=20,
        )
        if resp.status_code < 300:
            return resp.json().get("text", "").strip()
        logging.getLogger("sanjeevani.streamlit").warning(
            "Transcription failed: %s %s", resp.status_code, resp.text[:200]
        )
        return ""
    except Exception:
        logging.getLogger("sanjeevani.streamlit").exception("Transcription request failed")
        return ""


# ---------------------------------------------------------------------------
# Persistent login ("remember me") via an encrypted browser cookie
# ---------------------------------------------------------------------------
_cookies = None


def get_cookies():
    """EncryptedCookieManager needs a moment to sync with the browser on
    first load — .ready() tells us whether that round-trip has completed
    yet. Until it has, we must not read/write cookies or make login
    decisions based on them (that's the bug that made session persistence
    silently fail before): we stop this run and let Streamlit's own
    automatic rerun (triggered by the component once it's ready) pick
    things up a moment later."""
    global _cookies
    if _cookies is None:
        secret = os.getenv("SANJEEVANI_SESSION_SECRET") or os.getenv("SANJEEVANI_MASTER_KEY") or "insecure-dev-secret"
        _cookies = EncryptedCookieManager(prefix="sanjeevani/", password=secret)
    if not _cookies.ready():
        st.stop()
    return _cookies


def make_session_token(user_id: str, days: int = 30) -> str:
    expiry = int((dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=days)).timestamp())
    return f"{user_id}|{expiry}"


def verify_session_token(token: str):
    try:
        user_id, expiry = token.split("|")
        if int(expiry) < int(dt.datetime.now(dt.timezone.utc).timestamp()):
            return None
        return user_id
    except Exception:
        return None


def set_session_cookie(user_id: str):
    cookies = get_cookies()
    cookies["sanjeevani_session"] = make_session_token(user_id)
    cookies.save()


def clear_session_cookie():
    cookies = get_cookies()
    if "sanjeevani_session" in cookies:
        del cookies["sanjeevani_session"]
        cookies.save()


def restore_session_from_cookie():
    """Runs before the login check — if a valid remember-me cookie exists
    from a previous visit, this signs the person back in automatically
    instead of making them log in again after every page refresh."""
    if "user_id" in st.session_state:
        return
    cookies = get_cookies()
    token = cookies.get("sanjeevani_session")
    if not token:
        return
    user_id = verify_session_token(token)
    if user_id:
        st.session_state["user_id"] = user_id


def compute_mood_streak(db, user):
    """Consecutive-day streak of mood logging, counting back from today.
    A streak survives a "today, no entry yet" gap (still counts if
    yesterday had one) but breaks on any actual missed day. Returns
    (current_streak, longest_streak_ever)."""
    entries = (
        db.query(models.MoodEntry.logged_at)
        .filter(models.MoodEntry.user_id == user.id)
        .order_by(models.MoodEntry.logged_at.desc())
        .all()
    )
    logged_days = sorted({e.logged_at.date() for e in entries}, reverse=True)
    if not logged_days:
        return 0, 0

    today = dt.datetime.now(dt.timezone.utc).date()
    current = 0
    cursor = today
    day_set = set(logged_days)
    if today not in day_set:
        cursor = today - dt.timedelta(days=1)
    while cursor in day_set:
        current += 1
        cursor -= dt.timedelta(days=1)

    longest = 1
    run = 1
    for i in range(1, len(logged_days)):
        if (logged_days[i - 1] - logged_days[i]).days == 1:
            run += 1
        else:
            longest = max(longest, run)
            run = 1
    longest = max(longest, run, current)
    return current, longest


STREAK_MILESTONES = [3, 7, 14, 30, 60, 100]


def streak_badge_for(streak: int) -> str:
    reached = [m for m in STREAK_MILESTONES if streak >= m]
    return f"{reached[-1]}-day badge 🏅" if reached else ""


def _log_audit(db, actor_id, action, target_type, target_id, metadata):
    db.add(models.AuditLog(
        actor_id=actor_id, action=action, target_type=target_type,
        target_id=target_id, audit_metadata=metadata,
    ))


# ---------------------------------------------------------------------------
# Demo banner — always visible, every page
# ---------------------------------------------------------------------------

def render_banner():
    st.markdown(
        """
        <style>
        /* Hide the small anchor-link icon Streamlit auto-adds next to every
           header/subheader — on mobile, tapping it opens the browser's
           "copy link / download link" menu instead of being useful. */
        [data-testid="stHeaderActionElements"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="background:#b91c1c;color:#fff;padding:10px 16px;
        border-radius:6px;text-align:center;font-size:14px;font-weight:600;
        margin-bottom:16px;line-height:1.4;">
        ⚠️ PORTFOLIO DEMO — This is a student engineering project, not a
        real crisis-support service. It has not been clinically or legally
        reviewed. If you are in crisis, please contact a real local
        emergency service or crisis line instead.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(crisis_resources("IN"))


# ---------------------------------------------------------------------------
# Auth pages
# ---------------------------------------------------------------------------

def page_login_register():
    st.title("🌱 Sanjeevani")
    st.write("A space to reflect. Not a substitute for therapy or medical care.")

    tab_login, tab_register = st.tabs(["Sign in", "Create account"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in")
        if submitted:
            db = get_db()
            try:
                email_norm = email.strip().lower()
                if not rate_limiter.allow(f"login:{email_norm}"):
                    st.error("Too many login attempts. Please wait a moment and try again.")
                    return
                user = db.query(models.User).filter(models.User.email == email_norm).first()
                now = dt.datetime.now(dt.timezone.utc)
                if not user or user.deleted_at is not None:
                    st.error("Incorrect email or password.")
                    return
                if user.locked_until and user.locked_until > now:
                    st.error("Account temporarily locked. Please try again later.")
                    return
                if not verify_password(password, user.password_hash):
                    user.failed_login_count = (user.failed_login_count or 0) + 1
                    if user.failed_login_count >= 5:
                        user.locked_until = now + dt.timedelta(minutes=15)
                        user.failed_login_count = 0
                    db.commit()
                    st.error("Incorrect email or password.")
                    return
                user.failed_login_count = 0
                user.locked_until = None
                db.commit()

                prefs = db.query(models.UserPreferences).filter(
                    models.UserPreferences.user_id == user.id
                ).first()
                totp_settings = (prefs.notification_settings or {}) if prefs else {}
                if totp_settings.get("totp_enabled"):
                    st.session_state["pending_2fa_user_id"] = str(user.id)
                    st.rerun()
                else:
                    st.session_state["user_id"] = str(user.id)
                    set_session_cookie(str(user.id))
                    st.rerun()
            finally:
                db.close()

    if st.session_state.get("pending_2fa_user_id"):
        st.divider()
        st.write("**Two-factor authentication**")
        st.caption("Enter the 6-digit code from your authenticator app.")
        with st.form("totp_form"):
            code = st.text_input("Code", max_chars=6)
            totp_submitted = st.form_submit_button("Verify")
        if totp_submitted:
            db = get_db()
            try:
                uid = st.session_state["pending_2fa_user_id"]
                if not rate_limiter.allow(f"totp:{uid}"):
                    st.error("Too many attempts. Please wait a moment and try again.")
                    return
                prefs = db.query(models.UserPreferences).filter(
                    models.UserPreferences.user_id == uid
                ).first()
                secret = (prefs.notification_settings or {}).get("totp_secret") if prefs else None
                if secret and pyotp.TOTP(secret).verify(code.strip(), valid_window=1):
                    del st.session_state["pending_2fa_user_id"]
                    st.session_state["user_id"] = uid
                    set_session_cookie(uid)
                    st.rerun()
                else:
                    st.error("Incorrect code. Please try again.")
            finally:
                db.close()
        return

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("Name", key="reg_name")
            email_r = st.text_input("Email", key="reg_email")
            password_r = st.text_input(
                "Password", type="password", key="reg_password",
                help="Use at least 12 characters.",
            )
            submitted_r = st.form_submit_button("Create account")
        if submitted_r:
            db = get_db()
            try:
                if password_r.strip() != password_r or len(password_r) < 12:
                    st.error("Password must be at least 12 characters, with no leading/trailing spaces.")
                    return
                email_norm = email_r.strip().lower()
                if not email_norm or "@" not in email_norm:
                    st.error("Please enter a valid email address.")
                    return
                if not rate_limiter.allow(f"register:{email_norm}"):
                    st.error("Too many attempts. Please try again later.")
                    return
                if db.query(models.User).filter(models.User.email == email_norm).first():
                    st.error("Email already registered. Try signing in instead.")
                    return
                user = models.User(
                    email=email_norm,
                    password_hash=hash_password(password_r),
                    display_name=name.strip() or None,
                    email_verified_at=None,
                )
                db.add(user)
                db.flush()
                db.add(models.UserPreferences(user_id=user.id))
                db.add(models.ConsentRecord(
                    user_id=user.id, consent_type="terms",
                    version=os.getenv("SANJEEVANI_TERMS_VERSION", "1.0"), granted=True,
                ))
                verify_raw = secrets.token_urlsafe(48)
                db.add(models.VerificationToken(
                    user_id=user.id,
                    token_hash=hashlib.sha256(verify_raw.encode()).hexdigest(),
                    expires_at=dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=24),
                ))
                db.commit()
                app_url = os.getenv("SANJEEVANI_APP_URL", "https://sanjeevani-w3yji9hmnzsljkkqtkrxpe.streamlit.app")
                verify_link = f"{app_url}/?verify={verify_raw}"
                email_sent = email_service.send_verification_email(email_norm, verify_link)
                if email_sent:
                    st.success("Account created! Check your email for a verification link.")
                else:
                    # Demo fallback: no email provider configured (or send
                    # failed) — don't lock the user out of a demo, but be
                    # honest that verification wasn't actually completed.
                    st.success("Account created!")
                    st.info(
                        "Email verification isn't configured on this deployment, "
                        "so your account starts unverified — you can still sign "
                        "in and use the app."
                    )
            finally:
                db.close()


# ---------------------------------------------------------------------------
# Chat page
# ---------------------------------------------------------------------------

def page_chat(db, user):
    st.subheader("Chat")
    st.caption("Start whenever you're ready. There's no wrong way to begin.")

    LANGUAGES = ["English", "Hindi", "Hinglish", "Tamil", "Telugu", "Bengali", "Marathi", "Gujarati"]
    st.session_state.setdefault("chat_language", "English")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.selectbox("Language", LANGUAGES, key="chat_language")
    with col_b:
        st.session_state.setdefault("speak_replies", False)
        st.checkbox("🔊 Read replies aloud", key="speak_replies")

    if "chat_id" not in st.session_state:
        st.session_state["chat_id"] = None
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["sender"]):
            st.write(msg["text"])
            if msg.get("resources_text"):
                st.warning(msg["resources_text"])

    if st.session_state["speak_replies"] and st.session_state["chat_history"]:
        last = st.session_state["chat_history"][-1]
        last_idx = len(st.session_state["chat_history"]) - 1
        if last["sender"] == "assistant" and st.session_state.get("last_spoken_idx") != last_idx:
            st.session_state["last_spoken_idx"] = last_idx
            safe_text = last["text"].replace("`", "'").replace("\\", "").replace("</script>", "")
            st.components.v1.html(
                f"""
                <script>
                  var u = new SpeechSynthesisUtterance({safe_text!r});
                  window.parent.speechSynthesis.cancel();
                  window.parent.speechSynthesis.speak(u);
                </script>
                """,
                height=0,
            )

    audio_value = st.audio_input("Or record your message")
    prompt = st.chat_input("Type how you're feeling...")

    if audio_value is not None:
        audio_bytes = audio_value.getvalue()
        audio_hash = hashlib.sha256(audio_bytes).hexdigest()
        if st.session_state.get("last_audio_hash") != audio_hash:
            st.session_state["last_audio_hash"] = audio_hash
            with st.spinner("Transcribing..."):
                transcribed = transcribe_audio(audio_bytes)
            if transcribed:
                prompt = transcribed
            else:
                st.warning("Couldn't transcribe that — please try again or type instead.")

    if not prompt:
        return

    cipher = get_cipher(db, user)

    if not rate_limiter.allow(f"chat:{user.id}"):
        st.error("Too many messages. Please wait a moment and try again.")
        return

    chat_id = st.session_state["chat_id"]
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id, models.Chat.user_id == user.id).first() if chat_id else None
    if not chat:
        chat = models.Chat(user_id=user.id)
        db.add(chat)
        db.flush()
        st.session_state["chat_id"] = str(chat.id)

    user_msg = models.Message(chat_id=chat.id, sender="user", content_encrypted=cipher.encrypt(prompt))
    db.add(user_msg)
    db.flush()

    emotion_signal = emotion_agent.analyze(prompt)

    recent = (
        db.query(models.SafetyAssessment.concern_level)
        .filter(models.SafetyAssessment.user_id == user.id)
        .order_by(models.SafetyAssessment.created_at.desc())
        .limit(10).all()
    )
    recent_levels = [r[0] for r in reversed(recent)]

    active_alert = (
        db.query(models.Alert)
        .join(models.SafetyAssessment, models.Alert.safety_assessment_id == models.SafetyAssessment.id)
        .filter(
            models.SafetyAssessment.user_id == user.id,
            models.SafetyAssessment.concern_level.in_(["high", "immediate"]),
            models.Alert.status.in_(["pending_review", "acknowledged"]),
        )
        .order_by(models.SafetyAssessment.created_at.desc())
        .first()
    )
    active_floor = None
    if active_alert:
        active_floor = db.query(models.SafetyAssessment.concern_level).filter(
            models.SafetyAssessment.id == active_alert.safety_assessment_id
        ).scalar()

    assessment = safety_agent.assess(prompt, emotion_signal, recent_levels, active_floor)
    directive = decision_router(assessment)

    safety_record = models.SafetyAssessment(
        user_id=user.id, message_id=user_msg.id,
        concern_level=assessment.concern_level,
        contributing_factors=assessment.contributing_factors,
        explanation=assessment.explanation, confidence=assessment.confidence,
    )
    db.add(safety_record)
    db.flush()

    if directive["create_alert"]:
        alert = models.Alert(safety_assessment_id=safety_record.id, status="pending_review")
        db.add(alert)
        db.flush()
        _log_audit(
            db, user.id, "safety_alert_created", "safety_assessment", safety_record.id,
            {"concern_level": assessment.concern_level, "escalation": directive["human_escalation"]},
        )

    ai_reply = conversation_agent.generate_response(
        prompt, directive, assessment.concern_level, language=st.session_state["chat_language"]
    )

    ai_msg = models.Message(chat_id=chat.id, sender="ai", content_encrypted=cipher.encrypt(ai_reply["text"]))
    db.add(ai_msg)
    db.flush()
    db.commit()

    st.session_state["chat_history"].append({"sender": "user", "text": prompt})
    st.session_state["chat_history"].append({
        "sender": "assistant", "text": ai_reply["text"],
        "resources_text": ai_reply["resources_text"],
    })
    st.rerun()


# ---------------------------------------------------------------------------
# Mood page
# ---------------------------------------------------------------------------

def page_mood(db, user):
    st.subheader("Mood")
    with st.form("mood_form"):
        score = st.slider("How are you feeling right now? (1 = very low, 10 = very good)", 1, 10, 5)
        tags = st.multiselect("Tags (optional)", ["anxious", "tired", "calm", "stressed", "hopeful", "sad", "grateful", "overwhelmed"])
        note = st.text_area("Note (optional, private and encrypted)")
        submitted = st.form_submit_button("Log mood")
    if submitted:
        cipher = get_cipher(db, user)
        entry = models.MoodEntry(
            user_id=user.id, mood_score=score, tags=tags,
            note_encrypted=cipher.encrypt(note) if note else None,
        )
        db.add(entry)
        db.commit()
        st.success("Mood logged.")

    st.divider()

    entries = (
        db.query(models.MoodEntry)
        .filter(models.MoodEntry.user_id == user.id)
        .order_by(models.MoodEntry.logged_at.desc())
        .limit(30)
        .all()
    )

    if not entries:
        st.caption("No mood entries yet — log your first one above to start seeing your trend.")
    else:
        from datetime import datetime, timedelta

        now = datetime.now()
        today = now.date()
        start_date = today - timedelta(days=6)

        # Keep only entries from the last 7 calendar days, including today.
        recent_entries = [
            e for e in entries
            if e.logged_at.date() >= start_date
        ]

        st.write("**Your mood trend — last 7 calendar days**")

        daily_averages = []
        daily_labels = []

        for offset in range(6, -1, -1):
            day = today - timedelta(days=offset)
            day_scores = [
                e.mood_score for e in recent_entries
                if e.logged_at.date() == day
            ]

            if day_scores:
                daily_avg = sum(day_scores) / len(day_scores)
                daily_averages.append(daily_avg)
                daily_labels.append(day.strftime("%b %d"))
            else:
                daily_averages.append(float("nan"))
                daily_labels.append(day.strftime("%b %d"))

        chart_data = pd.DataFrame(
            {"Daily average": daily_averages},
            index=daily_labels,
        )

        st.line_chart(chart_data, y="Daily average", height=250)

        valid_daily_averages = [
            value for value in daily_averages
            if pd.notna(value)
        ]

        if valid_daily_averages:
            avg_7_day = sum(valid_daily_averages) / len(valid_daily_averages)

            if len(valid_daily_averages) >= 2:
                trend = valid_daily_averages[-1] - valid_daily_averages[0]
            else:
                trend = 0

            col1, col2 = st.columns(2)
            col1.metric("7-day average", f"{avg_7_day:.1f}/10")
            col2.metric(
                "Trend",
                f"{'+' if trend >= 0 else ''}{trend:.1f}",
                delta=f"{trend:+.1f}",
            )

            st.write("**Daily averages**")
            for label, value in zip(daily_labels, daily_averages):
                if pd.notna(value):
                    st.write(f"**{label}** — {value:.1f}/10")
                else:
                    st.write(f"**{label}** — No mood logged")

        if recent_entries:
            st.write("**Mood history — last 7 calendar days**")
            for e in recent_entries:
                st.write(
                    f"**{e.mood_score}/10** — "
                    f"{', '.join(e.tags or [])} · "
                    f"{e.logged_at.strftime('%b %d, %Y %H:%M')}"
                )
        else:
            st.caption("No mood entries in the last 7 calendar days.")


# ---------------------------------------------------------------------------
# Journal page
# ---------------------------------------------------------------------------

def page_journal(db, user):
    st.subheader("Journal")
    cipher = get_cipher(db, user)
    with st.form("journal_form"):
        content = st.text_area("What's on your mind?", height=150)
        submitted = st.form_submit_button("Save entry")
    if submitted and content.strip():
        entry = models.Journal(user_id=user.id, content_encrypted=cipher.encrypt(content))
        db.add(entry)
        db.commit()
        st.success("Journal entry saved.")

    st.divider()
    entries = (
        db.query(models.Journal).filter(models.Journal.user_id == user.id)
        .order_by(models.Journal.created_at.desc()).limit(50).all()
    )
    if not entries:
        st.caption("No journal entries yet.")
    for e in entries:
        with st.expander(e.created_at.strftime("%b %d, %Y %H:%M")):
            st.write(safe_decrypt(cipher, e.content_encrypted))
            if st.button("Delete", key=f"del_journal_{e.id}"):
                db.delete(e)
                db.commit()
                st.rerun()


# ---------------------------------------------------------------------------
# Weekly summary page
# ---------------------------------------------------------------------------

def page_summary(db, user):
    st.subheader("Weekly summary")
    end = dt.datetime.now(dt.timezone.utc)
    start = end - dt.timedelta(days=7)
    moods = db.query(models.MoodEntry).filter(models.MoodEntry.user_id == user.id, models.MoodEntry.logged_at >= start).all()
    journals = db.query(models.Journal).filter(models.Journal.user_id == user.id, models.Journal.created_at >= start).count()
    chats = db.query(models.Chat).filter(models.Chat.user_id == user.id, models.Chat.started_at >= start).count()
    elevated = db.query(models.SafetyAssessment).filter(
        models.SafetyAssessment.user_id == user.id,
        models.SafetyAssessment.created_at >= start,
        models.SafetyAssessment.concern_level.in_(["moderate", "high", "immediate"]),
    ).count()
    avg = round(mean([m.mood_score for m in moods]), 2) if moods else None

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg mood", f"{avg}/10" if avg is not None else "—")
    col2.metric("Journal entries", journals)
    col3.metric("Chats", chats)
    if elevated:
        st.warning(f"{elevated} elevated wellbeing check-in(s) this week — consider reviewing how you're feeling.")
    if not (moods or journals or chats):
        st.caption("No activity recorded this week. A small check-in can be a useful place to start.")


# ---------------------------------------------------------------------------
# Privacy dashboard
# ---------------------------------------------------------------------------

def page_privacy(db, user):
    st.subheader("Privacy & data")
    prefs = db.query(models.UserPreferences).filter(models.UserPreferences.user_id == user.id).first()
    if not prefs:
        prefs = models.UserPreferences(user_id=user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    with st.form("prefs_form"):
        ltm = st.checkbox("Long-term memory", value=prefs.long_term_memory_enabled)
        voice = st.checkbox("Voice emotion analysis", value=prefs.voice_emotion_enabled)
        wearable = st.checkbox("Wearable integration", value=prefs.wearable_integration_enabled)
        research = st.checkbox("Research participation (opt-in)", value=prefs.research_participation_opt_in)
        contacts_enabled = st.checkbox("Emergency contacts enabled", value=prefs.emergency_contacts_enabled)
        submitted = st.form_submit_button("Save preferences")
    if submitted:
        changes = {
            "long_term_memory_enabled": ltm, "voice_emotion_enabled": voice,
            "wearable_integration_enabled": wearable, "research_participation_opt_in": research,
            "emergency_contacts_enabled": contacts_enabled,
        }
        for k, v in changes.items():
            setattr(prefs, k, v)
        _log_audit(db, user.id, "consent_preferences_updated", "user_preferences", user.id, changes)
        db.commit()
        st.success("Preferences saved.")

    st.divider()
    st.write("**Two-factor authentication**")
    settings = prefs.notification_settings or {}

    if settings.get("totp_enabled"):
        st.success("2FA is enabled on your account.")
        with st.form("disable_2fa_form"):
            confirm_code = st.text_input("Enter a current code from your authenticator app to disable 2FA", max_chars=6)
            disable_submitted = st.form_submit_button("Disable 2FA")
        if disable_submitted:
            secret = settings.get("totp_secret")
            if secret and pyotp.TOTP(secret).verify(confirm_code.strip(), valid_window=1):
                settings["totp_enabled"] = False
                settings["totp_secret"] = None
                prefs.notification_settings = settings
                _log_audit(db, user.id, "2fa_disabled", "user_preferences", user.id, {})
                db.commit()
                st.success("2FA disabled.")
                st.rerun()
            else:
                st.error("Incorrect code.")
    else:
        st.caption("Add an extra layer of security using an authenticator app (Google Authenticator, Authy, etc.).")
        if "pending_totp_secret" not in st.session_state:
            if st.button("Set up 2FA"):
                st.session_state["pending_totp_secret"] = pyotp.random_base32()
                st.rerun()
        else:
            secret = st.session_state["pending_totp_secret"]
            uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Sanjeevani")
            qr_img = qrcode.make(uri)
            buf = io.BytesIO()
            qr_img.save(buf, format="PNG")
            st.image(buf.getvalue(), width=220, caption="Scan with your authenticator app")
            st.code(secret, language=None)
            st.caption("Or enter this key manually if you can't scan the code.")
            with st.form("confirm_2fa_form"):
                verify_code = st.text_input("Enter the 6-digit code to confirm setup", max_chars=6)
                confirm_submitted = st.form_submit_button("Confirm & enable 2FA")
            if confirm_submitted:
                if pyotp.TOTP(secret).verify(verify_code.strip(), valid_window=1):
                    settings["totp_enabled"] = True
                    settings["totp_secret"] = secret
                    prefs.notification_settings = settings
                    _log_audit(db, user.id, "2fa_enabled", "user_preferences", user.id, {})
                    db.commit()
                    del st.session_state["pending_totp_secret"]
                    st.success("2FA enabled!")
                    st.rerun()
                else:
                    st.error("Incorrect code. Please try again.")
            if st.button("Cancel setup"):
                del st.session_state["pending_totp_secret"]
                st.rerun()

    st.divider()
    if st.button("Export my data (JSON)"):
        cipher = get_cipher(db, user)
        moods = db.query(models.MoodEntry).filter(models.MoodEntry.user_id == user.id).all()
        journals = db.query(models.Journal).filter(models.Journal.user_id == user.id).all()
        export = {
            "user": {"id": str(user.id), "email": user.email, "display_name": user.display_name},
            "mood_entries": [{"mood_score": m.mood_score, "tags": m.tags, "logged_at": m.logged_at.isoformat()} for m in moods],
            "journals": [{"content": safe_decrypt(cipher, j.content_encrypted), "created_at": j.created_at.isoformat()} for j in journals],
        }
        _log_audit(db, user.id, "data_export_requested", "user", user.id, {})
        db.commit()
        st.json(export)

    st.divider()
    st.write("**Delete account**")
    with st.form("delete_form"):
        pw = st.text_input("Confirm your password", type="password")
        confirm = st.checkbox("I understand this cannot be undone")
        del_submit = st.form_submit_button("Delete my account", type="primary")
    if del_submit:
        if not verify_password(pw, user.password_hash):
            st.error("Incorrect password.")
        elif not confirm:
            st.error("Please confirm you understand this is permanent.")
        else:
            now = dt.datetime.now(dt.timezone.utc)
            user.deleted_at = now
            key_row = db.query(models.UserEncryptionKey).filter(models.UserEncryptionKey.user_id == user.id).first()
            if key_row:
                key_row.revoked_at = now
            _log_audit(db, user.id, "account_deletion_requested", "user", user.id, {"confirmation": True})
            db.commit()
            st.session_state.clear()
            st.success("Account deleted.")
            st.rerun()

    st.divider()
    if user.role == "user" and os.getenv("SANJEEVANI_DEMO_MODE", "false").lower() in {"1", "true", "yes"}:
        st.caption("Demo-only: grant yourself reviewer access to try the reviewer dashboard.")
        if st.button("Grant myself reviewer access (demo)"):
            user.role = "reviewer"
            db.commit()
            st.success("You now have reviewer access. Reload the sidebar to see it.")
            st.rerun()


# ---------------------------------------------------------------------------
# Emergency contacts
# ---------------------------------------------------------------------------

def _mask(v):
    return ("*" * max(0, len(v) - 4) + v[-4:]) if v else ""


def page_contacts(db, user):
    st.subheader("Emergency contacts")
    cipher = get_cipher(db, user)

    with st.form("contact_form"):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        email_c = st.text_input("Email (optional)")
        relationship = st.text_input("Relationship (optional)")
        consent = st.checkbox("This person has consented to be listed as my emergency contact")
        submitted = st.form_submit_button("Add contact")
    if submitted:
        if not consent:
            st.error("Explicit consent is required before an emergency contact can be activated.")
        elif not name.strip() or not phone.strip():
            st.error("Name and phone are required.")
        else:
            c = models.EmergencyContact(
                user_id=user.id, name=name.strip(), phone_encrypted=cipher.encrypt(phone.strip()),
                email_encrypted=cipher.encrypt(email_c.strip()) if email_c.strip() else None,
                relationship_label=relationship.strip() or None,
                consent_given_at=dt.datetime.now(dt.timezone.utc), active=True,
            )
            db.add(c)
            db.commit()
            st.success("Contact added.")
            st.rerun()

    st.divider()
    contacts = db.query(models.EmergencyContact).filter(
        models.EmergencyContact.user_id == user.id, models.EmergencyContact.active.is_(True)
    ).all()
    if not contacts:
        st.caption("No emergency contacts added yet.")
    for c in contacts:
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{c.name}** ({c.relationship_label or 'unspecified'}) — {_mask(safe_decrypt(cipher, c.phone_encrypted))}")
        if col2.button("Remove", key=f"rm_contact_{c.id}"):
            c.active = False
            db.commit()
            st.rerun()


# ---------------------------------------------------------------------------
# Reviewer dashboard
# ---------------------------------------------------------------------------

def page_reviewer(db, user):
    st.subheader("Reviewer dashboard")
    st.caption("Visible only to accounts with reviewer / super_admin role.")

    status_filter = st.selectbox("Status", ["pending_review", "acknowledged", "resolved", None], format_func=lambda s: s or "All")
    q = (
        db.query(models.Alert, models.SafetyAssessment)
        .join(models.SafetyAssessment, models.Alert.safety_assessment_id == models.SafetyAssessment.id)
    )
    if status_filter:
        q = q.filter(models.Alert.status == status_filter)
    rows = q.order_by(models.SafetyAssessment.created_at.desc()).limit(100).all()

    if not rows:
        st.caption("No alerts matching this filter.")
    for alert, assessment in rows:
        with st.expander(f"[{assessment.concern_level.upper()}] {assessment.created_at.strftime('%b %d, %H:%M')} — {alert.status}"):
            st.write(assessment.explanation)
            st.write("Contributing factors:", ", ".join(assessment.contributing_factors or []))
            if alert.status == "pending_review":
                if st.button("Acknowledge", key=f"ack_{alert.id}"):
                    now = dt.datetime.now(dt.timezone.utc)
                    alert.status = "acknowledged"
                    alert.assigned_reviewer_id = user.id
                    alert.acknowledged_at = now
                    alert.last_escalated_at = now
                    _log_audit(db, user.id, "alert_acknowledged", "alert", alert.id, {"reviewer_id": str(user.id)})
                    db.commit()
                    st.rerun()
            elif alert.status == "acknowledged":
                notes = st.text_area("Resolution notes (required)", key=f"notes_{alert.id}")
                if st.button("Resolve", key=f"resolve_{alert.id}"):
                    if not notes.strip():
                        st.error("Resolution notes are required for auditability.")
                    else:
                        cipher = get_cipher(db, user)
                        now = dt.datetime.now(dt.timezone.utc)
                        alert.status = "resolved"
                        alert.assigned_reviewer_id = user.id
                        alert.resolved_at = now
                        alert.resolution_notes_encrypted = cipher.encrypt(notes.strip())
                        _log_audit(db, user.id, "alert_resolved", "alert", alert.id, {"reviewer_id": str(user.id)})
                        db.commit()
                        st.rerun()


# ---------------------------------------------------------------------------
# System status / diagnostics page
#
# This is the "self-healing" feature: not autonomous code-modification
# (that's not something any responsible system should attempt on itself,
# especially not a mental-health app), but the standard production
# resilience pattern — automatic retries on transient failures (see
# llm_client.py's call_llm), graceful degradation instead of a hard crash
# (see run_page_safely below), and a visible diagnostics page so failures
# are transparent instead of silent. Real systems (Netflix's Hystrix,
# resilience4j, etc.) call this general approach "circuit breaking" /
# "graceful degradation" — this page makes that behavior visible.
# ---------------------------------------------------------------------------

def page_system_status(db):
    st.subheader("System status")
    st.caption("Live self-diagnostics: what's working, what recovered automatically, and what needs attention.")

    col1, col2 = st.columns(2)
    with col1:
        try:
            result = db.execute(__import__("sqlalchemy").text("SELECT 1"))
            result.fetchone()
            st.success("Database: reachable")
        except Exception as exc:
            st.error(f"Database: unreachable ({exc})")
            record_incident("db_healthcheck_failed", str(exc))
    with col2:
        has_key = bool(os.getenv("GROQ_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
        if has_key:
            st.success("LLM API key: configured")
        else:
            st.warning("LLM API key: not set — chat will use safe fallback replies")

    st.divider()
    st.write("**Recent incidents & automatic recoveries**")
    st.caption("Retried LLM calls, caught page errors, and health-check failures from this session. Resets when the app restarts.")
    incidents = recent_incidents()
    if not incidents:
        st.caption("No incidents recorded since this app process started. ✅")
    for inc in incidents:
        ts = inc["timestamp"].split("T")[1][:8]
        st.text(f"{ts}  [{inc['kind']}]  {inc['detail']}")


def run_page_safely(page_fn, *args):
    """Error boundary: a bug in one page must not take down the whole app
    for the user's whole session. Catches, logs, and offers a retry instead
    of Streamlit's default full-stack-trace crash screen."""
    try:
        page_fn(*args)
    except Exception as exc:
        logger.exception("Page crashed: %s", page_fn.__name__)
        record_incident("page_error", f"{page_fn.__name__}: {exc}")
        st.error(
            "Something went wrong loading this page. It's been logged — "
            "you can check **System status** in the sidebar for details, "
            "or try again below."
        )
        if st.button("Try again"):
            st.rerun()


def page_intro():
    """Branded intro: mandatory 10-second video, then a Start button.
    No skip — the Start button only appears once the video's runtime has
    elapsed (tracked server-side via streamlit_autorefresh, not by trusting
    the browser to tell us the video finished)."""
    import base64
    import time as _time
    from streamlit_autorefresh import st_autorefresh

    st.markdown(
        "<h1 style='text-align:center;color:#2E3A32;margin-top:8px;'>🌱 Sanjeevani</h1>",
        unsafe_allow_html=True,
    )

    video_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sanjeevani_intro.mp4")
    if "intro_started_at" not in st.session_state:
        st.session_state["intro_started_at"] = _time.time()

    elapsed = _time.time() - st.session_state["intro_started_at"]
    VIDEO_DURATION = 10.2  # slight buffer over the actual 10.0s clip

    if os.path.exists(video_path) and elapsed < VIDEO_DURATION:
        with open(video_path, "rb") as f:
            video_b64 = base64.b64encode(f.read()).decode()
        st.components.v1.html(
            f"""
            <div id="sanjeevani-intro-wrap" style="display:flex;justify-content:center;
                        align-items:center;width:100%;background:#F6F5F1;padding:8px 0;">
              <div style="width:100%;max-width:720px;position:relative;">
                <video id="sanjeevani-intro-video" autoplay playsinline
                       style="width:100%;aspect-ratio:16/9;height:auto;border-radius:16px;
                              display:block;object-fit:contain;background:#000;">
                  <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
                </video>
                <button id="unmute-btn" onclick="
                    var v=document.getElementById('sanjeevani-intro-video');
                    v.muted=false; v.play(); this.style.display='none';
                  " style="position:absolute;bottom:16px;right:16px;display:none;
                           background:#6E8B7A;color:white;border:none;border-radius:999px;
                           padding:10px 16px;font-size:14px;cursor:pointer;">
                  🔊 Tap for sound
                </button>
              </div>
            </div>
            <script>
              var v = document.getElementById('sanjeevani-intro-video');
              var btn = document.getElementById('unmute-btn');
              var p = v.play();
              if (p !== undefined) {{
                p.catch(function() {{
                  v.muted = true;
                  v.play();
                  btn.style.display = 'block';
                }});
              }}

              // Responsive iframe height: report actual rendered content
              // height to the parent Streamlit frame, on load, on video
              // metadata load, and on any resize/orientation change — so
              // phone/tablet/desktop/rotation all get a correctly sized
              // container instead of a hardcoded pixel height.
              function reportHeight() {{
                var h = document.getElementById('sanjeevani-intro-wrap').offsetHeight;
                window.parent.postMessage({{type: "streamlit:setFrameHeight", height: h + 24}}, "*");
              }}
              window.addEventListener('resize', reportHeight);
              v.addEventListener('loadedmetadata', reportHeight);
              window.addEventListener('load', reportHeight);
              setTimeout(reportHeight, 100);
              setTimeout(reportHeight, 500);
            </script>
            """,
            height=420,
        )
        # Ticks the page forward until the video's runtime has elapsed —
        # not a full browser reload, so session_state (and the video
        # playback itself) isn't disturbed.
        st_autorefresh(interval=800, limit=20, key="intro_wait")
        st.markdown(
            "<p style='text-align:center;color:#8A968D;'>Playing introduction…</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<p style='text-align:center;color:#5A6B5E;font-size:18px;'>"
            "A calm, private space to reflect.</p>",
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("START", use_container_width=True, type="primary"):
                st.session_state["onboarding_stage"] = "auth_choice"
                st.rerun()


def page_auth_choice():
    """Stage 2 of onboarding: choose Login or Register. Both lead into the
    existing, unmodified authentication screen (page_login_register)."""
    st.markdown(
        "<h1 style='text-align:center;color:#2E3A32;margin-top:24px;'>🌱 Sanjeevani</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;color:#5A6B5E;font-size:18px;margin-bottom:32px;'>"
        "How would you like to continue?</p>",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("LOGIN", use_container_width=True, type="primary"):
            st.session_state["onboarding_stage"] = "auth"
            st.rerun()
        st.write("")
        if st.button("REGISTER", use_container_width=True):
            st.session_state["onboarding_stage"] = "auth"
            st.rerun()


# ---------------------------------------------------------------------------
# Main app / navigation
# ---------------------------------------------------------------------------

def inject_pwa_support():
    """Adds a manifest link + theme-color meta + service worker registration
    into the real page <head> (Streamlit only renders markdown into <body>,
    so a plain st.markdown can't do this — this component's iframe is
    same-origin with the parent app, so it can reach window.parent.document)."""
    st.components.v1.html(
        """
        <script>
        (function() {
          var doc = window.parent.document;
          if (!doc.querySelector('link[rel="manifest"]')) {
            var link = doc.createElement('link');
            link.rel = 'manifest';
            link.href = 'app/static/manifest.json';
            doc.head.appendChild(link);
          }
          if (!doc.querySelector('meta[name="theme-color"]')) {
            var meta = doc.createElement('meta');
            meta.name = 'theme-color';
            meta.content = '#6E8B7A';
            doc.head.appendChild(meta);
          }
          if ('serviceWorker' in window.parent.navigator) {
            window.parent.navigator.serviceWorker.register('app/static/sw.js').catch(function(){});
          }
        })();
        </script>
        """,
        height=0,
    )


def handle_email_verification_link():
    """If the app was opened via a verification-email link (?verify=<token>),
    check the token and mark the account verified. Runs before anything
    else so it works whether or not the person is currently logged in."""
    token = st.query_params.get("verify")
    if not token:
        return
    db = get_db()
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        row = db.query(models.VerificationToken).filter(
            models.VerificationToken.token_hash == token_hash
        ).first()
        now = dt.datetime.now(dt.timezone.utc)
        if row and row.used_at is None and row.expires_at > now:
            user = db.query(models.User).filter(models.User.id == row.user_id).first()
            if user:
                user.email_verified_at = now
                row.used_at = now
                db.commit()
                st.success("✅ Email verified! You can now sign in.")
        elif row and row.used_at is not None:
            st.info("This verification link was already used.")
        else:
            st.warning("This verification link is invalid or has expired.")
    finally:
        db.close()
    st.query_params.clear()


def main():
    render_banner()
    inject_pwa_support()
    handle_email_verification_link()
    restore_session_from_cookie()

    if "user_id" not in st.session_state:
        st.session_state.setdefault("onboarding_stage", "intro")
        if st.session_state["onboarding_stage"] == "intro":
            run_page_safely(page_intro)
        elif st.session_state["onboarding_stage"] == "auth_choice":
            run_page_safely(page_auth_choice)
        else:
            run_page_safely(page_login_register)
        return

    db = get_db()
    try:
        user = db.query(models.User).filter(
            models.User.id == st.session_state["user_id"], models.User.deleted_at.is_(None)
        ).first()
        if not user:
            st.session_state.clear()
            st.rerun()
            return

        if user.email_verified_at is None:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.warning("Your email isn't verified yet.")
            with col2:
                if st.button("Resend link"):
                    verify_raw = secrets.token_urlsafe(48)
                    db.add(models.VerificationToken(
                        user_id=user.id,
                        token_hash=hashlib.sha256(verify_raw.encode()).hexdigest(),
                        expires_at=dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=24),
                    ))
                    db.commit()
                    app_url = os.getenv("SANJEEVANI_APP_URL", "https://sanjeevani-w3yji9hmnzsljkkqtkrxpe.streamlit.app")
                    sent = email_service.send_verification_email(user.email, f"{app_url}/?verify={verify_raw}")
                    st.success("Sent!" if sent else "Email delivery isn't configured on this deployment.")

        with st.sidebar:
            st.write(f"Signed in as **{user.display_name or user.email}**")
            current_streak, longest_streak = compute_mood_streak(db, user)
            if current_streak > 0:
                badge = streak_badge_for(current_streak)
                st.metric("🔥 Mood streak", f"{current_streak} day{'s' if current_streak != 1 else ''}")
                if badge:
                    remaining = [m for m in STREAK_MILESTONES if m > current_streak]
                    next_note = f" · next badge at {remaining[0]} days" if remaining else " · all badges earned! 🎉"
                    st.caption(f"Best: {longest_streak} days · {badge}{next_note}")
                else:
                    st.caption(f"Best: {longest_streak} days · next badge at {STREAK_MILESTONES[0]} days")
            else:
                st.caption("Log your mood today to start a streak 🔥")
            pages = ["Chat", "Mood", "Journal", "Weekly summary", "Privacy & data", "Emergency contacts"]
            if user.role in ("reviewer", "super_admin"):
                pages.append("Reviewer dashboard")
            pages.append("System status")
            choice = st.radio("Navigate", pages, label_visibility="collapsed")
            st.divider()
            if st.button("Sign out"):
                clear_session_cookie()
                st.session_state.clear()
                st.rerun()

        if choice == "Chat":
            run_page_safely(page_chat, db, user)
        elif choice == "Mood":
            run_page_safely(page_mood, db, user)
        elif choice == "Journal":
            run_page_safely(page_journal, db, user)
        elif choice == "Weekly summary":
            run_page_safely(page_summary, db, user)
        elif choice == "Privacy & data":
            run_page_safely(page_privacy, db, user)
        elif choice == "Emergency contacts":
            run_page_safely(page_contacts, db, user)
        elif choice == "Reviewer dashboard":
            run_page_safely(page_reviewer, db, user)
        elif choice == "System status":
            run_page_safely(page_system_status, db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
