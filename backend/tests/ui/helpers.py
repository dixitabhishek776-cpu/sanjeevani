import os
import uuid
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

APP = os.path.join(os.path.dirname(__file__), "..", "..", "..", "streamlit_app", "app.py")
PW = "Str0ng-Passw0rd!x"


def new_email(prefix="ui"):
    return f"{prefix}{uuid.uuid4().hex[:8]}@example.com"


def fresh():
    return AppTest.from_file(APP, default_timeout=120).run()


def button(at, label):
    matches = [b for b in at.button if b.label == label]
    assert matches, f"no button {label!r}; have {[b.label for b in at.button]}"
    return matches[0]


def open_auth(at=None):
    at = at or fresh()
    at.button[0].click().run()  # intro -> sign in / create account
    return at


def register(email, pw=PW, name="Test User", age=True, terms=True, at=None):
    at = open_auth(at)
    at.text_input(key="reg_name").set_value(name)
    at.text_input(key="reg_email").set_value(email)
    at.text_input(key="reg_password").set_value(pw)
    at.checkbox(key="reg_age_ok").set_value(age)
    at.checkbox(key="reg_terms_ok").set_value(terms)
    button(at, "Create account").click().run()
    return at


def login(email, pw=PW, at=None, remember=True):
    at = open_auth(at)
    at.text_input(key="login_email").set_value(email)
    at.text_input(key="login_password").set_value(pw)
    at.checkbox(key="login_remember").set_value(remember)
    button(at, "Sign in").click().run()
    return at


def go(at, page):
    at.radio(key="nav_choice").set_value(page).run()
    return at


def logged_in(at):
    return "user_id" in at.session_state and at.session_state["user_id"] is not None


def db():
    from app.database import SessionLocal
    return SessionLocal()


def user_row(email):
    from app import models
    s = db()
    try:
        u = s.query(models.User).filter(models.User.email == email).first()
        if u is not None:
            s.expunge(u)
        return u
    finally:
        s.close()


def verify_email_in_db(email):
    import datetime as dt
    from app import models
    s = db()
    try:
        u = s.query(models.User).filter(models.User.email == email).first()
        u.email_verified_at = dt.datetime.now(dt.timezone.utc)
        s.commit()
    finally:
        s.close()


def fake_cookies(monkeypatch, cookies):
    import streamlit as st
    monkeypatch.setattr(st, "context", SimpleNamespace(cookies=cookies), raising=False)
