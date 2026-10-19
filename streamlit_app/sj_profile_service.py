"""
sj_profile_service.py - database layer for the Profile page.

No new tables or columns: everything extra (phone, bio, goals, photo, time zone, reminder time,
full name) lives inside UserPreferences.notification_settings (JSONB), the same place the app
already keeps companion_name / chat_language. Phone and bio are encrypted with the user's own key.
"""
from __future__ import annotations
import base64, io, json
from datetime import datetime, time

_DEFAULT_GOALS: list = []


def make_avatar_data_uri(file_bytes: bytes, px: int = 256) -> str:
    from PIL import Image, ImageOps
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(file_bytes))).convert("RGB")
    img = ImageOps.fit(img, (px, px), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=84, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


class ProfileService:
    pass


class SQLProfileService(ProfileService):
    def __init__(self, db, user, h: dict):
        self.db, self.user, self.h = db, user, h
        self.m = h["models"]

    # ---- internals
    def _prefs(self):
        m = self.m
        p = self.db.query(m.UserPreferences).filter(m.UserPreferences.user_id == self.user.id).first()
        if not p:
            p = m.UserPreferences(user_id=self.user.id)
            self.db.add(p); self.db.commit(); self.db.refresh(p)
        return p

    def _settings(self) -> dict:
        return dict(self._prefs().notification_settings or {})

    def _update_settings(self, upd: dict) -> None:
        p = self._prefs()
        s = dict(p.notification_settings or {})
        s.update(upd)
        p.notification_settings = s          # new dict object so the JSONB change is detected

    def _enc(self, text: str):
        if not text:
            return ""
        cipher = self.h["get_cipher"](self.db, self.user)
        return base64.b64encode(cipher.encrypt(text)).decode()

    def _dec(self, token) -> str:
        if not token:
            return ""
        try:
            cipher = self.h["get_cipher"](self.db, self.user)
            return self.h["safe_decrypt"](cipher, base64.b64decode(token))
        except Exception:
            return ""

    @staticmethod
    def _naive(d):
        return d.replace(tzinfo=None) if d is not None and d.tzinfo else d

    # ---- reads
    def get_profile(self, user_id) -> dict:
        u, s, m = self.user, self._settings(), self.m
        rt = s.get("reminder_time", "21:00")
        try:
            hh, mm = [int(x) for x in rt.split(":")[:2]]
            rtime = time(hh, mm)
        except Exception:
            rtime = time(21, 0)
        row = (self.db.query(m.AuditLog)
               .filter(m.AuditLog.actor_id == u.id, m.AuditLog.action == "password_changed")
               .order_by(m.AuditLog.created_at.desc()).first())
        return {
            "full_name": s.get("full_name") or u.display_name or u.email.split("@")[0],
            "display_name": u.display_name or "",
            "email": u.email,
            "email_verified": u.email_verified_at is not None,
            "phone": self._dec(s.get("phone_enc")),
            "created_at": self._naive(u.created_at) or datetime.utcnow(),
            "avatar_data_uri": s.get("avatar_data_uri"),
            "companion_name": s.get("companion_name", "Mitra"),
            "language": s.get("chat_language", "English"),
            "timezone": s.get("timezone", "Asia/Kolkata"),
            "goals": list(s.get("goals", _DEFAULT_GOALS)),
            "bio": self._dec(s.get("bio_enc")),
            "reminder_enabled": bool(s.get("daily_reminder_enabled", False)),
            "reminder_time": rtime,
            "weekly_email": False,
            "two_factor_enabled": bool(s.get("totp_enabled", False)),
            "password_changed_at": self._naive(row.created_at) if row else None,
        }

    def get_stats(self, user_id) -> dict:
        m, db, u = self.m, self.db, self.user
        cur, best = self.h["mood_streak"](db, u)
        return {
            "streak": cur, "best_streak": best,
            "checkins": db.query(m.MoodEntry).filter(m.MoodEntry.user_id == u.id).count(),
            "entries": db.query(m.Journal).filter(m.Journal.user_id == u.id).count(),
            "contacts": db.query(m.EmergencyContact).filter(m.EmergencyContact.user_id == u.id,
                                                            m.EmergencyContact.active.is_(True)).count(),
        }

    def list_sessions(self, user_id) -> list:
        return []        # the app does not track devices, so the card stays hidden

    def revoke_session(self, user_id, session_id) -> None:
        pass

    # ---- writes (whitelisted keys only: never email / password / verified flag)
    def save_profile(self, user_id, changes: dict) -> None:
        upd = {}
        if "display_name" in changes:
            self.user.display_name = (changes["display_name"] or "").strip() or None
        if "full_name" in changes:      upd["full_name"] = changes["full_name"]
        if "phone" in changes:          upd["phone_enc"] = self._enc(changes["phone"])
        if "bio" in changes:            upd["bio_enc"] = self._enc(changes["bio"])
        if "companion_name" in changes: upd["companion_name"] = changes["companion_name"]
        if "language" in changes:
            upd["chat_language"] = changes["language"]
            try:
                import streamlit as st
                st.session_state["chat_language"] = changes["language"]
            except Exception:
                pass
        if "timezone" in changes:       upd["timezone"] = changes["timezone"]
        if "goals" in changes:          upd["goals"] = list(changes["goals"])
        if "reminder_enabled" in changes: upd["daily_reminder_enabled"] = bool(changes["reminder_enabled"])
        if "reminder_time" in changes and changes["reminder_time"] is not None:
            upd["reminder_time"] = changes["reminder_time"].strftime("%H:%M")
        if "avatar_data_uri" in changes: upd["avatar_data_uri"] = changes["avatar_data_uri"]
        if upd:
            self._update_settings(upd)
        self.db.commit()

    def change_password(self, user_id, current: str, new: str):
        h, u = self.h, self.user
        if not h["verify_password"](current, u.password_hash):
            return "Current password is incorrect."
        if len(new) < 8:
            return "New password must be at least 8 characters."
        u.password_hash = h["hash_password"](new)
        h["log_audit"](self.db, u.id, "password_changed", "user", u.id, {})
        self.db.commit()
        return None

    def export_data(self, user_id) -> str:
        m, db, u = self.m, self.db, self.user
        cipher = self.h["get_cipher"](db, u)
        moods = db.query(m.MoodEntry).filter(m.MoodEntry.user_id == u.id).all()
        journals = db.query(m.Journal).filter(m.Journal.user_id == u.id).all()
        p = self.get_profile(user_id)
        return json.dumps({
            "user": {"id": str(u.id), "email": u.email, "display_name": u.display_name},
            "profile": {k: (v.isoformat() if hasattr(v, "isoformat") else v)
                        for k, v in p.items() if k not in ("avatar_data_uri", "email")},
            "mood_entries": [{"mood_score": x.mood_score, "tags": x.tags, "logged_at": x.logged_at.isoformat()} for x in moods],
            "journals": [{"content": self.h["safe_decrypt"](cipher, j.content_encrypted),
                          "created_at": j.created_at.isoformat()} for j in journals],
        }, indent=2, default=str)

    def delete_account(self, user_id, password: str):
        h, u, m, db = self.h, self.user, self.m, self.db
        if not h["verify_password"](password, u.password_hash):
            return "Incorrect password."
        import datetime as dt
        now = dt.datetime.now(dt.timezone.utc)
        u.deleted_at = now
        key_row = db.query(m.UserEncryptionKey).filter(m.UserEncryptionKey.user_id == u.id).first()
        if key_row:
            key_row.revoked_at = now
        h["log_audit"](db, u.id, "account_deletion_requested", "user", u.id, {"confirmation": True})
        db.commit()
        return None
