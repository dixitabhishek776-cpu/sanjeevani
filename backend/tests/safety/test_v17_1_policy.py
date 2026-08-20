from app.agents.safety_agent import SafetyAssessment, decision_router

def test_high_concern_does_not_auto_notify_emergency_contact():
    directive = decision_router(SafetyAssessment("high"))
    assert directive["notify_emergency_contact"] is False

def test_immediate_does_not_auto_notify_by_default(monkeypatch):
    monkeypatch.delenv("SANJEEVANI_AUTO_EMERGENCY_CONTACT_IMMEDIATE", raising=False)
    directive = decision_router(SafetyAssessment("immediate"))
    assert directive["notify_emergency_contact"] is False

def test_immediate_notification_requires_explicit_policy_opt_in(monkeypatch):
    monkeypatch.setenv("SANJEEVANI_AUTO_EMERGENCY_CONTACT_IMMEDIATE", "true")
    directive = decision_router(SafetyAssessment("immediate"))
    assert directive["notify_emergency_contact"] is True
