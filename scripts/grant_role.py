#!/usr/bin/env python3
"""Grant or revoke the reviewer / super_admin role for a user, from the shell.

Reviewers see the "Reviewer dashboard" and the safety alert queue, so this is
deliberately not available inside the app.

  DATABASE_URL=... python3 scripts/grant_role.py someone@example.com reviewer
  DATABASE_URL=... python3 scripts/grant_role.py someone@example.com user      # revoke
Roles: user | reviewer | super_admin
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

ROLES = ("user", "reviewer", "super_admin")


def main(argv) -> int:
    if len(argv) != 3 or argv[2] not in ROLES:
        print(__doc__)
        return 2
    email, role = argv[1].strip().lower(), argv[2]
    from app.database import SessionLocal
    from app import models

    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == email, models.User.deleted_at.is_(None)).first()
        if not user:
            print(f"No active user with email {email}", file=sys.stderr)
            return 1
        before = user.role
        user.role = role
        db.add(models.AuditLog(actor_id=None, action="role_changed_by_operator", target_type="user",
                               target_id=user.id, audit_metadata={"from": before, "to": role}))
        db.commit()
        print(f"{email}: {before} -> {role}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
