"""Deterministic intervention selector.

The LLM may personalize wording, but it does not invent intervention content.
Only reviewed catalog entries are eligible and crisis levels never receive
routine self-help interventions.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Intervention:
    slug: str
    title: str
    indication: str
    steps: tuple[str, ...]
    evidence_source: str

CATALOG = (
    Intervention(
        "grounding-54321", "5-4-3-2-1 grounding", "stress",
        ("Name 5 things you can see.", "Name 4 things you can touch.", "Name 3 things you can hear.", "Name 2 things you can smell.", "Name 1 thing you can taste."),
        "WHO stress-management self-help materials",
    ),
    Intervention(
        "slow-breathing", "Slow breathing", "stress",
        ("Sit comfortably.", "Breathe in gently.", "Breathe out slowly.", "Repeat for a few minutes without forcing the breath."),
        "WHO stress-management self-help materials",
    ),
)


def select_intervention(concern_level: str, emotion_primary: str, *, enabled: bool = True) -> Optional[Intervention]:
    if not enabled or concern_level in {"high", "immediate"}:
        return None
    # Keep selection conservative until a clinician-reviewed catalog is larger.
    if concern_level == "moderate" or emotion_primary == "negative":
        return CATALOG[0]
    return None
