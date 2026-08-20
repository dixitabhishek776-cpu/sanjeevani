# Sanjeevani Backend (scaffold)

FastAPI implementation of the architecture in Chapter 1 of the blueprint:
auth, the multi-agent chat/safety pipeline, mood tracking, and the
reviewer alert queue.

## What's real vs. stubbed

**Real / functional:**
- Full request → Emotion Agent → Safety Agent → Decision Router → Conversation Agent pipeline, wired end-to-end
- Fail-closed behavior (classifier errors route to "moderate", never silently to "low")
- RBAC-gated reviewer endpoints, audit logging on every safety-relevant write
- Field-level encryption of message/journal/mood content
- DB schema matching Chapter 1 exactly (SQLAlchemy models)
- **The Conversation Agent now calls a real LLM** (Claude, via the Anthropic
  API) with a hard-enforced non-diagnostic system prompt
- **The Safety Agent now has a real LLM classification stage**, layered
  under the keyword pre-filter (which still runs first and can't be
  overridden — see `app/agents/safety_agent.py` docstring)
- A runnable regression eval (`app/eval_safety_agent.py`) — a fixed set of
  test messages you can check the classifier against before deploying any change

- **Per-user envelope encryption with a real, pluggable KMS backend.**
  Each user gets a randomly-generated 256-bit DEK, used directly for
  AES-256-GCM content encryption. The DEK is wrapped by a Master Key via
  `app/core/master_key_provider.py`, which has two real implementations:
  `LocalDevMasterKeyProvider` (dev only, key in an env var) and
  `AWSKMSMasterKeyProvider` (production — wraps/unwraps DEKs through a
  real AWS KMS Customer Master Key; the master key material never leaves
  AWS KMS). Switching between them is one env var
  (`SANJEEVANI_ENCRYPTION_PROVIDER`), not a code change. See "Set up
  encryption" below.
- **A reviewer dashboard now exists** at `frontend/app/reviewer` — talks
  to the `/v1/safety/alerts` endpoints already in this backend
- **Journal endpoints** (`/v1/journals`) — were missing before; the
  `Journal` model existed but had no API surface. Now has create/list/delete.
- **Privacy dashboard endpoints** (`/v1/privacy/*`) — consent preference
  toggles, full data export (GDPR/CCPA-style), and account deletion with
  crypto-shredding (revokes the user's DEK so ciphertext becomes
  permanently unreadable, per Ch.2 Sec.8)
- **Alembic migrations** — schema is now version-controlled
  (`alembic/versions/0001_initial.py` mirrors `models.py` exactly). Run
  `alembic upgrade head` before starting the app; Docker Compose does
  this automatically now.

**Still stubbed / needs real-world work before any real use:**
- The LLM classifier is a strong heuristic, not a clinically-validated
  model — it still needs the human-review workflow behind it, and ideally
  clinical review of its prompt and eval results (Ch.4's Clinical Safety
  Review process)
- The keyword pre-filter (Stage 1 of the Safety Agent) is English-only —
  crisis language in other languages relies entirely on the LLM
  classification stage, with a fail-safe keyword layer underneath it

### Set up encryption

**Local development (default, no setup needed):**
Leave `SANJEEVANI_ENCRYPTION_PROVIDER` unset or `local_dev` in your
`.env`. The app will generate a key automatically. You'll see a warning
in the logs — that's intentional, so this mode is never accidentally
mistaken for production-ready.

**Real deployment (AWS KMS):**
1. Create a symmetric KMS Customer Master Key in the AWS Console (or via Terraform), usage type `ENCRYPT_DECRYPT`
2. Attach a key policy granting your app's IAM role `kms:Encrypt` and `kms:Decrypt` on that key (no `kms:GenerateDataKey` needed — DEKs are generated locally)
3. In `.env`:
   ```
   SANJEEVANI_ENCRYPTION_PROVIDER=aws_kms
   SANJEEVANI_KMS_KEY_ID=arn:aws:kms:us-east-1:XXXXXXXXXXXX:key/your-key-id
   AWS_REGION=us-east-1
   ```
4. Provide AWS credentials the normal way (IAM role in production; `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` env vars for local testing against a real key)
5. `pip install -r requirements.txt` (now includes `boto3`)

Existing users' data encrypted under the local dev key will NOT be
readable after switching providers — this switch is meant for before
real data exists, not as a live migration. A real migration would need
to decrypt under the old provider and re-encrypt under the new one,
which isn't implemented here.

### Test the KMS integration without a real AWS account

```bash
cd backend
pytest tests/test_master_key_provider.py -v
```

The AWS KMS tests mock `boto3` entirely — they verify the integration
code calls the right KMS APIs with the right arguments, without needing
real AWS credentials. They do NOT verify your actual KMS key policy is
configured correctly — do one real end-to-end test against a real
(even sandbox) AWS account before trusting this in production.

### Run migrations manually (if not using Docker)

```bash
cd backend
alembic upgrade head
```

### Grant yourself reviewer access (to test the dashboard)

Register/log in normally via `/v1/auth/register`, then manually update
that user's role in the database:

```sql
UPDATE users SET role = 'reviewer' WHERE email = 'you@example.com';
```

Then sign in at `/login` in the frontend and visit `/reviewer`.

### Set up your API key (required for chat to work)

1. Get a key at [console.anthropic.com](https://console.anthropic.com) — this is a *developer* account, separate from your normal claude.ai login, and requires adding billing (pay-per-use, quite cheap for testing)
2. Copy `.env.example` to `.env`
3. Paste your key into `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
4. If using Docker: set the same variable in your shell before `docker compose up` (or put it in a `.env` file at the project root — Docker Compose reads it automatically)

### Run the safety eval

```bash
cd backend
python -m app.eval_safety_agent
```

Run this after any change to `safety_agent.py` — it's a fast automated
sanity check, not a substitute for clinical review.

### Run the unit test suite

```bash
cd backend
pip install -r requirements.txt
pytest
```

Covers: emotion analysis logic, the safety pre-filter (verified to never
call the LLM when it short-circuits), fail-closed behavior under
simulated LLM errors and malformed output, the decision router's
escalation mapping, conversation fallback behavior, and the envelope
encryption roundtrip (including that one user's DEK cannot decrypt
another user's data). None of these tests require a real Anthropic API
key or a running database — LLM calls and DB access are not exercised by
this suite (see "What this doesn't test" below).

**What this doesn't test:** the actual HTTP API layer (FastAPI routes),
real database behavior, or real LLM output quality. Those need
integration tests against a running Postgres instance and a real API
key — a reasonable next addition, using `TestClient` from `fastapi` and
either a disposable test database or `docker compose`.

## Run locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# needs a running Postgres; e.g.:
# docker run -e POSTGRES_USER=sanjeevani -e POSTGRES_PASSWORD=sanjeevani \
#   -e POSTGRES_DB=sanjeevani -p 5432:5432 -d postgres:16

export DATABASE_URL=postgresql://sanjeevani:sanjeevani@localhost:5432/sanjeevani
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs.

## Try the safety pipeline

```bash
# register + login
curl -X POST localhost:8000/v1/auth/register -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
curl -X POST localhost:8000/v1/auth/login \
  -d "username=test@example.com&password=password123"

# send a message (use the access_token from above)
curl -X POST localhost:8000/v1/chat/message \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"content":"I have been feeling really overwhelmed lately"}'
```

To grant reviewer access for testing the alert queue, manually set a
user's `role` column to `reviewer` in the database.
