# Deploying Sanjeevani as a Portfolio Demo (Phone-Only Guide)

This deploys a public demo version — NOT a real crisis-support service.
A red banner is already built into the frontend saying so. Emergency-contact
notifications stay off by default; do not set the
`SANJEEVANI_AUTO_EMERGENCY_CONTACT_IMMEDIATE` / `SANJEEVANI_EMERGENCY_CONTACT_POLICY_APPROVED`
env vars, or that safety promise becomes misleading again.

## Step 1 — Push code to GitHub (via Termux)
Follow the Termux steps already covered in chat. Once `git push` succeeds,
your repo is live on GitHub.

## Step 2 — Deploy the backend (Render, free tier)
1. Go to render.com on your phone browser, sign up / log in with GitHub.
2. Click **New +** → **Blueprint**.
3. Select your `sanjeevani` (or `sanjeevani`) repo. Render will detect
   `render.yaml` automatically and propose: 1 web service, 1 Postgres DB,
   1 Redis instance — all free tier.
4. Click **Apply**. It will build and deploy automatically (takes a few minutes).
5. Once live, Render gives you a URL like
   `https://sanjeevani-backend-demo.onrender.com` — copy this, you'll need it
   in Step 3.

Note: Render's free tier spins down when idle and wakes on the next request
(30-60 sec cold start). That's expected and fine for a demo link.

## Step 3 — Deploy the frontend (Vercel, free tier)
1. Go to vercel.com on your phone browser, sign up / log in with GitHub.
2. Click **Add New** → **Project**, select the same repo.
3. Set **Root Directory** to `frontend`.
4. Add an environment variable:
   - `NEXT_PUBLIC_API_URL` = the Render backend URL from Step 2
5. Click **Deploy**. Vercel gives you a public link like
   `https://sanjeevani-demo.vercel.app` — this is your shareable demo link.

## Step 4 — Sanity check before sharing the link
- [ ] Red demo banner is visible on every page
- [ ] Register a test account, send a test chat message, confirm it responds
- [ ] Confirm no real emergency-contact env vars were set
- [ ] Do NOT put real personal crisis content into the demo — it's for
      showing the UI/architecture, not real use

## What to say about it on LinkedIn / resume
Call it a "live portfolio demo," not a "launched product." Example line:
"Live demo: [link] — student engineering project, not a certified
mental-health service."
