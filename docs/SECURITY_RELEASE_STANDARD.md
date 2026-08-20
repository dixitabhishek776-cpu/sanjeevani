# Sanjeevani Security & Release Standard

This document is the minimum engineering bar before a public release. It is not a legal certification.

## Mandatory controls
- Production uses unique secrets outside source control.
- Production uses managed KMS/equivalent key management.
- Production schema changes use Alembic; API startup does not perform production DDL.
- HTTPS is mandatory.
- CORS is allow-list based.
- Redis is required for distributed rate limiting in production.
- Access tokens are short-lived; refresh tokens are random, hashed, rotated and revocable.
- Sensitive content uses per-user AES-256-GCM encryption with wrapped DEKs.
- Secrets and raw tokens never appear in logs.
- Safety alerts are auditable and human-reviewable.
- Backups are encrypted and restoration is tested.

## Security testing before launch
1. SAST and dependency scanning.
2. Container image scanning.
3. Authentication/authorization tests.
4. Rate-limit and abuse tests.
5. Prompt-injection tests.
6. Cross-tenant isolation tests.
7. Encryption/key-revocation tests.
8. Independent penetration test.

## Never ship
- Default production secrets.
- Development master keys.
- Unreviewed crisis-response prompts.
- Unstaffed human-escalation promises.
- Unreviewed claims that Sanjeevani diagnoses or treats disorders.

## V7 automated controls
- Every request receives a correlation/request ID.
- Low-cardinality HTTP metrics are available only behind `SANJEEVANI_METRICS_TOKEN`.
- Production API documentation is disabled by default.
- Login attempts and chat traffic are rate-limited.
- Production requires Redis for distributed rate limiting.
- Password reset and email verification tokens are single-use and hashed at rest.
- Password reset revokes active refresh sessions.
- Critical account deletion requires re-authentication and explicit confirmation.
