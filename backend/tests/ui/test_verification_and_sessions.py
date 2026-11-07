import datetime as dt
import hashlib
import secrets

from .helpers import PW, button, db, fake_cookies, fresh, go, login, logged_in, new_email, register, user_row, verify_email_in_db


def _token_for(email, days=14, revoked=False):
    from app import models
    raw = secrets.token_urlsafe(40)
    s = db()
    try:
        s.add(models.RefreshToken(
            user_id=user_row(email).id, token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=days),
            revoked_at=dt.datetime.now(dt.timezone.utc) if revoked else None,
        ))
        s.commit()
    finally:
        s.close()
    return raw


def test_unverified_user_sees_gate_when_verification_required(monkeypatch):
    monkeypatch.setenv("SANJEEVANI_REQUIRE_EMAIL_VERIFICATION", "true")
    email = new_email("gate")
    register(email)
    at = login(email)
    assert logged_in(at)
    assert any("verify your email" in t.value.lower() for t in at.title)
    assert [r for r in at.radio if r.key == "nav_choice"] == []  # no app navigation
    assert "14416" in " ".join(m.value for m in at.markdown)  # helplines stay visible


def test_verified_user_passes_the_gate(monkeypatch):
    monkeypatch.setenv("SANJEEVANI_REQUIRE_EMAIL_VERIFICATION", "true")
    email = new_email("ok")
    register(email)
    verify_email_in_db(email)
    at = login(email)
    assert at.radio(key="nav_choice") is not None


def test_unverified_user_can_use_app_when_not_required(monkeypatch):
    monkeypatch.setenv("SANJEEVANI_REQUIRE_EMAIL_VERIFICATION", "false")
    email = new_email("free")
    register(email)
    at = login(email)
    assert at.radio(key="nav_choice") is not None
    assert any("isn't verified" in w.value for w in at.warning)


def test_remember_me_token_is_created_on_login():
    from app import models
    email = new_email("rem")
    register(email)
    login(email, remember=True)
    s = db()
    try:
        assert s.query(models.RefreshToken).filter(models.RefreshToken.user_id == user_row(email).id).count() == 1
    finally:
        s.close()
    email2 = new_email("norem")
    register(email2)
    login(email2, remember=False)
    s = db()
    try:
        assert s.query(models.RefreshToken).filter(models.RefreshToken.user_id == user_row(email2).id).count() == 0
    finally:
        s.close()


def test_valid_cookie_restores_session(monkeypatch):
    email = new_email("cookie")
    register(email)
    raw = _token_for(email)
    fake_cookies(monkeypatch, {"sj_remember": raw})
    at = fresh()
    assert logged_in(at) and not at.exception


def test_expired_revoked_or_unknown_cookie_does_not_restore(monkeypatch):
    email = new_email("cookie2")
    register(email)
    for raw in (_token_for(email, days=-1), _token_for(email, revoked=True), "x" * 50):
        fake_cookies(monkeypatch, {"sj_remember": raw})
        assert not logged_in(fresh())


def test_cookie_of_deleted_user_does_not_restore(monkeypatch):
    from app import models
    email = new_email("cookie3")
    register(email)
    raw = _token_for(email)
    s = db()
    try:
        u = s.query(models.User).filter(models.User.email == email).first()
        u.deleted_at = dt.datetime.now(dt.timezone.utc)
        s.commit()
    finally:
        s.close()
    fake_cookies(monkeypatch, {"sj_remember": raw})
    assert not logged_in(fresh())


def test_sign_out_revokes_the_token(monkeypatch):
    from app import models
    email = new_email("so")
    register(email)
    raw = _token_for(email)
    fake_cookies(monkeypatch, {"sj_remember": raw})
    at = fresh()
    assert logged_in(at)
    button(at, "Sign out").click().run()
    s = db()
    try:
        row = s.query(models.RefreshToken).filter(
            models.RefreshToken.token_hash == hashlib.sha256(raw.encode()).hexdigest()).first()
        assert row.revoked_at is not None
    finally:
        s.close()
    assert not logged_in(fresh())


def test_password_change_revokes_all_remember_tokens(monkeypatch):
    from app import models
    email = new_email("pwrev")
    register(email)
    raw = _token_for(email)
    at = login(email)
    go(at, "👤 Profile")
    pw = [t for t in at.text_input if t.label in ("Current password", "New password", "Confirm new password")][:3]
    pw[0].set_value(PW); pw[1].set_value("NewStr0ng-Passw0rd!y"); pw[2].set_value("NewStr0ng-Passw0rd!y")
    button(at, "Update password").click().run()
    s = db()
    try:
        active = s.query(models.RefreshToken).filter(
            models.RefreshToken.user_id == user_row(email).id, models.RefreshToken.revoked_at.is_(None)).count()
        assert active == 0
    finally:
        s.close()
    fake_cookies(monkeypatch, {"sj_remember": raw})
    assert not logged_in(fresh())
