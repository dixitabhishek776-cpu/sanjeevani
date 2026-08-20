# Sanjeevani V17.1 Safety Policy Decisions

## Decisions adopted

1. The LLM safety classifier must receive user messages as **untrusted DATA** and must never follow instructions embedded in the message.
2. Production readiness must fail closed when required LLM configuration is absent.
3. The clinical and safety release gate remains mandatory before public launch.
4. A bare `suicide` keyword is **not** treated as an automatic immediate-risk tripwire. Educational, awareness, prevention, historical, and other non-personal contexts must be evaluated by the broader safety pipeline.
5. `high` concern creates an urgent human-review alert but does **not** automatically notify an emergency contact. Automatic emergency-contact notification requires an explicitly approved clinical/safety policy.
6. The application must not claim that an emergency contact was notified unless a real notification provider successfully queued/sent that notification.

These are engineering defaults pending independent clinical/safety review. They are not clinical guidance.
