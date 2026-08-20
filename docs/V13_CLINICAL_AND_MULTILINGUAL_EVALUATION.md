# V13 — Clinical, Safety & Multilingual Evaluation

Sanjeevani is not clinically validated by automated tests. V13 defines the evidence package that must be reviewed by qualified mental-health professionals and people with lived experience before public use.

## Dataset families

- ordinary wellbeing conversations
- stress/anxiety/depression-like distress without self-harm intent
- indirect or metaphorical risk language
- explicit self-harm/suicide language
- imminent intent/plan/means
- self-harm negation and quoted text
- concern about another person
- Hindi
- Hinglish / Romanized Hindi
- code-switching
- slang and misspellings
- sarcasm and figurative language
- prompt injection embedded in distress text
- adversarial attempts to suppress crisis resources

## Metrics

Report sensitivity/recall for high and immediate risk, specificity, false-positive rate, calibration, abstention/fail-closed rate, intervention appropriateness, resource correctness and human-review agreement.

Do not optimize only for accuracy. For safety routing, false negatives and failure modes require explicit clinical review.

## Release requirement

A signed clinical/safety review is required before `SAFETY_BENCHMARK_PASSED=1` can be used in the final launch gate.
