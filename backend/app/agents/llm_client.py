"""
Thin wrapper around an LLM API. Supports two backends, selected automatically:

- Groq (free tier, no credit card) — used if GROQ_API_KEY is set.
- Anthropic — used if ANTHROPIC_API_KEY is set (takes priority if both are set).

Both the Conversation Agent and the Safety Agent's LLM-classification
stage go through this single client so retries, timeouts, and error
handling are consistent in one place.
"""
import os
import json

from app.incident_log import record_incident

_client = None
_backend = None


def get_client():
    """Lazy-imports the relevant SDK on first real use, rather than
    at module load time. This means app modules (and tests) that only
    need the *pipeline structure* — e.g. the keyword pre-filter path, or
    tests that monkeypatch call_llm/call_llm_json — can import and run
    without any SDK or an API key being present at all."""
    global _client, _backend
    if _client is None:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        if anthropic_key:
            from anthropic import Anthropic

            _client = Anthropic(api_key=anthropic_key)
            _backend = "anthropic"
        elif groq_key:
            from groq import Groq

            _client = Groq(api_key=groq_key)
            _backend = "groq"
        else:
            raise RuntimeError(
                "No LLM API key is set. Set GROQ_API_KEY (free, get one at "
                "https://console.groq.com/keys) or ANTHROPIC_API_KEY "
                "(https://console.anthropic.com) in your environment."
            )
    return _client


def call_llm(system: str, user_message: str, max_tokens: int = 400) -> str:
    """Plain text completion. Raises on failure — callers must handle
    fail-closed behavior themselves (see safety_agent.py, conversation_agent.py).

    Resilience: retries transient failures (timeouts, rate limits, network
    blips) up to 2 times with exponential backoff before giving up. This
    catches the common case of a single flaky request without masking a
    genuinely broken configuration (wrong model name, bad API key) — those
    still fail fast-ish and surface to the fail-closed caller.
    """
    import time
    client = get_client()
    last_exc = None
    for attempt in range(3):
        try:
            if _backend == "groq":
                response = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_message},
                    ],
                    timeout=15.0,
                )
                return response.choices[0].message.content or ""
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_message}],
                timeout=15.0,
            )
            return "".join(block.text for block in response.content if block.type == "text")
        except Exception as exc:
            last_exc = exc
            record_incident("llm_call_retry", f"attempt {attempt + 1}/3 failed: {exc}")
            if attempt < 2:
                time.sleep(0.5 * (2 ** attempt))
    raise last_exc


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
