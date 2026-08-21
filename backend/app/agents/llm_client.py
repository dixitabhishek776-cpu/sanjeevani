import os
import json

_client = None
_backend = None

def get_client():
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
            raise RuntimeError("No LLM API key is set. Set GROQ_API_KEY or ANTHROPIC_API_KEY.")
    return _client

def call_llm(system, user_message, max_tokens=400):
    client = get_client()
    if _backend == "groq":
        response = client.chat.completions.create(model="openai/gpt-oss-20b", max_tokens=max_tokens, messages=[{"role": "system", "content": system}, {"role": "user", "content": user_message}], timeout=15.0)
        return response.choices[0].message.content or ""
    response = client.messages.create(model="claude-sonnet-4-6", max_tokens=max_tokens, system=system, messages=[{"role": "user", "content": user_message}], timeout=15.0)
    return "".join(block.text for block in response.content if block.type == "text")

def call_llm_json(system, user_message, max_tokens=400):
    raw = call_llm(system, user_message, max_tokens=max_tokens)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError as e:
        raise ValueError("LLM did not return valid JSON: " + repr(raw)) from e
