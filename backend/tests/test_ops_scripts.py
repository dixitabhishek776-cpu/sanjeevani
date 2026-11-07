import os
import subprocess
import sys
import uuid

import pytest
from cryptography.fernet import Fernet

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _run(script, env_extra, *args):
    env = dict(os.environ, **env_extra)
    env["PYTHONPATH"] = os.path.join(ROOT, "backend")
    return subprocess.run([sys.executable, os.path.join(ROOT, "scripts", script), *args],
                          capture_output=True, text=True, env=env, cwd=ROOT)


@pytest.fixture()
def user_with_key():
    from app.database import SessionLocal
    from app import models
    old = Fernet.generate_key().decode()
    db = SessionLocal()
    uid = uuid.uuid4()
    try:
        db.add(models.User(id=uid, email=f"rot{uid.hex[:8]}@example.com", password_hash="x"))
        db.flush()
        dek = b"0" * 32
        db.add(models.UserEncryptionKey(user_id=uid, wrapped_dek=Fernet(old.encode()).encrypt(dek)))
        db.commit()
    finally:
        db.close()
    yield uid, old, dek
    db = SessionLocal()
    try:
        db.query(models.UserEncryptionKey).filter_by(user_id=uid).delete()
        db.query(models.User).filter_by(id=uid).delete()
        db.commit()
    finally:
        db.close()


def _wrapped(uid):
    from app.database import SessionLocal
    from app import models
    db = SessionLocal()
    try:
        return bytes(db.query(models.UserEncryptionKey).filter_by(user_id=uid).one().wrapped_dek)
    finally:
        db.close()


def test_rotate_master_key_dry_run_changes_nothing(user_with_key):
    uid, old, dek = user_with_key
    new = Fernet.generate_key().decode()
    before = _wrapped(uid)
    r = _run("rotate_master_key.py", {"OLD_MASTER_KEY": old, "NEW_MASTER_KEY": new}, "--skip-undecryptable")
    assert r.returncode == 0, r.stderr
    assert "Dry run" in r.stdout
    assert _wrapped(uid) == before


def test_rotate_master_key_apply_rewraps_and_data_key_still_opens(user_with_key):
    uid, old, dek = user_with_key
    new = Fernet.generate_key().decode()
    r = _run("rotate_master_key.py", {"OLD_MASTER_KEY": old, "NEW_MASTER_KEY": new}, "--apply", "--skip-undecryptable")
    assert r.returncode == 0, r.stderr
    wrapped = _wrapped(uid)
    assert Fernet(new.encode()).decrypt(wrapped) == dek
    with pytest.raises(Exception):
        Fernet(old.encode()).decrypt(wrapped)
    # second run is a no-op
    r2 = _run("rotate_master_key.py", {"OLD_MASTER_KEY": old, "NEW_MASTER_KEY": new}, "--apply", "--skip-undecryptable")
    assert r2.returncode == 0 and "already on new key" in r2.stdout


def test_rotate_rejects_wrong_old_key(user_with_key):
    uid, old, dek = user_with_key
    r = _run("rotate_master_key.py", {"OLD_MASTER_KEY": Fernet.generate_key().decode(),
                                      "NEW_MASTER_KEY": Fernet.generate_key().decode()}, "--apply")
    assert r.returncode == 1
    assert Fernet(old.encode()).decrypt(_wrapped(uid)) == dek


def test_grant_role_changes_role_and_audits(user_with_key):
    from app.database import SessionLocal
    from app import models
    uid, _, _ = user_with_key
    db = SessionLocal()
    try:
        email = db.query(models.User).filter_by(id=uid).one().email
    finally:
        db.close()
    assert _run("grant_role.py", {}, email, "reviewer").returncode == 0
    db = SessionLocal()
    try:
        assert db.query(models.User).filter_by(id=uid).one().role == "reviewer"
        assert db.query(models.AuditLog).filter_by(target_id=uid, action="role_changed_by_operator").count() == 1
    finally:
        db.close()
    assert _run("grant_role.py", {}, email, "superuser").returncode == 2
    assert _run("grant_role.py", {}, "nobody@example.com", "reviewer").returncode == 1
