import pytest

from .helpers import PW, button, fresh, login, logged_in, new_email, register, user_row, open_auth


def test_intro_loads_without_errors():
    at = fresh()
    assert not at.exception


def test_register_requires_age_confirmation():
    email = new_email()
    at = register(email, age=False)
    assert any("18" in e.value for e in at.error)
    assert user_row(email) is None


def test_register_requires_terms():
    email = new_email()
    at = register(email, terms=False)
    assert any("Terms" in e.value for e in at.error)
    assert user_row(email) is None


@pytest.mark.parametrize("pw,fragment", [
    ("short", "at least 12"),
    ("password1234", "too common"),
    ("aaaaaaaaaaaa", "too simple"),
    ("abcdefghijkl", "too"),
])
def test_register_rejects_weak_passwords(pw, fragment):
    email = new_email()
    at = register(email, pw=pw)
    assert any(fragment in e.value for e in at.error), [e.value for e in at.error]
    assert user_row(email) is None


def test_register_rejects_password_containing_email_name():
    email = "riyasharma99@example.com"
    at = register(email, pw="riyasharma99-Xz!")
    assert any("email name" in e.value for e in at.error)


def test_register_rejects_bad_email():
    at = register("not-an-email")
    assert any("valid email" in e.value for e in at.error)


def test_register_then_duplicate_email_is_rejected_case_insensitively():
    email = new_email()
    at = register(email)
    assert not at.exception and user_row(email) is not None
    at2 = register(email.upper())
    assert any("already registered" in e.value for e in at2.error)


def test_consents_recorded_on_register():
    from app import models
    from .helpers import db
    email = new_email()
    register(email)
    s = db()
    try:
        u = s.query(models.User).filter(models.User.email == email).first()
        types = {c.consent_type for c in s.query(models.ConsentRecord).filter(models.ConsentRecord.user_id == u.id)}
    finally:
        s.close()
    assert {"terms", "age_18_plus"} <= types


def test_login_success_and_wrong_password():
    email = new_email()
    register(email)
    bad = login(email, pw="wrong-password-123")
    assert not logged_in(bad) and any("Incorrect" in e.value for e in bad.error)
    good = login(email)
    assert logged_in(good) and not good.exception


def test_account_locks_after_repeated_failures():
    email = new_email()
    register(email)
    at = open_auth()
    for _ in range(5):
        at.text_input(key="login_email").set_value(email)
        at.text_input(key="login_password").set_value("wrong-password-123")
        button(at, "Sign in").click().run()
    at.text_input(key="login_email").set_value(email)
    at.text_input(key="login_password").set_value(PW)
    button(at, "Sign in").click().run()
    assert not logged_in(at)
    assert any("locked" in e.value.lower() or "too many" in e.value.lower() for e in at.error)


def test_xss_in_display_name_is_not_rendered_as_html():
    email = new_email()
    register(email, name="<script>alert(1)</script>")
    at = login(email)
    assert logged_in(at)
    html_blobs = [m.value for m in at.markdown if "<script>alert(1)</script>" in m.value and m.proto.allow_html]
    assert html_blobs == []
