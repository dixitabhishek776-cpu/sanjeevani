#!/usr/bin/env python3
"""Rotate SANJEEVANI_MASTER_KEY (local_dev provider) without losing user data.

Every user's data key (DEK) is stored wrapped by the master key. Rotating the
master key therefore only means re-wrapping those small DEKs; journal, chat and
mood ciphertext is untouched. If you simply replace SANJEEVANI_MASTER_KEY in
your secrets without running this, existing entries become unreadable.

Steps:
  1. Generate a new key:
       python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  2. Dry run (changes nothing, only checks):
       DATABASE_URL=... OLD_MASTER_KEY=<current key> NEW_MASTER_KEY=<new key> \\
         python3 scripts/rotate_master_key.py
  3. Apply:
       ... python3 scripts/rotate_master_key.py --apply
  4. Put the NEW key into Streamlit secrets as SANJEEVANI_MASTER_KEY and reboot.

Run it from the repository root. The run is one database transaction: either
every key is re-wrapped or none is.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from cryptography.fernet import Fernet, InvalidToken, MultiFernet  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the re-wrapped keys (default is a dry run)")
    ap.add_argument("--skip-undecryptable", action="store_true",
                    help="continue even if some keys cannot be unwrapped with the old key (they stay as they are)")
    args = ap.parse_args()

    old_key, new_key = os.getenv("OLD_MASTER_KEY"), os.getenv("NEW_MASTER_KEY")
    if not old_key or not new_key:
        print("Set OLD_MASTER_KEY and NEW_MASTER_KEY.", file=sys.stderr)
        return 2
    if old_key == new_key:
        print("OLD_MASTER_KEY and NEW_MASTER_KEY are the same; nothing to do.", file=sys.stderr)
        return 2
    try:
        old_f, new_f = Fernet(old_key.encode()), Fernet(new_key.encode())
    except Exception as exc:
        print(f"One of the keys is not a valid Fernet key: {exc}", file=sys.stderr)
        return 2
    rotator = MultiFernet([new_f, old_f])

    from app.database import SessionLocal
    from app import models

    db = SessionLocal()
    try:
        rows = db.query(models.UserEncryptionKey).filter(models.UserEncryptionKey.revoked_at.is_(None)).all()
        ok, already_new, bad = 0, 0, []
        for row in rows:
            token = bytes(row.wrapped_dek)
            try:
                old_f.decrypt(token)
            except InvalidToken:
                try:
                    new_f.decrypt(token)
                    already_new += 1
                except InvalidToken:
                    bad.append(row.user_id)
                continue
            if args.apply:
                row.wrapped_dek = rotator.rotate(token)
            ok += 1
        print(f"keys checked: {len(rows)}  re-wrap: {ok}  already on new key: {already_new}  unreadable: {len(bad)}")
        if bad:
            print("Unreadable with either key (user ids):", ", ".join(str(b) for b in bad))
            if not args.skip_undecryptable:
                print("Aborting. Fix the keys or pass --skip-undecryptable.", file=sys.stderr)
                db.rollback()
                return 1
        if not args.apply:
            print("Dry run only. Re-run with --apply to write changes.")
            db.rollback()
            return 0
        # Verify every re-wrapped key opens under the NEW key before committing.
        for row in rows:
            if row.user_id in bad:
                continue
            new_f.decrypt(bytes(row.wrapped_dek))
        db.commit()
        print("Done. Now set SANJEEVANI_MASTER_KEY to the NEW key and reboot the app.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
