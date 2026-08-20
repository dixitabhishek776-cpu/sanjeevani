"""
Thin wrapper around the Anthropic API.

Requires an ANTHROPIC_API_KEY environment variable (get one at
https://console.anthropic.com — separate from your claude.ai account).

Both the Conversation Agent and the Safety Agent's LLM-classification
stage go through this single client so retries, timeouts, and error
handling are consistent in one place.
"""
import os
import json

_client = None


def get_client():
    """Lazy-imports the anthropic package on first real use, rather than
    at module load time. This means app modules (and tests) that only
    need the *pipeline structure* — e.g. the keyword pre-filter path, or
    tests that monkeypatch call_llm/call_llm_json — can import and run
    without the anthropic package or an API key being present at all."""
    global _client
    if _client is None:
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Get a key at "
                "https://console.anthropic.com and put it in your .env file."
            )
        _client = Anthropic(api_key=api_key)
    return _client


def call_llm(system: str, user_message: str, max_tokens: int = 400) -> str:
    """Plain text completion. Raises on failure — callers must handle
    fail-closed behavior themselves (see safety_agent.py, conversation_agent.py)."""
    client = get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}],
        timeout=15.0,
    )
    return "".join(block.text for block in response.content if block.type == "text")


def call_llm_json(system: str, user_message: str, max_tokens: int = 400) -> dict:
    """Completion that expects a strict JSON object back. Raises ValueError
    if the model doesn't return parseable JSON — treat as a classifier
    failure and fail closed, don't retry-loop indefinitely."""
    raw = call_llm(system, user_message, max_tokens=max_tokens)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {raw!r}") from e
