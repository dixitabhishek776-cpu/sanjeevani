# Sanjeevani V10 production readiness

V10 adds explicit user-controlled memory and a durable notification outbox/worker. Safety notifications are queued transactionally with the alert instead of performing network delivery in the request path.

## Required before production
- Run Alembic migrations through 0005 against a managed PostgreSQL staging database.
- Run the notification worker with AWS KMS enabled and production SMTP/webhook credentials stored in a secrets manager.
- Execute backup/restore drills.
- Run the connected CI pipeline; this environment cannot install external packages.
- Complete independent clinical/safety review and multilingual red-team evaluation.
- Complete penetration testing and dependency/container scanning.
- Configure staffed human escalation and incident response.
- Obtain deployment-specific privacy/legal review.
