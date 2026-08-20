"""
Emotion Analysis Agent (Chapter 1, Sec.3).

Scaffold implementation: uses simple lexicon-based sentiment as a stand-in
for a real emotion model. Swap `analyze()` internals for a proper
model/API call (e.g. a fine-tuned classifier or LLM call) in production.
Interface is stable so callers never need to change.
"""
from dataclasses import dataclass

NEGATIVE_WORDS = {
    "sad", "hopeless", "worthless", "tired", "exhausted", "anxious",
    "overwhelmed", "alone", "empty", "numb", "scared", "angry", "hurt",
    "crying", "cry", "depressed", "panic", "worried",
}
POSITIVE_WORDS = {
    "happy", "good", "great", "grateful", "calm", "hopeful", "excited",
    "proud", "relieved", "okay", "fine", "better", "peaceful",
}


@dataclass
class EmotionSignal:
    valence: float          # -1 (very negative) to +1 (very positive)
    arousal: float          # 0 (calm) to 1 (highly activated)
    primary_emotion: str
    deviation_from_baseline: float  # 0 = matches baseline, 1 = large deviation


class EmotionAnalysisAgent:
    def analyze(self, text: str, baseline_valence: float = 0.0) -> EmotionSignal:
        tokens = [t.strip(".,!?").lower() for t in text.split()]
        neg = sum(1 for t in tokens if t in NEGATIVE_WORDS)
        pos = sum(1 for t in tokens if t in POSITIVE_WORDS)
        total = max(neg + pos, 1)
        valence = (pos - neg) / total if (pos or neg) else 0.0
        arousal = min(1.0, (neg + pos) / max(len(tokens), 1) * 3)
        primary = "negative" if valence < -0.15 else "positive" if valence > 0.15 else "neutral"
        deviation = min(1.0, abs(valence - baseline_valence))

        return EmotionSignal(
            valence=round(valence, 3),
            arousal=round(arousal, 3),
            primary_emotion=primary,
            deviation_from_baseline=round(deviation, 3),
        )
