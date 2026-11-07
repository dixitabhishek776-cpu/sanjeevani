# Sanjeevani

An AI-assisted mental wellness companion for college students: private chat in
8 languages, mood tracking, an encrypted journal, PHQ-9 and GAD-7 check-ins,
trusted contacts, and a safety pipeline that always keeps helplines in reach.
It is a self-help tool, not therapy or medical care.

## What runs where

| Part | Folder | Status |
| --- | --- | --- |
| **Streamlit app** (the live product) | `streamlit_app/` | Deployed on Streamlit Community Cloud |
| Core library (models, safety agents, encryption, email) | `backend/app/` | Used directly by the Streamlit app |
| REST API (FastAPI) | `backend/app/main.py`, `backend/app/routers/` | Optional, not part of the Streamlit deployment |
| Next.js site | `frontend/` | Optional, not the live product |
| Operator scripts | `scripts/` | Database init, daily reminders, key rotation, role grants |

## Safety design in one paragraph

Every chat message passes a safety check before a reply is shown: crisis
phrases are matched first, then an AI classifier. If the classifier is
unavailable the system fails closed (helplines are shown with the reply and no
reviewer alert is created for the outage). High and immediate cases create a
reviewer alert. Journals, chats and notes are encrypted with a key per user.

## Deploy

Follow `STREAMLIT_DEPLOY_GUIDE.md`.

## Develop and test

```
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements.txt -r streamlit_app/requirements.txt
export DATABASE_URL=postgresql://user:pass@localhost:5432/sanjeevani_test
export SANJEEVANI_ENV=test SANJEEVANI_JWT_SECRET=test-only
export SANJEEVANI_MASTER_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
(cd backend && alembic upgrade head)
pytest backend/tests          # backend, safety rules and the Streamlit app (AppTest)
streamlit run streamlit_app/app.py
```

## Operator tasks

- `python scripts/grant_role.py EMAIL reviewer` gives the reviewer role.
- `python scripts/rotate_master_key.py` rotates the master key without data loss.
- `python scripts/secret_scan.py` checks the repository for committed secrets.

## More documentation

- `SECURITY.md` for reporting vulnerabilities.
- `docs/` for the threat model, data governance, incident response and safety evaluation notes.
- `backend/README.md` for the API and the encryption design.
