# Sanjeevani — AI Mental Wellness Operating System
## Chapter 1: Foundation Blueprint (Safety, AI Architecture, Data, Core APIs)

> Scope note: This chapter covers the load-bearing systems — the ones every other chapter (UI, business model, deployment) depends on. Subsequent chapters (Business & Legal, Frontend/UX, Deployment/QA) will build on this without contradicting it.

---

## 1. Product Philosophy (Operationalized)

These aren't slogans — each maps to a concrete engineering constraint:

| Principle | Engineering Consequence |
|---|---|
| Safety Before Intelligence | Every message passes through the Safety Agent *before* the Conversation Agent's reply is released to the user. Safety is a gate, not a feature. |
| Human First | High/Immediate risk classifications always route to a human reviewer or crisis resource — the AI never "handles" a crisis alone. |
| Explainable AI | Every safety classification stores the contributing signals (not a black-box score) in `safety_assessments.explanation`. |
| Privacy by Design | Field-level encryption on all emotional/clinical data; user-controlled data export/delete (GDPR/CCPA compliant) from day one. |
| No Diagnosis, No Therapist Framing | System prompts for the Conversation Agent hard-block diagnostic language; enforced by a post-generation classifier, not just prompting. |
| User Control | Long-term memory, wearable integration, and research participation are all opt-in, reversible, and independently toggleable. |

**Hard product constraint:** Sanjeevani classifies concern level as **Low / Moderate / High / Immediate** — never a numeric suicide-risk probability. Numeric scores create false precision and legal/clinical liability; categorical bands map cleanly to defined response protocols.

---

## 2. Safety Intelligence Architecture

This is the system's most important subsystem. Design it first, test it hardest.

### 2.1 Risk Classification Pipeline

```
User Message
     │
     ▼
[1] Pre-filter (regex/keyword, <5ms)  ──► catches explicit crisis language instantly
     │
     ▼
[2] Emotion Analysis Agent  ──► sentiment, affect intensity, trend vs. baseline
     │
     ▼
[3] Safety Intelligence Agent (LLM-based classifier)
     │    Inputs: current message, emotion signals, last 30 days of mood/journal
     │            trend, prior safety assessments, conversation memory
     │    Output: { concern_level, contributing_factors[], confidence,
     │              recommended_action, explanation }
     ▼
[4] Decision Router
     ├─ LOW       → normal AI Companion response, log only
     ├─ MODERATE  → AI responds with grounding/coping content +
     │              gentle nudge toward resources; flagged for async human audit
     ├─ HIGH      → AI responds with stabilizing, non-judgmental message +
     │              crisis resources surfaced in-app immediately +
     │              real-time alert to human reviewer queue (SLA: minutes)
     └─ IMMEDIATE → Crisis resources shown FIRST, before any AI-generated reply +
                    immediate human escalation (on-call clinical reviewer) +
                    opt-in emergency contact notification triggered +
                    conversation flagged, audit-logged, never auto-closed
```

### 2.2 Why a Multi-Stage Pipeline (not a single LLM call)

- **Latency & reliability:** the regex pre-filter guarantees crisis phrases are never missed due to an LLM timeout or hallucinated leniency.
- **Defense in depth:** a single classifier failure mode (e.g., an adversarial or sarcastic phrasing) doesn't leave the user unprotected — three independent signals must agree to suppress escalation.
- **Auditability:** each stage's output is logged separately, so a clinical reviewer can reconstruct *why* the system responded as it did.

### 2.3 Human Review Workflow

- Every HIGH/IMMEDIATE classification creates a record in `alerts` with status `pending_review`.
- Reviewers (licensed clinical staff, contracted or in-house) see a redacted-by-default case view; can request full context with audit-logged justification.
- Reviewer actions: acknowledge, escalate to emergency services, contact user (if consented), close with notes.
- **No auto-resolution:** IMMEDIATE alerts cannot be closed by the system; only a human reviewer can close them.
- All reviewer actions are immutably audit-logged (`audit_logs`), including timestamps and identity, for compliance and QA.

### 2.4 Failure-Handling Strategy

| Failure | Mitigation |
|---|---|
| Safety Agent LLM call times out / errors | Fail closed to MODERATE minimum + surface crisis resources link; never fail silently to LOW |
| Classifier disagrees with pre-filter | Escalate to higher of the two classifications automatically |
| Human reviewer queue backlog | Auto-escalate unacknowledged HIGH alerts to IMMEDIATE protocol after SLA breach (e.g., 10 min) |
| Model drift / false negatives discovered in audit | Weekly clinical safety review (see Testing chapter) feeds relabeled examples back into eval set, not directly into production without review |

---

## 3. AI Multi-Agent Architecture

```
                         ┌─────────────────────┐
                         │   API Gateway        │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    │        Orchestration Layer       │
                    │   (routes to agents, manages     │
                    │    conversation state via Redis) │
                    └───┬─────┬─────┬─────┬─────┬─────┘
                        │     │     │     │     │
            ┌───────────┘     │     │     │     └───────────┐
            ▼                 ▼     ▼     ▼                 ▼
    ┌───────────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────┐
    │ Conversation   │ │  Emotion   │ │  Memory  │ │   Safety     │
    │ Agent          │ │  Analysis  │ │  Agent   │ │   Intel.     │
    │                │ │  Agent     │ │          │ │   Agent      │
    └───────┬────────┘ └─────┬──────┘ └────┬─────┘ └──────┬───────┘
            │                │             │              │
            ▼                ▼             ▼              ▼
    ┌────────────────────────────────────────────────────────────┐
    │  Shared Services: Vector DB (memory/embeddings) · Postgres  │
    │  · Recommendation Engine · Planning Agent · Personality     │
    │  Engine · Explainability Engine · Learning Engine ·         │
    │  Report Generator · Analytics Engine                        │
    └────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities & Interfaces

**Conversation Agent**
- Responsibility: generates empathetic, non-clinical dialogue; personality-consistent tone via Personality Engine.
- Interface: `generate_response(user_msg, conversation_context, safety_directive) → response_text`
- Constraint: `safety_directive` (from Safety Agent) can override tone/content (e.g., force resource-surfacing) — Conversation Agent cannot bypass it.
- Failure handling: on LLM error, return a pre-approved static empathetic fallback, never an empty/broken reply.

**Emotion Analysis Agent**
- Responsibility: real-time sentiment/affect extraction from text (and optionally voice); maintains rolling emotion baseline per user.
- Interface: `analyze(message, modality) → { valence, arousal, primary_emotion, deviation_from_baseline }`
- Failure handling: degrade to text-only sentiment if voice model unavailable; never block the conversation pipeline.

**Memory Agent**
- Responsibility: manages short-term (session) and optional long-term memory; writes/reads the knowledge graph and vector store.
- Interface: `retrieve_context(user_id, query) → memory_snippets[]`; `write_memory(user_id, fact, ttl?)`
- Constraint: long-term memory is opt-in per `user_preferences.long_term_memory_enabled`; if disabled, only session-scoped memory (Redis, cleared on session end) is used.

**Safety Intelligence Agent**
- Responsibility: as described in Section 2. Highest-priority agent — has veto power over Conversation Agent output.
- Interface: `assess(message, emotion_signals, history) → SafetyAssessment`
- Failure handling: fail-closed (see 2.4).

**Recommendation Engine**
- Responsibility: suggests coping strategies, habits, content based on current state + goals. Evidence-informed content library, not generative clinical advice.
- Interface: `recommend(user_state, goals) → recommendation[]`

**Planning Agent**
- Responsibility: builds/adjusts the AI Wellness Planner (habits, goals, check-in cadence).

**Personality Engine**
- Responsibility: maintains a consistent, configurable companion tone/persona across sessions.

**Learning Engine**
- Responsibility: personalizes recommendation weighting over time from explicit feedback (thumbs up/down, goal completion) — not from inferred clinical state.

**Explainability Engine**
- Responsibility: converts internal agent signals into human-readable explanations for both users ("Why am I seeing this resource?") and reviewers ("Why was this flagged HIGH?").

**Report Generator / Analytics Engine**
- Responsibility: weekly/monthly personal reports; aggregate, de-identified analytics for org dashboards.

---

## 4. Core Database Schema (PostgreSQL)

Core tables only (full schema with indexes/migrations belongs in the Database chapter). PII and clinical fields are encrypted at column level (see Security section).

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now(),
    role VARCHAR(20) NOT NULL DEFAULT 'user', -- user, therapist, org_admin, reviewer, super_admin
    org_id UUID REFERENCES organizations(id),
    deleted_at TIMESTAMPTZ -- soft delete for GDPR-compliant erasure workflow
);

CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    long_term_memory_enabled BOOLEAN DEFAULT false,
    voice_emotion_enabled BOOLEAN DEFAULT false,
    wearable_integration_enabled BOOLEAN DEFAULT false,
    research_participation_opt_in BOOLEAN DEFAULT false,
    emergency_contacts_enabled BOOLEAN DEFAULT false,
    notification_settings JSONB DEFAULT '{}'
);

CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    sender VARCHAR(10) NOT NULL, -- 'user' | 'ai'
    content_encrypted BYTEA NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE mood_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    mood_score SMALLINT CHECK (mood_score BETWEEN 1 AND 10),
    tags TEXT[],
    note_encrypted BYTEA,
    logged_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE journals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content_encrypted BYTEA NOT NULL,
    prompt_used TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE safety_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id),
    concern_level VARCHAR(10) NOT NULL CHECK (concern_level IN ('low','moderate','high','immediate')),
    contributing_factors JSONB NOT NULL,
    explanation TEXT NOT NULL,
    confidence NUMERIC(4,3),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    safety_assessment_id UUID REFERENCES safety_assessments(id),
    status VARCHAR(20) DEFAULT 'pending_review', -- pending_review, acknowledged, escalated, closed
    assigned_reviewer_id UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    resolution_notes_encrypted BYTEA
);

CREATE TABLE emergency_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100),
    phone_encrypted BYTEA,
    relationship VARCHAR(50),
    consent_given_at TIMESTAMPTZ
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id UUID,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE habits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(150),
    cadence VARCHAR(20), -- daily, weekly, custom
    streak_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(150),
    status VARCHAR(20) DEFAULT 'active',
    target_date DATE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    type VARCHAR(30) -- university, corporate, hospital, ngo
);
```

**Indexing strategy (highlights):** `mood_entries(user_id, logged_at)`, `messages(chat_id, created_at)`, `safety_assessments(user_id, concern_level, created_at)`, `alerts(status, safety_assessment_id)` — the last one is critical for reviewer-queue query performance under load.

**Encryption:** all `*_encrypted` columns use application-layer AES-256-GCM with per-user data encryption keys (DEKs), themselves wrapped by a KMS-managed master key (AWS KMS). This means a database breach alone does not expose plaintext emotional/clinical content.

---

## 5. Core API Design (illustrative)

**POST `/v1/chat/message`**
```json
// Request
{ "chat_id": "uuid", "content": "I've been feeling really overwhelmed lately" }

// Response
{
  "message_id": "uuid",
  "ai_response": "That sounds heavy to carry. Want to tell me more about what's been going on?",
  "safety": {
    "concern_level": "low",
    "resources_shown": false
  }
}
```

**GET `/v1/safety/alerts?status=pending_review`** *(reviewer role only, RBAC-enforced)*
```json
{
  "alerts": [
    {
      "alert_id": "uuid",
      "user_ref": "pseudonymized-id",
      "concern_level": "high",
      "created_at": "2026-07-29T10:12:00Z",
      "explanation": "Sharp deviation from 30-day emotional baseline; language indicating hopelessness without explicit crisis phrasing."
    }
  ]
}
```

**POST `/v1/mood`**
```json
{ "mood_score": 4, "tags": ["anxious", "tired"], "note": "rough day at work" }
```

All endpoints: JWT bearer auth, RBAC middleware, rate-limited (per-user + per-IP), request/response schema-validated (Pydantic), and every write to clinical/safety tables triggers an `audit_logs` entry automatically at the ORM layer (not left to individual endpoint authors to remember).

---

## 6. Security Baseline (MVP-required, not optional)

- TLS 1.3 everywhere; HSTS.
- Column-level encryption for all emotional/clinical content (Section 4).
- RBAC with least-privilege roles: `user`, `therapist`, `org_admin`, `reviewer`, `super_admin`.
- MFA required for `reviewer`, `org_admin`, `super_admin` roles.
- Secrets in AWS Secrets Manager, never in env files committed to source control.
- All safety/reviewer actions immutably audit-logged.
- Data export & right-to-erasure endpoints from day one (GDPR/CCPA).

---

## 7. MVP Roadmap (build order)

1. Auth + user model + RBAC
2. Chat pipeline with Safety Agent gating (fail-closed) — **ship nothing without this**
3. Mood tracking + journaling
4. Reviewer dashboard for HIGH/IMMEDIATE alerts
5. Emotion Analysis Agent + baseline tracking
6. Memory Agent (session-scoped first, long-term opt-in later)
7. Recommendation Engine + Wellness Planner
8. Weekly/monthly reports
9. Org/therapist dashboards
10. Voice, wearables, research platform (post-MVP)

---

*Next chapters available on request: (A) Business & Legal — pricing, GTM, privacy policy, ToS; (B) Frontend/UX — full screen inventory, design system, user flows; (C) Deployment & QA — Kubernetes topology, CI/CD, clinical safety testing protocol.*
