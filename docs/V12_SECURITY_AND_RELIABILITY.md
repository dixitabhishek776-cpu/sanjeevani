# V12 — Security, Reliability & Abuse Testing

## Required automated checks

1. Authentication: brute-force throttling, lockout, refresh-token rotation, replay rejection.
2. Authorization: every user-owned resource must query by both resource ID and authenticated user ID; reviewer routes require DB-backed role checks.
3. BOLA/IDOR: attempt access to another user's chat, journal, mood, memory, contact, export and deletion endpoints.
4. Input limits: body-size, string length, pagination, title/content lengths.
5. Abuse: rate-limit boundary tests, concurrent requests, idempotency replay, duplicate submissions.
6. Dependency/container: pip-audit, npm audit, image scanning, secret scanning.
7. Failure injection: PostgreSQL unavailable, Redis unavailable, LLM timeout/error, SMTP/webhook error, worker restart.
8. Recovery: backup + restore drill against an isolated database.

## Acceptance criteria

- No cross-user read/write is possible.
- Refresh-token replay is rejected.
- Concurrent idempotent chat retries produce one logical operation.
- Production refuses to start without required secrets.
- Public docs and metrics are inaccessible in production.
- Safety notification delivery is durable and retryable.
- No user message content or secrets appear in logs/metrics.

## Load testing

Run the bounded staging test only against infrastructure you own:

`python scripts/load_test.py https://staging.example.com 100`

Scale gradually with an approved performance budget. Never run uncontrolled load tests against third-party infrastructure.
