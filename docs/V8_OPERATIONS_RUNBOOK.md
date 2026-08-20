# Sanjeevani V8 Operations Runbook

## Production startup
1. Provision PostgreSQL, Redis, KMS/secrets, object storage and monitoring.
2. Set production environment variables; never commit secrets.
3. Run `alembic upgrade head` as a one-off migration job.
4. Run `/livez`, `/health`, and `/v1/system/readiness` from the private monitoring network.
5. Start backend workers and frontend only after readiness succeeds.

## Backups
- Run `scripts/backup_postgres.sh` daily.
- Encrypt backups at rest and retain according to the approved data-retention policy.
- Verify SHA-256 manifests.
- Perform a restore drill at least monthly.

## Incident response
- Preserve request IDs and audit records.
- Disable affected feature flags before disabling safety-critical routing.
- Revoke compromised credentials/tokens.
- Record timeline, impact, containment, remediation and user-notification decision.

## Launch blockers
Public launch remains blocked until clinical/safety sign-off, independent security testing, real human escalation coverage, production privacy/legal review, and a successful restore drill are complete.
