# Sanjeevani AI Safety Model Card — Launch Candidate

## Intended use

Supportive conversation, wellbeing reflection, structured self-help interventions from a reviewed catalog, mood/journal support, and routing to human/professional resources.

## Not intended for

Diagnosis, emergency dispatch, autonomous clinical decisions, medication decisions, or replacing qualified mental-health professionals.

## Safety design

- deterministic crisis tripwires before LLM classification
- conservative higher-risk heuristics
- LLM classification as a routing heuristic, not a clinical diagnosis
- fail-closed behavior on classifier failure
- human review queue for elevated cases
- reviewed intervention catalog
- user-controlled memory
- encrypted sensitive data

## Known limitations

The current repository does not constitute clinical validation. Coverage of language, culture, slang, indirect risk and rare failure modes must be measured independently before release.
