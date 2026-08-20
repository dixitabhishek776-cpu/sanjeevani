# Sanjeevani — Chapter 2: Business, Legal & Ethics

---

## 1. Business Model

**Category:** B2C freemium + B2B2C (organizations pay for seats/dashboards).

| Segment | Model |
|---|---|
| Individual consumers | Freemium: free tier (AI companion, mood/journal, basic reports) + paid tier (long-term memory, voice, advanced analytics, wearables) |
| Universities / Corporates / Hospitals / NGOs | Per-seat or per-org annual licensing, includes admin dashboard, aggregate analytics, therapist integration |
| Therapists (independent) | Subscription to therapist dashboard + client-consented data sharing |

## 2. Revenue Model & Pricing (illustrative — validate with market research before finalizing)

| Tier | Price | Includes |
|---|---|---|
| Free | $0 | AI companion, mood tracking, daily journal, crisis resources |
| Plus | $9.99/mo | Long-term memory, voice conversations, weekly/monthly reports, wellness planner |
| Pro | $19.99/mo | Wearable integration, advanced analytics, priority support |
| Organization | Custom (per-seat, min. commit) | Admin dashboard, aggregate (de-identified) analytics, therapist integration, SLA-backed human review |

**Note:** Safety Intelligence features (crisis resources, human review escalation) are **never** paywalled — available identically on every tier. Gating safety behind payment is a hard no-go, both ethically and from a liability standpoint.

## 3. Go-to-Market Plan

1. **Phase 1 — University partnerships:** universities have existing counseling infrastructure Sanjeevani augments rather than replaces; easier procurement than hospitals, built-in high-need population.
2. **Phase 2 — Corporate wellness:** EAP (Employee Assistance Program) channel partnerships.
3. **Phase 3 — Direct consumer:** app store + content marketing once clinical safety track record is established (credibility matters enormously in this category).
4. **Phase 4 — Healthcare/NGO:** requires HIPAA-level compliance maturity; slowest but highest-trust channel.

## 4. Competitive Analysis (landscape categories, not scored claims about specific current products — verify current market positioning via search before using in an investor deck)

- **AI companion apps** (general emotional support chatbots) — Sanjeevani differentiates on the explicit categorical risk-classification + human-review architecture, not just conversational quality.
- **Clinical teletherapy platforms** — Sanjeevani does not compete here; it's a complementary on-ramp/between-session support layer, positioned to integrate with (not replace) these platforms via the therapist dashboard.
- **Employee wellness platforms** — differentiation is the combination of AI companion + clinically-grounded escalation, vs. content-library-only competitors.

## 5. SWOT

| Strengths | Weaknesses |
|---|---|
| Safety-first architecture is defensible and trust-building | High-risk category — one incident can be existential |
| Multi-agent design allows independent improvement of safety vs. conversation quality | Requires clinical staffing for human review — real operating cost, not just infra |
| B2B2C channel reduces CAC vs. pure consumer app | Regulatory landscape (FDA/SaMD boundary, EU AI Act) is still evolving |

| Opportunities | Threats |
|---|---|
| Growing mental health demand outpacing licensed provider capacity | Regulatory reclassification as a medical device if scope creeps toward diagnosis |
| Underserved population segments (students, shift workers) | Large platform players (Big Tech) entering wellness space |

## 6. Risk Analysis

- **Clinical/liability risk:** mitigated by categorical (not numeric) risk classification, mandatory human review of HIGH/IMMEDIATE, and explicit non-diagnostic framing enforced at the model-output layer.
- **Regulatory risk:** monitor FDA Software as a Medical Device (SaMD) guidance and EU AI Act "high-risk AI system" criteria — if Sanjeevani's marketing or functionality drifts toward diagnosis/treatment claims, it could trigger medical-device regulation. Legal review required before any feature launch that touches diagnostic language.
- **Data breach risk:** mitigated via encryption architecture (Chapter 1 §6) and incident response plan (below).

## 7. Roadmap (business, aligned to technical MVP roadmap in Ch.1 §7)

- **Months 0–3:** MVP build, internal clinical safety review, closed beta with one university partner.
- **Months 3–6:** Beta feedback loop, safety pipeline hardening, therapist dashboard v1.
- **Months 6–12:** Paid consumer tiers launch, 2–3 additional org partnerships.
- **Year 2:** Hospital/NGO channel, wearable integrations, research platform (opt-in).

---

## 8. Legal & Ethics

### Privacy Policy — required disclosures (draft outline, have counsel finalize)
- What data is collected (chat content, mood/journal entries, optional voice/wearable data)
- How Safety Intelligence uses data (explicitly: to classify concern level and route human review — not to build advertising profiles)
- Data retention periods, and user-initiated deletion/export rights
- Third-party processors (LLM provider, cloud host) and data flow to them
- Circumstances under which data may be disclosed without consent (imminent danger to self/others, legal requirement) — **state this clearly and specifically**, since ambiguity here undermines trust

### Terms of Service — required clauses
- Explicit non-diagnostic, non-therapy disclaimer, prominent at signup and periodically re-surfaced
- Crisis resources always accessible regardless of subscription status
- Limitation of liability consistent with "wellness support tool" positioning (have counsel align this with actual product claims — the ToS cannot promise more than the product delivers)

### Consent Management
- Granular, revocable consent per data use: long-term memory, voice analysis, wearable data, research participation, emergency contact notification.
- Consent state stored in `user_preferences` (Ch.1 §4) and changes audit-logged.

### Data Retention
- Chat/journal content: retained per user-configurable policy (default e.g. 24 months), deletable anytime.
- Safety assessments/alerts: retained longer (e.g., 7 years) for clinical/legal audit trail even if user deletes account — **disclose this explicitly**, it's a material exception to "delete my data."

### Applicable Regulations (jurisdiction-dependent — confirm current status with counsel, this space moves)
- GDPR (EU), CCPA/CPRA (California), HIPAA (if/when integrating with covered healthcare entities), FDA SaMD guidance (US), EU AI Act high-risk system provisions if applicable.

### Incident Response Plan (outline)
1. Detection (monitoring, audit log anomalies, user report)
2. Triage & containment (isolate affected systems, revoke compromised credentials)
3. Clinical safety incident escalation path (separate from security incident path — a false-negative crisis classification is an incident even without a breach)
4. Notification (regulatory timelines vary by jurisdiction — e.g., GDPR 72-hour breach notification)
5. Post-incident review feeding back into Safety Agent eval set and security controls

---

*Chapters remaining: (B) Frontend/UX, (C) Deployment & QA.*
