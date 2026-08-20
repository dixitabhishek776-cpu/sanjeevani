import pytest

from app.agents import safety_agent as safety_agent_module
from app.agents.safety_agent import SafetyIntelligenceAgent, decision_router
from app.agents.emotion_agent import EmotionAnalysisAgent


@pytest.fixture
def agent():
    return SafetyIntelligenceAgent()


@pytest.fixture
def emotion():
    return EmotionAnalysisAgent().analyze("placeholder message")


class TestKeywordPreFilter:
    """The pre-filter must catch explicit crisis language WITHOUT ever
    calling the LLM — this is the fail-safe layer described in Ch.1 Sec.2
    and must work even if the LLM is down or unreachable."""

    def test_explicit_crisis_phrase_routes_immediate_without_llm_call(self, agent, emotion, monkeypatch):
        def fail_if_called(*args, **kwargs):
            raise AssertionError("LLM should NOT be called when the pre-filter already matched")

        monkeypatch.setattr(safety_agent_module, "call_llm_json", fail_if_called)

        result = agent.assess("I'm planning to kill myself tonight", emotion, [])
        assert result.concern_level == "immediate"
        assert result.confidence > 0.9

    def test_benign_message_does_not_trigger_prefilter(self, agent, emotion, monkeypatch):
        # Should fall through to the LLM stage — we mock it to return 'low'
        monkeypatch.setattr(
            safety_agent_module, "call_llm_json",
            lambda **kwargs: {"concern_level": "low", "contributing_factors": [], "explanation": "fine", "confidence": 0.9},
        )
        result = agent.assess("I had a great day today", emotion, [])
        assert result.concern_level == "low"


class TestLLMClassificationStage:
    def test_uses_llm_result_when_valid(self, agent, emotion, monkeypatch):
        monkeypatch.setattr(
            safety_agent_module, "call_llm_json",
            lambda **kwargs: {
                "concern_level": "high",
                "contributing_factors": ["hopelessness"],
                "explanation": "Expresses hopelessness without explicit plan.",
                "confidence": 0.7,
            },
        )
        result = agent.assess("I don't see the point in anything anymore", emotion, [])
        assert result.concern_level == "high"
        assert "hopelessness" in result.contributing_factors

    def test_invalid_concern_level_from_llm_fails_closed(self, agent, emotion, monkeypatch):
        monkeypatch.setattr(
            safety_agent_module, "call_llm_json",
            lambda **kwargs: {"concern_level": "not_a_real_level", "confidence": 0.5},
        )
        result = agent.assess("some message", emotion, [])
        # Must fail closed to 'moderate', never silently to 'low'
        assert result.concern_level == "moderate"
        assert "fail_closed" in " ".join(result.contributing_factors)

    def test_llm_exception_fails_closed_to_moderate(self, agent, emotion, monkeypatch):
        def raise_error(**kwargs):
            raise RuntimeError("simulated API timeout")

        monkeypatch.setattr(safety_agent_module, "call_llm_json", raise_error)

        result = agent.assess("some ambiguous message", emotion, [])
        assert result.concern_level == "moderate"
        assert result.confidence == 0.0

    def test_never_fails_silently_to_low(self, agent, emotion, monkeypatch):
        """This is the single most important safety invariant in the whole
        system: on ANY classifier failure, the floor is 'moderate', never
        'low'. If this test fails, do not deploy the change that broke it."""
        monkeypatch.setattr(
            safety_agent_module, "call_llm_json",
            lambda **kwargs: (_ for _ in ()).throw(ValueError("malformed json")),
        )
        result = agent.assess("anything", emotion, [])
        assert result.concern_level != "low"


class TestDecisionRouter:
    def test_immediate_triggers_full_escalation(self, agent, emotion):
        result = agent.assess("I have a suicide plan for tonight", emotion, [])
        directive = decision_router(result)
        assert directive["show_resources_first"] is True
        # No contact-notification provider is wired yet; never claim an
        # emergency contact was notified. The alert is routed for human action.
        assert directive["notify_emergency_contact"] is False
        assert directive["human_escalation"] == "realtime_oncall_if_configured"

    def test_low_creates_no_alert(self):
        from app.agents.safety_agent import SafetyAssessment

        directive = decision_router(SafetyAssessment(concern_level="low"))
        assert directive["create_alert"] is False
        assert directive["human_escalation"] is None
