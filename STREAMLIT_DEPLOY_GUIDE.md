# Deploying Sanjeevani on Streamlit Community Cloud

Sanjeevani runs as **one Streamlit app** (`streamlit_app/app.py`). It uses the
code in `backend/app/` (models, safety agents, encryption, email) directly as a
Python library, so there is no separate API server to deploy.

## What you need (all have free tiers)

| Service | Used for |
| --- | --- |
| GitHub | Hosts the code; Streamlit Cloud deploys from it; runs the daily reminder job |
| Neon (Postgres) | The database |
| Streamlit Community Cloud | Runs the app |
| Groq (and optionally Gemini / Anthropic) | AI replies and the safety classifier |
| Resend | Verification and alert emails |
| Redis (optional, e.g. Upstash free tier) | Shared rate limiting (see below) |

## 1. Create the database tables (once)

1. In GitHub open **Settings, Secrets and variables, Actions** and add a secret
   `DATABASE_URL` (your Neon connection string, starting with `postgresql://`).
2. Open the **Actions** tab, choose **Initialize Database Schema**, press **Run workflow**.

It runs `scripts/init_db.py` and is safe to run again.

## 2. Create the Streamlit app

1. Go to share.streamlit.io, sign in with GitHub, choose **New app**.
2. Repository `sanjeevani`, branch `main`, main file `streamlit_app/app.py`.
3. Under **Advanced settings, Secrets** paste (replace every value):

```toml
DATABASE_URL = "postgresql://user:pass@host/db?sslmode=require"
SANJEEVANI_ENV = "production"
SANJEEVANI_ENCRYPTION_PROVIDER = "local_dev"
SANJEEVANI_MASTER_KEY = "generate-your-own-see-below"
SANJEEVANI_JWT_SECRET = "random-text"
SANJEEVANI_APP_URL = "https://your-app.streamlit.app"
GROQ_API_KEY = "gsk_xxx"
RESEND_API_KEY = "re_xxx"
SANJEEVANI_ADMIN_EMAIL = "you@example.com"
# Optional
# GEMINI_API_KEY = "xxx"
# ANTHROPIC_API_KEY = "xxx"
# REDIS_URL = "rediss://..."
# SANJEEVANI_REQUIRE_EMAIL_VERIFICATION = "true"
```

Generate the master key on any machine with Python and `cryptography`:

```
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Never commit it or paste it anywhere public. It protects every user's data
key, and **if you lose it, existing journal and chat entries cannot be read**.

## 3. Behaviour you should know about

- **Email verification.** When `RESEND_API_KEY` is set, a new account must verify
  its email before using the app (helplines stay visible on that screen).
  Without a Resend key the app lets unverified users in, with a banner. Set
  `SANJEEVANI_REQUIRE_EMAIL_VERIFICATION` to `true` or `false` to override.
- **Sign-up.** Requires confirming age 18+ and agreeing to the Terms. Passwords
  need 12+ characters and must not be common, simple, or contain the email name.
- **Stay signed in.** The "Keep me signed in" box on login stores a random token
  (only its hash is kept in the database) in a browser cookie for 14 days.
  Signing out, changing the password, or deleting the account revokes it.
- **Deleting an account** shreds the user's encryption key, removes the email
  and name, and frees the email address for a new sign-up.
- **Rate limiting.** Without `REDIS_URL` counters live in memory and reset when
  the app restarts. Account lockout after 5 wrong passwords is stored in the
  database and is not affected. Add a free Redis URL for shared limits.
- **If the AI provider is down** the safety check fails closed: the reply shows
  the helplines, and no reviewer alert is created for the outage itself.

## 4. Daily reminder emails

`.github/workflows/daily-reminder.yml` runs every day at 13:00 UTC. It needs two
GitHub Actions secrets: `DATABASE_URL` and `RESEND_API_KEY`. Test it with
**Run workflow**; a red run means one of them is missing or wrong.

## 5. Operator tasks (from a terminal, not in the app)

Grant the reviewer role (to see the Reviewer dashboard):

```
DATABASE_URL=... python3 scripts/grant_role.py someone@example.com reviewer
```

Rotate the master key without losing data (dry run first, then `--apply`):

```
DATABASE_URL=... OLD_MASTER_KEY=... NEW_MASTER_KEY=... python3 scripts/rotate_master_key.py
```

Then set the new key as `SANJEEVANI_MASTER_KEY` in Streamlit secrets and reboot.
Rotate the key straight away if it was ever committed, pasted in a chat or
posted anywhere. Removing a key from a file does not remove it from git history.

## 6. First-run checklist

1. Open the app, tick the 18+ and Terms boxes, create an account.
2. Open the verification email and click the link.
3. Sign in and send a chat message. If the reply is the "having trouble" text,
   check `GROQ_API_KEY`, then the **System status** page.
4. Log a mood and a journal entry, then refresh the page: you should stay signed in.
5. Sign out and confirm you land on the welcome screen.

## What is the same as the older Render and Vercel setup

The agents (Emotion, Safety, Conversation), the fail-closed safety design,
per-user encryption, the audit log and the reviewer workflow are the same code
in `backend/app/`. The Render configuration was removed because the Streamlit
app replaced it.
