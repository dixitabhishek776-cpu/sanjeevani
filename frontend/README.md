# Sanjeevani Frontend (scaffold)

Next.js app implementing the calm companion chat flow from Chapter 3:
persistent crisis-resource access, resources-shown-first behavior on
elevated concern levels, and the muted design system tokens.

## Run locally

```bash
npm install
npm run dev
```

Set the backend URL if not on the default:

```bash
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local
```

## What's here vs. what's next

- `/` — chat interface (functional against the backend `/v1/chat/message` endpoint)
- `/login` — email/password sign-in, stores the JWT in localStorage
- `/mood` — log mood (score + tags + note) and see a simple bar-chart timeline of your last 30 entries
- `/journal` — write and browse encrypted journal entries, with rotating reflection prompts
- `/privacy` — consent toggles (all off by default), one-click data export as JSON, and account deletion with a confirmation step
- `/reviewer` — safety alert queue dashboard: view pending/acknowledged alerts sorted by urgency, acknowledge them, auto-refreshes every 20s. Requires a `reviewer` or `super_admin` role account (see backend README for how to grant this).
- `/crisis-resources` — static, backend-independent page (Ch.4 requirement)

Weekly summary, goals/habits APIs and reviewer safety dashboard are available; therapist/organization administration remains a post-beta product surface.
