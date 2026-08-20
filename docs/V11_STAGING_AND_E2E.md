# Sanjeevani V11 — staging and end-to-end validation

## Goal
Exercise the complete service graph in a controlled staging environment before security/clinical release gates.

## Service graph
Frontend → FastAPI → PostgreSQL + Redis → safety/LLM services → encrypted persistence → notification outbox → worker.

## Required checks
1. `docker compose -f docker-compose.staging.yml up --build -d`
2. `docker compose -f docker-compose.staging.yml ps` — every healthcheck green.
3. `./scripts/staging_smoke.sh` — API, PostgreSQL, Redis and frontend reachable.
4. Verify `alembic upgrade head` reached revision `0006_idempotency`.
5. Register → verify email → login → refresh → logout.
6. Enable memory → create/read/update/delete memory.
7. Create journal/mood/chat records and verify export.
8. Send the same chat request twice with one `Idempotency-Key`; exactly one message pair must be persisted; the idempotency record must contain only an encrypted response blob, never plaintext conversation content.
9. Reuse the same key with a different payload; expect HTTP 409.
10. Trigger a synthetic high-risk test case; verify alert + durable outbox row without sending an emergency dispatch.
11. Stop the worker, enqueue a notification, restart worker and verify eventual delivery.
12. Stop Redis and confirm staging reports degraded health; do not run this failure test against production.
13. Restore PostgreSQL from a backup into a clean database and run the smoke test again.

## Release evidence
Attach CI logs, migration revision, smoke output, backup/restore result, and safety evaluation report to the release record.

## Important
Staging uses synthetic accounts/data only. Never use real crisis or identifiable mental-health data for automated testing.
