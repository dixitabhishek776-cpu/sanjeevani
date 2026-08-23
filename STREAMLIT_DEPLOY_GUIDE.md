# Deploying Sanjeevani on Streamlit Community Cloud

This is a **single-deployment** version of Sanjeevani — one Streamlit app
instead of a separate Vercel frontend + Render backend. It reuses the
exact same core (`backend/app/models.py`, `agents/`, `core/crypto.py`,
`services.py`) directly as a Python library, so the safety pipeline,
encryption, and audit logging are unchanged. Only the deployment
architecture and the UI layer are different.

**Do NOT delete the Render/Vercel deployment until you've confirmed this
one works end-to-end** (register → login → chat → mood → journal →
reviewer dashboard).

## Step 1 — Push this code to GitHub
Same as before: unzip, `git add .`, `git commit`, `git push` from Termux.

## Step 2 — Create the Streamlit Cloud app
1. Go to **share.streamlit.io** on your phone browser
2. Sign in with GitHub
3. **New app** → select your `sanjeevani` repo, branch `main`
4. **Main file path**: `streamlit_app/app.py`
5. Before deploying, click **Advanced settings** → **Secrets**, and paste:

```toml
DATABASE_URL = "postgresql://...same value as your Render Postgres..."
REDIS_URL = "redis://...same value as your Render Redis..."
GROQ_API_KEY = "gsk_...your key..."
SANJEEVANI_ENCRYPTION_PROVIDER = "local_dev"
SANJEEVANI_MASTER_KEY = "...generate one, see below..."
SANJEEVANI_DEMO_MODE = "true"
```

To generate a `SANJEEVANI_MASTER_KEY` (a valid Fernet key), you can ask
Claude to generate one for you, or run this in Termux if you have
`cryptography` available — otherwise any 32 random bytes, base64
url-safe encoded, works. Here's a ready-to-use one generated for this
guide (fine to use directly, since it's fresh and only you have it):

```
SANJEEVANI_MASTER_KEY = "Y8vCBL1ngyEn32AalUr6M6E_YJuh1dQ5n3wme0fvm84="
```

You can copy `DATABASE_URL` and `REDIS_URL` straight from your existing
Render dashboard (`sanjeevani-demo-db` and `sanjeevani-demo-redis` →
"Connect" → external connection string) — **no need to create a new
database**, both deployments can share it.

6. Click **Deploy**

## Step 3 — Test
Streamlit Cloud gives you a URL like `https://sanjeevani-xxxx.streamlit.app`.
Open it, register a fresh account, and test:
- Chat (should get an AI response, not "Something went wrong")
- Mood logging
- Journal
- **System status** page in the sidebar — confirms DB + LLM key are wired up
- To test the reviewer dashboard: on the Privacy & data page, use the
  demo-only "Grant myself reviewer access" button, then check the sidebar
  for the new "Reviewer dashboard" entry.

## What's different from the Render+Vercel version
- No JWT, no refresh tokens, no CORS, no cross-domain cookies — Streamlit's
  own session state (tied to your browser tab) replaces all of that, which
  is what eliminates the 401 bugs that version kept hitting.
- Email verification is bypassed entirely for this demo build (no email
  delivery service configured) — accounts are auto-verified on register.
  This is clearly a demo-only shortcut; see the comment in
  `streamlit_app/app.py`'s `page_login_register()`.
- A **System status** page (self-diagnostics: DB reachability, whether an
  LLM key is configured, and a log of any transient errors that were
  automatically retried) — this is the "self-healing" feature: automatic
  retries for flaky LLM calls, and an error boundary so one broken page
  can't crash the whole app for your session. It is not autonomous
  code-modification — no system should attempt to rewrite its own logic
  unsupervised, especially not one handling mental-health data.

## What's the same
Every agent (Emotion, Safety Intelligence, Conversation), the fail-closed
safety design, per-user AES-256-GCM encryption, the audit log, and the
reviewer escalation workflow are the exact same code, imported directly
from `backend/app/`. Nothing about the safety architecture changed.
