# Sanjeevani V7 Integration Test Plan

## Automated in CI
1. Python compilation.
2. Backend unit/regression tests.
3. Safety evaluation dataset.
4. Secret scan.
5. Frontend dependency install and production build.

## Required staging tests
- Register → verify email → login → refresh → logout.
- Five failed logins → temporary lock → unlock after timeout.
- Password reset → old refresh token rejected.
- User A cannot access User B chats, journals, moods, contacts or alerts.
- Reviewer cannot access another reviewer's restricted functions unless explicitly authorized.
- Immediate-risk message creates a reviewer alert and crisis resources.
- Classifier failure fails closed to moderate and records the failure factor.
- Redis outage in production denies protected high-cost flows rather than silently using process-local limits.
- Metrics endpoint is inaccessible without its bearer token and contains no user identifiers.
- Account deletion revokes sessions and cryptographically revokes the user DEK.

## Load/abuse tests
- Burst chat requests.
- Password-reset enumeration attempts.
- Verification-token guessing.
- Oversized JSON payloads.
- Concurrent refresh-token reuse.
- Reviewer endpoint enumeration.

## Security acceptance
Map findings against OWASP ASVS and OWASP API Security Top 10 before public launch. In particular verify object-level authorization, authentication, resource-consumption controls, function-level authorization, security configuration and third-party API handling.
