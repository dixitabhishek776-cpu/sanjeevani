import os
from app.main import readiness

def test_readiness_is_not_ready_without_llm(monkeypatch):
    monkeypatch.setenv("SANJEEVANI_ENV","production")
    monkeypatch.delenv("ANTHROPIC_API_KEY",raising=False)
    result=readiness()
    assert result.status_code==503
