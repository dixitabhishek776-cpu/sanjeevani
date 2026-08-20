# Sanjeevani 17.3 — Final-Gap Hardening

## Engineering changes
- Added reviewer lifecycle timestamps (`acknowledged_at`, `last_escalated_at`).
- Reviewer workflow now requires `pending_review -> acknowledged -> resolved` and requires resolution notes.
- Added an active high/immediate safety floor: unresolved elevated alerts cannot be silently lowered by a new model classification.
- Emergency-contact automation now requires both an explicit approval flag and a non-empty policy version in addition to the existing feature flag.
- Added IP/email rate limiting to registration, password-reset and verification-resend endpoints.
- Expanded bounded load testing to report throughput, p50/p95/p99 latency and error samples.
- Added GitHub Actions CI with PostgreSQL and Redis services, Alembic migration, backend tests, TypeScript and production frontend build.
- Added a release-evidence template to separate executable checks from external approvals.

## Remaining external gates
These cannot be truthfully marked complete by code alone:
- Independent penetration test.
- Clinical/lived-experience review.
- Production-like staging execution.
- Real load-test evidence.
- Backup/restore drill.
- Privacy/legal review for the actual launch jurisdictions.
- Staffed human escalation and incident drills.

## Safety policy
No automatic emergency-contact action is enabled by default. No bare keyword is treated as sufficient proof of imminent risk. The product remains a mental-wellness support system, not a diagnostic or emergency-dispatch service.
