# Sanjeevani V15 Release Evidence

## Engineering checks executed in this environment

- Python compilation: PASS
- repository secret scan: PASS
- static release check: PASS
- deterministic V12/V13 regression tests: 11/11 PASS
- archive generation: PASS
- final public-launch gate: BLOCKED as designed because external approvals/infrastructure evidence are not present

## Important test limitation

The execution environment does not provide the project's external PostgreSQL/Redis/npm dependencies and cannot install them from the network. Therefore this artifact does **not** claim that the complete database integration suite or Next.js production build passed here. The GitHub Actions workflow `release-gates.yml` is configured to perform those connected checks.

## Security improvements included

- staging/production HttpOnly refresh-token cookie
- refresh-token rotation with row locking
- session revocation on password reset
- request payload limits
- security headers/CSP/HSTS in production
- TrustedHost in production
- Redis-backed rate limiting with production fail-closed behavior
- PostgreSQL advisory locking for idempotent chat requests
- durable notification outbox with worker lease recovery
- user-scoped resource queries retained
- secret scanning and release gates
- encrypted sensitive data and key revocation

## Safety improvements included

- deterministic crisis tripwires
- conservative elevated-risk routing
- prompt-injection guard
- fail-closed LLM classifier behavior
- reviewed intervention catalog architecture
- high/immediate alerts
- opt-in emergency-contact notification queue
- human-review workflow
- multilingual evaluation framework

## External launch gates

The application intentionally cannot self-certify the following:

1. Independent clinical/safety review
2. Independent security/penetration review
3. Privacy/legal review for each launch jurisdiction
4. Staffed human escalation operation
5. Successful isolated backup/restore drill
6. Connected staging end-to-end test
7. Clinically reviewed safety benchmark

These must be evidenced by the actual responsible people/organizations before public launch.
