from app.agents import conversation_agent as ca


def _boom(*a, **k):
    raise RuntimeError("llm down")


def test_crisis_fallback_is_not_generic_retry_message(monkeypatch):
    monkeypatch.setattr(ca, "call_llm", _boom)
    out = ca.ConversationAgent().generate_response(
        "I want to die", {"show_resources_first": True}, "immediate"
    )
    assert out["text"] == ca.CRISIS_FALLBACK_TEXT
    assert out["resources_shown"] is True


def test_normal_fallback_unchanged(monkeypatch):
    monkeypatch.setattr(ca, "call_llm", _boom)
    out = ca.ConversationAgent().generate_response("hello", {}, "low")
    assert out["text"] == ca.SAFE_FALLBACK_TEXT


def test_crisis_empty_reply_uses_crisis_fallback(monkeypatch):
    monkeypatch.setattr(ca, "call_llm", lambda *a, **k: "   ")
    out = ca.ConversationAgent().generate_response(
        "I want to die", {"show_resources_first": True}, "immediate"
    )
    assert out["text"] == ca.CRISIS_FALLBACK_TEXT


def test_classifier_outage_does_not_create_review_alert():
    from app.agents.safety_agent import SafetyAssessment, decision_router
    degraded = SafetyAssessment("moderate", ["classifier_error_fail_closed"], "x", 0.0)
    d = decision_router(degraded)
    assert d["create_alert"] is False and d["degraded"] is True
    real = SafetyAssessment("moderate", ["low_mood"], "x", 0.6)
    assert decision_router(real)["create_alert"] is True
