"""Security regression tests that require only the application source plus pytest.
Database/network integration tests live in CI and are intentionally separate.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_no_plaintext_sensitive_logging_patterns():
    forbidden = ("print(payload", "print(password", "print(token", "logger.info(payload")
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts or "tests" in path.parts and "security" in path.parts:
            continue
        text = path.read_text(errors="ignore")
        for pattern in forbidden:
            assert pattern not in text, f"Sensitive logging pattern {pattern!r} in {path}"


def test_no_default_production_secrets():
    text = (ROOT / "app" / "core" / "auth.py").read_text()
    assert 'SANJEEVANI_ENV", "development"' in text
    assert "SANJEEVANI_JWT_SECRET must be set in production" in text


def test_models_are_valid_python_ast():
    for path in (ROOT / "app").rglob("*.py"):
        ast.parse(path.read_text())
