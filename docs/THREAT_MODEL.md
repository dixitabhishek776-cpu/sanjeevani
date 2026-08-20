# Sanjeevani Threat Model

Assets: account credentials, access/refresh tokens, chats, journals, moods, memories, emergency contacts, safety assessments, reviewer notes, encryption keys.

Threats: account takeover, credential stuffing, BOLA/IDOR, XSS/token theft, CSRF, prompt injection, data exfiltration, insider misuse, notification spoofing, provider compromise, database theft, log leakage, backup leakage, model hallucination, safety false negatives, denial of service.

Controls: short-lived access tokens, HttpOnly refresh cookies in staging/production, rotation/revocation, password lockout, rate limiting, user-scoped queries, encryption, key revocation, no-store headers, CSP, audit records, secret scanning, durable outbox, fail-closed safety routing, independent review gate, backups and restore drills.

Residual risks: clinical false negatives, compromised user device, compromised cloud/provider account, legal/compliance interpretation, human escalation availability, and untested real-world language patterns. These require external operational controls and ongoing evaluation.
