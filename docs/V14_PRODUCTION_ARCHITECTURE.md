# V14 — Production Architecture

## Recommended topology

`CloudFront/WAF -> managed load balancer -> stateless FastAPI replicas -> managed PostgreSQL + managed Redis`

Supporting services:

- KMS for envelope-encryption key protection
- Secrets Manager for API/database credentials
- Object storage for encrypted backups with lifecycle retention
- centralized logs and metrics
- error tracking with sensitive-data scrubbing
- alerting/on-call system
- separate worker pool for notifications/background jobs

## Scaling principles

- API replicas remain stateless.
- PostgreSQL is the system of record; use connection pooling and read replicas only when measured demand requires them.
- Redis is used for rate limiting and short-lived coordination, never as the authoritative store for wellbeing records.
- Safety alerts and notifications are durable in PostgreSQL before network delivery.
- All encryption keys are externalized from application containers in production.
- Backups are encrypted, access-controlled and regularly restored in an isolated environment.

## Availability targets

Define SLOs before public launch. Suggested initial targets:

- API availability: 99.9% monthly
- successful request rate: >= 99.9% for non-provider failures
- p95 normal API latency: < 500 ms excluding LLM generation
- safety-alert persistence: >= 99.99%
- notification queue durability: >= 99.99%

These are targets, not guarantees; they must be validated with real infrastructure.
