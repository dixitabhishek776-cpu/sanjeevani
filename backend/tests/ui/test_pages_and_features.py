import pyotp

from .helpers import PW, button, fresh, go, login, logged_in, new_email, register, db, user_row, verify_email_in_db


def _signed_in(prefix="pg"):
    email = new_email(prefix)
    register(email)
    return email, login(email)


def test_every_page_renders_without_exceptions():
    _, at = _signed_in()
    for page in ["💬 Chat", "😊 Mood", "📔 Journal", "📊 Insights", "💜 Contacts", "👤 Profile", "⚙️ Settings"]:
        go(at, page)
        assert not at.exception, f"{page}: {[e.value[:200] for e in at.exception]}"


def test_old_sidebar_account_popover_is_gone():
    _, at = _signed_in()
    labels = [t.label for t in at.text_input]
    assert "Display name" not in labels  # only the Profile page edits names now


def test_mood_and_journal_are_saved():
    from app import models
    email, at = _signed_in()
    go(at, "😊 Mood")
    at.slider[0].set_value(4)
    button(at, "Log mood").click().run()
    go(at, "📔 Journal")
    at.text_area[0].set_value("Anxious about results.")
    button(at, "Save entry").click().run()
    s = db()
    try:
        uid = user_row(email).id
        assert s.query(models.MoodEntry).filter(models.MoodEntry.user_id == uid).count() == 1
        assert s.query(models.Journal).filter(models.Journal.user_id == uid).count() == 1
    finally:
        s.close()


def test_contact_added_and_confirmation_is_visible_after_rerun():
    from app import models
    email, at = _signed_in()
    go(at, "💜 Contacts")
    at.text_input[0].set_value("Mom")
    at.text_input[1].set_value("+919876543210")
    at.text_input[2].set_value("mom@example.com")
    at.text_input[3].set_value("Mother")
    for c in at.checkbox:
        c.check()
    button(at, "Add contact").click().run()
    assert any("Contact added" in s.value for s in at.success)
    s = db()
    try:
        assert s.query(models.EmergencyContact).filter(models.EmergencyContact.user_id == user_row(email).id).count() == 1
    finally:
        s.close()


def test_daily_reminder_toggle_persists():
    from app import models
    email, at = _signed_in()
    go(at, "⚙️ Settings")
    [c for c in at.checkbox if c.label.startswith("Send me a daily")][0].check()
    button(at, "Save preferences").click().run()
    s = db()
    try:
        prefs = s.query(models.UserPreferences).filter(models.UserPreferences.user_id == user_row(email).id).first()
        assert prefs.notification_settings.get("daily_reminder_enabled") is True
    finally:
        s.close()


def test_two_factor_secret_is_encrypted_and_login_requires_code():
    from app import models
    email, at = _signed_in()
    go(at, "⚙️ Settings")
    button(at, "Set up 2FA").click().run()
    secret = at.session_state["pending_totp_secret"]
    [t for t in at.text_input if t.label.startswith("Enter the 6-digit")][0].set_value(pyotp.TOTP(secret).now())
    button(at, "Confirm & enable 2FA").click().run()
    s = db()
    try:
        prefs = s.query(models.UserPreferences).filter(models.UserPreferences.user_id == user_row(email).id).first()
        st_ = prefs.notification_settings
        assert st_.get("totp_enabled") is True
        assert "totp_secret" not in st_ and secret not in str(st_)
        assert st_.get("totp_secret_enc")
    finally:
        s.close()
    at2 = login(email)
    assert not logged_in(at2)
    code = [t for t in at2.text_input if t.label == "Code"][0]
    code.set_value("000000")
    button(at2, "Verify").click().run()
    assert not logged_in(at2) and any("Incorrect code" in e.value for e in at2.error)
    [t for t in at2.text_input if t.label == "Code"][0].set_value(pyotp.TOTP(secret).now())
    button(at2, "Verify").click().run()
    assert logged_in(at2)


def test_legacy_plaintext_totp_secret_is_migrated_on_login():
    from sqlalchemy import text
    email = new_email("leg")
    register(email)
    secret = pyotp.random_base32()
    s = db()
    try:
        uid = user_row(email).id
        s.execute(text("update user_preferences set notification_settings = cast(:j as jsonb) where user_id=:u"),
                  {"j": '{"totp_enabled": true, "totp_secret": "%s"}' % secret, "u": str(uid)})
        s.commit()
    finally:
        s.close()
    at = login(email)
    [t for t in at.text_input if t.label == "Code"][0].set_value(pyotp.TOTP(secret).now())
    button(at, "Verify").click().run()
    assert logged_in(at)
    s = db()
    try:
        row = s.execute(text("select notification_settings::text from user_preferences where user_id=:u"), {"u": str(uid)}).scalar()
        assert secret not in row and "totp_secret_enc" in row
    finally:
        s.close()


def test_password_change_enforces_policy_and_works():
    email, at = _signed_in("pw")
    go(at, "👤 Profile")
    def attempt(new):
        pw = [t for t in at.text_input if t.label in ("Current password", "New password", "Confirm new password")][:3]
        pw[0].set_value(PW); pw[1].set_value(new); pw[2].set_value(new)
        button(at, "Update password").click().run()
    attempt("password1234")
    assert any("too common" in e.value for e in at.error)
    attempt("NewStr0ng-Passw0rd!y")
    assert any("Password updated" in s.value for s in at.success)
    assert logged_in(login(email, pw="NewStr0ng-Passw0rd!y"))


def test_delete_account_anonymises_and_frees_the_email():
    from app import models
    email, at = _signed_in("del")
    uid = user_row(email).id
    go(at, "👤 Profile")
    [t for t in at.text_input if "Confirm your password" in t.label][0].set_value(PW)
    [c for c in at.checkbox if "cannot be undone" in c.label][0].check()
    button(at, "Delete my account").click().run()
    assert not at.exception
    s = db()
    try:
        u = s.query(models.User).filter(models.User.id == uid).first()
        assert u.deleted_at is not None
        assert u.email != email and u.email.endswith("@deleted.invalid")
        assert u.display_name is None
        assert s.query(models.EmergencyContact).filter(models.EmergencyContact.user_id == uid).count() == 0
        key = s.query(models.UserEncryptionKey).filter(models.UserEncryptionKey.user_id == uid).first()
        assert key is None or key.revoked_at is not None
    finally:
        s.close()
    assert not logged_in(login(email))
    again = register(email)  # the address can be used again
    assert not again.exception and user_row(email) is not None


def test_chat_during_ai_outage_shows_helplines_and_creates_no_alert(monkeypatch):
    from app import models
    from app.agents import conversation_agent as ca, safety_agent as sa

    def boom(*a, **k):
        raise RuntimeError("provider down")

    monkeypatch.setattr(sa, "call_llm_json", boom)
    monkeypatch.setattr(ca, "call_llm", boom)
    email, at = _signed_in("chat")
    go(at, "💬 Chat")
    at.chat_input[0].set_value("hi, I had a stressful day").run()
    assert not at.exception
    s = db()
    try:
        uid = user_row(email).id
        assert s.query(models.SafetyAssessment).filter(models.SafetyAssessment.user_id == uid).count() >= 1
        alerts = s.query(models.Alert).join(
            models.SafetyAssessment, models.Alert.safety_assessment_id == models.SafetyAssessment.id
        ).filter(models.SafetyAssessment.user_id == uid).count()
        assert alerts == 0
    finally:
        s.close()
    text = " ".join(m.value for m in at.markdown)
    assert "14416" in text or "112" in text


def test_crisis_message_creates_alert_even_when_ai_is_down(monkeypatch):
    from app import models
    from app.agents import conversation_agent as ca, safety_agent as sa

    def boom(*a, **k):
        raise RuntimeError("provider down")

    monkeypatch.setattr(sa, "call_llm_json", boom)
    monkeypatch.setattr(ca, "call_llm", boom)
    email, at = _signed_in("crisis")
    go(at, "💬 Chat")
    at.chat_input[0].set_value("I want to kill myself").run()
    s = db()
    try:
        uid = user_row(email).id
        n = s.query(models.Alert).join(
            models.SafetyAssessment, models.Alert.safety_assessment_id == models.SafetyAssessment.id
        ).filter(models.SafetyAssessment.user_id == uid, models.SafetyAssessment.concern_level == "immediate").count()
        assert n == 1
    finally:
        s.close()
    assert "14416" in " ".join(m.value for m in at.markdown) + " ".join(w.value for w in at.warning)
