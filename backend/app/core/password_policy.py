"""Shared password policy used by the FastAPI backend and the Streamlit app.

Rules (kept simple and explainable to users):
  * 12 to 128 characters, no leading/trailing whitespace
  * not a very common password (checked in a normalised form)
  * not built from the person's own email name or display name
  * not just one or two repeated characters or a simple sequence
"""
import re
from typing import Optional

MIN_LENGTH = 12
MAX_LENGTH = 128

# Common passwords/bases seen in public breach lists. Compared against the
# normalised form of the password (lowercase letters + digits only), and also
# against that form with trailing digits removed ("password1234" -> "password").
_COMMON = frozenset("""
password passw0rd p4ssword pa55word passphrase admin administrator root toor
qwerty qwertyuiop qwertyuiopasdf asdfghjkl asdfghjklzxcv zxcvbnm azertyuiop
letmein welcome welcome1 iloveyou iloveu monkey dragon master sunshine princess
football baseball cricket abc123 abcdefgh abcdefghijkl trustno1 starwars
superman batman shadow michael jordan harley hunter ranger buster whatever
changeme default secret login guest user test testing temp temporary
sanjeevani amrit mitra india india123 bharat hindustan krishna shiva ganesh
jaishreeram radhakrishna harharmahadev omnamahshivaya sairam
12345678 123456789 1234567890 12345678901 123456789012 1234567890123
111111111111 000000000000 123123123123 987654321 987654321098 112233445566
iloveyou123 password123 qwerty123 admin123 welcome123 letmein123
""".split())

_SEQUENCES = ("abcdefghijklmnopqrstuvwxyz", "01234567890123456789", "qwertyuiopasdfghjklzxcvbnm")


def _normalise(p: str) -> str:
    return re.sub(r"[^a-z0-9]", "", p.lower())


def _is_simple_sequence(n: str) -> bool:
    if len(n) < 8:
        return False
    for seq in _SEQUENCES:
        if n in seq or n in seq[::-1]:
            return True
    return False


def password_problem(password: str, email: Optional[str] = None, name: Optional[str] = None) -> Optional[str]:
    """Returns a user-facing message describing what is wrong, or None if OK."""
    if password is None:
        return "Please enter a password."
    if password.strip() != password:
        return "Password must not start or end with a space."
    if len(password) < MIN_LENGTH:
        return f"Password must be at least {MIN_LENGTH} characters."
    if len(password) > MAX_LENGTH:
        return f"Password must be at most {MAX_LENGTH} characters."
    norm = _normalise(password)
    stripped = norm.rstrip("0123456789")
    if norm in _COMMON or (stripped and stripped in _COMMON):
        return "That password is too common. Try a few unrelated words, or a longer phrase."
    if len(set(password)) < 5 or _is_simple_sequence(norm):
        return "That password is too simple (repeated characters or a simple sequence)."
    if email:
        local = _normalise(email.split("@")[0])
        if len(local) >= 4 and local in norm:
            return "Password must not contain your email name."
    if name:
        for part in re.split(r"\s+", name.strip()):
            part_n = _normalise(part)
            if len(part_n) >= 4 and part_n in norm:
                return "Password must not contain your name."
    return None
