# Sanjeevani — Chapter 3: Frontend, UX & Design System

---

## 1. Design Principles

- **Calm by default:** low-stimulation visuals, generous whitespace, no red/urgent colors except in genuine crisis-resource surfacing (where urgency should read as clear, not alarming).
- **Never gamify distress:** streaks/achievements apply to habits and journaling, never to "days without a crisis" — that framing punishes relapse.
- **One primary action per screen** — reduce decision load for users who may be in distress.

## 2. Design System

| Token | Values |
|---|---|
| Typography | Humanist sans-serif (e.g., Inter or similar), min 16px body, generous line-height (1.6) for readability under stress |
| Color palette | Muted, low-saturation base (soft blues/greens); a single reserved "resource" accent color used *only* for crisis/safety surfaces so it's instantly recognizable |
| Spacing | 8px base grid |
| Dark mode | Full parity, not an afterthought — many users journal at night |
| Motion | Subtle, slow easing (300–400ms); no bouncy/playful motion on safety-related UI |
| Accessibility | WCAG 2.2 AA minimum; full screen-reader support on crisis resource flows especially |

## 3. Core Screens (Web + Mobile, React Native shares logic via shared TypeScript core)

**Onboarding**
- Welcome → non-diagnostic disclaimer (explicit, plain-language, not buried in ToS) → consent choices (memory, voice, wearables — all off by default) → optional emergency contact setup

**Home / Companion**
- Chat interface (primary), mood check-in prompt, quick-access to crisis resources (always visible, not hidden in a menu)

**Journal**
- Daily entry, prompt suggestions, entry history/timeline

**Mood & Emotion Timeline**
- Simple 1–10 log + tags; timeline visualization (line chart) with baseline overlay

**Wellness Planner**
- Habits, goals, meditation assistant, sleep tracking — modular cards, user can hide any they don't use

**Reports**
- Weekly/monthly summary; explicitly framed as reflection, not assessment ("Here's what we noticed" not "Your score is...")

**Privacy Dashboard**
- One place to see and toggle every consent setting, view what data exists, export or delete

**Crisis Resources (persistent, reachable from every screen)**
- Never more than one tap away; works offline (cached static content)

**Therapist/Org Dashboards** (separate app surface, RBAC-gated)
- Reviewer alert queue, aggregate (de-identified) analytics, audit log viewer

## 4. Key User Flows

**Crisis flow (highest-priority flow to design and test):**
```
User message → Safety Agent HIGH/IMMEDIATE
   → Resources screen shown immediately (before/alongside AI text response)
   → Clear, unambiguous next steps (hotline numbers, "talk to someone now")
   → No dead ends — always a visible path back to conversation
   → If emergency contacts enabled: confirmation shown that contact was notified
```

**Standard companion flow:**
```
Open app → Home → optional mood check-in → chat → 
   (Recommendation Engine surfaces coping content contextually, dismissible)
```

## 5. State Management & Offline

- Web: React Query for server state, minimal global client state (avoid over-centralizing).
- Mobile: same data layer shared via TypeScript core package; offline queue for journal/mood entries (sync on reconnect); crisis resources bundled locally so they render with zero network dependency.
- Conversation history cached locally, encrypted at rest on-device.

## 6. Performance & Accessibility Testing Requirements

- All screens keyboard-navigable; crisis resource screen tested with screen readers as a release-blocking check.
- Performance budget: chat response render <200ms after API returns; cold start <2s.

---

*Chapter remaining: (C) Deployment & QA.*
