"""Input safety guard for untrusted user content.

User text is DATA, never instructions. This guard does not attempt to decide
clinical risk; it only detects common prompt-injection patterns and produces a
sanitized envelope for downstream model calls.
"""
import re
from dataclasses import dataclass

INJECTION_PATTERNS = [
    r"ignore (all|any|the) (previous|prior|above) instructions",
    r"system prompt",
    r"developer message",
    r"reveal (your|the) (prompt|instructions|chain of thought)",
    r"jailbreak",
    r"you are now (a|an)",
    r"disregard (your|the) safety",
]

@dataclass(frozen=True)
class GuardResult:
    text: str
    injection_detected: bool
    matched_rules: tuple[str, ...]


def guard_user_text(text: str, max_chars: int = 4000) -> GuardResult:
    normalized = text[:max_chars]
    lower = normalized.casefold()
    matches = tuple(p for p in INJECTION_PATTERNS if re.search(p, lower))
    # Preserve the user's content; only mark it as untrusted. The model prompt
    # explicitly separates DATA from instructions, avoiding destructive rewrites.
    return GuardResult(normalized, bool(matches), matches)
