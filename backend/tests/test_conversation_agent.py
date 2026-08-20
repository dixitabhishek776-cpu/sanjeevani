from app.agents import conversation_agent as conv_module
from app.agents.conversation_agent import ConversationAgent


def test_llm_failure_falls_back_to_safe_text(monkeypatch):
    def raise_error(**kwargs):
        raise RuntimeError("simulated network failure")

    monkeypatch.setattr(conv_module, "call_llm", raise_error)

    agent = ConversationAgent()
    result = agent.generate_response("I'm having a hard time", {"show_resources_first": False}, "moderate")

    assert result["text"] == conv_module.SAFE_FALLBACK_TEXT
    assert result["text"] != ""  # never an empty reply


def test_resources_shown_when_directive_requires_it(monkeypatch):
    monkeypatch.setattr(conv_module, "call_llm", lambda **kwargs: "I'm here with you.")

    agent = ConversationAgent()
    result = agent.generate_response(
        "message", {"show_resources_first": True}, "immediate"
    )
    assert result["resources_shown"] is True
    assert result["resources_text"] is not None


def test_resources_not_shown_for_low_concern(monkeypatch):
    monkeypatch.setattr(conv_module, "call_llm", lambda **kwargs: "Glad to hear it!")

    agent = ConversationAgent()
    result = agent.generate_response("message", {"show_resources_first": False}, "low")
    assert result["resources_shown"] is False
    assert result["resources_text"] is None


def test_empty_llm_response_still_falls_back_to_safe_text(monkeypatch):
    monkeypatch.setattr(conv_module, "call_llm", lambda **kwargs: "   ")  # whitespace-only

    agent = ConversationAgent()
    result = agent.generate_response("message", {"show_resources_first": False}, "low")
    assert result["text"] == conv_module.SAFE_FALLBACK_TEXT
