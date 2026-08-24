"""
Thin wrapper around an LLM API. Supports three backends, selected automatically:

- Anthropic — used if ANTHROPIC_API_KEY is set (highest priority).
- Groq (free tier, no credit card) — used as primary if ANTHROPIC_API_KEY is
  not set and GROQ_API_KEY is.
- Gemini (free tier, no credit card) — used as a FALLBACK when the primary
  backend's own retries are exhausted (e.g. Groq's free-tier daily/per-minute
  cap is hit), if GEMINI_API_KEY is set. This roughly doubles the free daily
  message capacity, since Groq and Gemini's free quotas are independent of
  each other, without adding any cost — both stay genuinely free at this
  scale.

Both the Conversation Agent and the Safety Agent's LLM-classification
stage go through this single client so retries, timeouts, fallback, and
error handling are consistent in one place.
"""
import os
import json
import time

from app.incident_log import record_incident

_client = None
_backend = None
_fallback_client = None
_fallback_backend = None
_fallback_checked = False


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
        gemini_key = os.getenv("GEMINI_API_KEY")
        if anthropic_key:
            from anthropic import Anthropic

            _client = Anthropic(api_key=anthropic_key)
            _backend = "anthropic"
        elif groq_key:
            from groq import Groq

            _client = Groq(api_key=groq_key)
            _backend = "groq"
        elif gemini_key:
            import google.generativeai as genai

            genai.configure(api_key=gemini_key)
            _client = genai
            _backend = "gemini"
        else:
            raise RuntimeError(
                "No LLM API key is set. Set GROQ_API_KEY (free, "
                "https://console.groq.com/keys), GEMINI_API_KEY (free, "
                "https://aistudio.google.com/apikey), or ANTHROPIC_API_KEY "
                "(https://console.anthropic.com) in your environment."
            )
    return _client


def get_fallback_client():
    """A second, independent free-tier LLM backend used only when the
    primary backend fails after its own retries. Only set up if a
    different provider's key is configured and it isn't already the
    primary — no point falling back to the same provider that just failed."""
    global _fallback_client, _fallback_backend, _fallback_checked
    if _fallback_checked:
        return _fallback_client, _fallback_backend
    _fallback_checked = True
    get_client()  # ensure primary _backend is resolved first
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    if _backend != "gemini" and gemini_key:
        import google.generativeai as genai

        genai.configure(api_key=gemini_key)
        _fallback_client = genai
        _fallback_backend = "gemini"
    elif _backend != "groq" and groq_key:
        from groq import Groq

        _fallback_client = Groq(api_key=groq_key)
        _fallback_backend = "groq"
    return _fallback_client, _fallback_backend


def _call_backend(backend: str, client, system: str, user_message: str, max_tokens: int) -> str:
    if backend == "groq":
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
    if backend == "gemini":
        model = client.GenerativeModel("gemini-2.5-flash-lite", system_instruction=system)
        response = model.generate_content(
            user_message,
            generation_config={"max_output_tokens": max_tokens},
            request_options={"timeout": 15.0},
        )
        return response.text or ""
    # anthropic
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}],
        timeout=15.0,
    )
    return "".join(block.text for block in response.content if block.type == "text")


def call_llm(system: str, user_message: str, max_tokens: int = 400) -> str:
    """Plain text completion. Raises on failure — callers must handle
    fail-closed behavior themselves (see safety_agent.py, conversation_agent.py).

    Resilience: retries transient failures on the primary backend up to 3
    times with exponential backoff, then — if a second, independent free
    LLM provider is configured — falls back to it once before giving up.
    This catches both single flaky requests and a backend's rate limit
    being exhausted, without masking a genuinely broken configuration.
    """
    client = get_client()
    last_exc = None
    for attempt in range(3):
        try:
            return _call_backend(_backend, client, system, user_message, max_tokens)
        except Exception as exc:
            last_exc = exc
            record_incident("llm_call_retry", f"{_backend} attempt {attempt + 1}/3 failed: {exc}")
            if attempt < 2:
                time.sleep(0.5 * (2 ** attempt))

    fb_client, fb_backend = get_fallback_client()
    if fb_client:
        try:
            record_incident("llm_fallback_used", f"primary '{_backend}' exhausted, switching to '{fb_backend}'")
            return _call_backend(fb_backend, fb_client, system, user_message, max_tokens)
        except Exception as exc2:
            record_incident("llm_fallback_failed", f"{fb_backend}: {exc2}")
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
