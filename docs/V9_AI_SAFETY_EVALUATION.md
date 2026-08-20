# V9 AI Safety & Intervention Evaluation

V9 introduces a deterministic intervention selector and a prompt-injection guard around all model-facing user content.

## Safety principles
- User content is untrusted data, never instructions.
- Explicit crisis tripwires run before the LLM.
- Conservative high-risk heuristics run before the LLM.
- LLM failure fails closed to moderate, never low.
- High/immediate risk never receives routine self-help interventions.
- Intervention wording comes only from a reviewed catalog; the LLM may personalize but may not invent the intervention steps.

## Required release evidence
1. Run `python -m evaluation.run_v9_eval`.
2. Add clinician-reviewed English, Hindi, Hinglish and adversarial cases before release.
3. Measure false negatives separately from false positives.
4. Test prompt injection, jailbreaks, indirect language, sarcasm and context drift.
5. Require independent clinical/safety sign-off before public crisis-facing use.

This evaluation is an engineering gate, not clinical validation.
