# Sanjeevani — Launch Candidate V15

Sanjeevani is an AI-assisted mental-wellness platform designed around privacy, evidence-based self-help, safety routing and human escalation.

## Architecture

- Next.js/React web application
- FastAPI backend
- PostgreSQL system of record
- Redis for rate limiting/coordination
- envelope encryption for sensitive user data
- durable notification worker
- deterministic + LLM-assisted safety pipeline
- user-controlled long-term memory
- reviewed intervention catalog
- audit and privacy/export/deletion controls

## Run development

See `backend/README.md` and `frontend/README.md`.

## Staging

Copy `.env.staging.example`, provide non-production secrets, then:

`docker compose -f docker-compose.staging.yml up --build`

Run:

`bash scripts/staging_smoke.sh`

## Security checks

`python scripts/secret_scan.py`

`python scripts/release_check.py`

`python -m pytest backend/tests -q`

## Safety evaluation

`cd backend && python -m app.eval_safety_agent`

Automated evaluation is not clinical validation.

## Public launch gate

`python scripts/launch_gate.py`

The command intentionally blocks public launch until external clinical, security, legal, human-escalation, recovery and connected-staging evidence has been recorded.

## Current release status

**Engineering launch candidate. Not self-certified for public mental-health use.**

See:

- `docs/V12_SECURITY_AND_RELIABILITY.md`
- `docs/V13_CLINICAL_AND_MULTILINGUAL_EVALUATION.md`
- `docs/V14_PRODUCTION_ARCHITECTURE.md`
- `docs/V15_BETA_AND_PUBLIC_LAUNCH.md`
- `docs/THREAT_MODEL.md`
- `RELEASE_EVIDENCE.md`
