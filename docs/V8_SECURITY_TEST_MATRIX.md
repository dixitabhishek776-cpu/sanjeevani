# V8 Security Test Matrix

Mapped to OWASP API Security Top 10 2023:
- BOLA: verify every user-owned resource rejects another user's ID.
- Broken authentication: expired/revoked/rotated tokens must fail.
- Property authorization: mass-assignment attempts must be rejected.
- Resource consumption: payload, page-size, login, reset and notification limits.
- Function authorization: reviewer endpoints require reviewer roles.
- Sensitive flows: reset/verification/notification endpoints are throttled.
- SSRF: remote destinations are configuration-only and must use an allowlist in production.
- Misconfiguration: production docs/default secrets are prohibited.
- Inventory: CI checks deployed API routes and release artifacts.
- Third-party APIs: validate provider responses and enforce timeouts/cost limits.
