# Sanjeevani Scaffold Audit & MVP Completion Report

## What was reviewed

- Frontend: Next.js/React pages, API client, chat, mood, journal, privacy, reviewer queue.
- Backend: FastAPI routes, auth, encryption, agent pipeline, safety routing, persistence models, migrations, tests, Docker configuration.
- Safety invariants: fail-closed classifier behavior and crisis routing.

## Changes made

1. **Authentication hardening**
   - Normalized registration/login email addresses to lowercase.
   - Deleted accounts can no longer authenticate.
   - Production now requires `SANJEEVANI_JWT_SECRET` instead of silently using a shared default.
   - Added configurable `SANJEEVANI_CORS_ORIGINS`.

2. **Safety honesty / fail-safe behavior**
   - Removed the misleading `notify_emergency_contact=True` directive because no notification provider is actually implemented.
   - Immediate cases still create a reviewer alert and route to a `realtime_oncall_if_configured` escalation state.
   - Updated the safety unit test to enforce the new invariant.

3. **Frontend account flow**
   - Added registration through the existing login page.
   - Registration automatically signs the user in.
   - Account link from the chat now leads to the combined sign-in/create-account screen.

4. **Privacy UX cleanup**
   - Corrected the export filename and product name typo.
   - Clarified that emergency-contact use is only available when the underlying feature is configured.

## Validation performed

- Python bytecode compilation of backend application and tests: **PASS**.
- Emotion-agent smoke test: **PASS**.
- Safety immediate-pattern smoke test: **PASS**.
- Crypto envelope-encryption round trip: **PASS**.
- Full `pytest` suite: **BLOCKED by environment** — the execution environment has no package-download/network access and the required pinned dependencies were not available locally (`jose`, `passlib`, etc.).
- Full Next.js build/typecheck: **BLOCKED by environment** — `node_modules` could not be installed because the npm registry/cache is unavailable.

## Remaining work before real users

### Critical

- Run the complete backend test suite in a normal development environment with dependencies installed.
- Run a real Postgres integration test and Alembic migration from an empty database.
- Run a full Next.js production build.
- Configure AWS KMS for production encryption; do not use `local_dev` with real data.
- Configure a real, audited human-review/on-call process for high/immediate alerts.
- Clinically review and validate the safety classifier, multilingual coverage, crisis policy, and evaluation set.
- Add rate limiting, abuse protection, security headers, structured logging, monitoring, and secret management before public deployment.

### Important product gaps

- Emergency-contact management/notification is not implemented yet.
- Voice, wearable integration, long-term memory, research workflows, and richer personalization remain preference/data-model scaffolding rather than complete features.
- Conversation history is stored but there is no dedicated history browser yet.
- Reviewer workflow currently supports acknowledgment, not full escalation/resolution workflows.

## Current assessment

**Good MVP scaffold, not production-ready mental-health software.** The core architecture is coherent and the strongest safety invariant—classifier failure must not silently become `low`—is present. The next milestone should be integration testing + production security + clinical safety review rather than adding more cosmetic features.
