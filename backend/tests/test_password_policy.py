import pytest

from app.core.password_policy import password_problem


@pytest.mark.parametrize("pw", [
    "correct horse battery staple", "Tr0ub4dor&3-purple-lotus", "mitra-sings-at-dawn-7",
    "Str0ng-Passw0rd!x", "a1b2c3d4e5f6g7h8",
])
def test_good_passwords(pw):
    assert password_problem(pw) is None


@pytest.mark.parametrize("pw,frag", [
    ("short1!", "at least 12"),
    (" leadingspace123", "start or end"),
    ("trailingspace123 ", "start or end"),
    ("password1234", "too common"),
    ("Password-1234", "too common"),
    ("qwertyuiop12", "too common"),
    ("123456789012", "too common"),
    ("aaaaaaaaaaaa", "too simple"),
    ("abababababab", "too simple"),
    ("abcdefghijklmnop", "too simple"),
    ("x" * 129, "at most"),
])
def test_bad_passwords(pw, frag):
    assert frag in password_problem(pw)


def test_rejects_email_and_name_parts():
    assert "email name" in password_problem("riyasharma99-Xz!", email="riyasharma99@example.com")
    assert "your name" in password_problem("Abhishek-loves-chai", name="Abhishek Dixit")
    assert password_problem("unrelated-words-here-42", email="riya@example.com", name="Riya") is None
