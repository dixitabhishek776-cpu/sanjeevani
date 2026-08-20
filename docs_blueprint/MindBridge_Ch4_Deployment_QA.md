# Sanjeevani — Chapter 4: Deployment, Infrastructure & QA

---

## 1. Infrastructure Overview

```
                 ┌────────────────────┐
                 │   Route 53 / CDN    │
                 └─────────┬──────────┘
                           ▼
                 ┌────────────────────┐
                 │  ALB (TLS term.)    │
                 └─────────┬──────────┘
                           ▼
        ┌──────────────────────────────────┐
        │     EKS (Kubernetes) Cluster       │
        │  ┌────────────┐  ┌──────────────┐ │
        │  │ API Gateway │  │ Agent Services│ │
        │  │  (FastAPI)  │  │ (Conversation,│ │
        │  │             │  │ Safety, etc.) │ │
        │  └────────────┘  └──────────────┘ │
        │  ┌────────────┐  ┌──────────────┐ │
        │  │ Celery      │  │ WebSocket     │ │
        │  │ Workers     │  │ Gateway       │ │
        │  └────────────┘  └──────────────┘ │
        └───────┬─────────────┬─────────────┘
                ▼             ▼
      ┌──────────────┐  ┌──────────────┐
      │ RDS Postgres  │  │ ElastiCache  │
      │ (Multi-AZ)    │  │ (Redis)      │
      └──────────────┘  └──────────────┘
                ▼
      ┌──────────────┐  ┌──────────────┐
      │ Vector DB      │  │ RabbitMQ     │
      │ (managed)      │  │ (queues)     │
      └──────────────┘  └──────────────┘
```

- **Compute:** EKS, separate node pools for latency-sensitive Safety Agent services vs. batch/report-generation workloads.
- **Data:** RDS Postgres Multi-AZ with automated backups + point-in-time recovery; Redis for session/cache; managed vector DB for embeddings/memory.
- **IaC:** Terraform for all infra, versioned, PR-reviewed; no manual console changes to production.
- **Secrets:** AWS Secrets Manager, injected via Kubernetes External Secrets Operator — never baked into images.

## 2. CI/CD

```
PR opened → lint + unit tests → security scan (SAST, dependency audit)
   → build image → deploy to staging → integration + safety-eval suite (blocking)
   → manual approval gate for production → canary deploy (5% traffic)
   → automated rollback on error-rate/latency SLO breach → full rollout
```

- **Safety-eval suite is a hard deploy gate:** any change to the Safety Agent, its prompts, or its routing logic must pass a fixed regression set of known crisis/non-crisis scenarios before it can reach production. This gate cannot be skipped by any role, including admins.

## 3. Monitoring, Logging, Alerting

- **Golden signals** per service: latency, traffic, errors, saturation (Prometheus + Grafana).
- **Safety-specific monitoring:** alert-queue depth, time-to-human-acknowledgment (SLA breach paging), classifier confidence distribution drift over time (flags model drift before it becomes an incident).
- **Centralized logging:** structured logs shipped to a log store with PII redaction at the shipping layer, not just at rest.
- **On-call:** dedicated escalation path for Safety/clinical alerts, separate from standard infra on-call — a HIGH/IMMEDIATE reviewer-queue SLA breach pages a human, not just triggers a dashboard warning.

## 4. Scaling & Cost

- Autoscale API/agent pods on request latency + queue depth, not just CPU (LLM-bound workloads are latency-bound, not CPU-bound).
- Cache aggressively at the Recommendation/Report layers (these are not safety-critical and tolerate staleness).
- Cost optimization: batch non-real-time work (weekly/monthly report generation) into off-peak Celery jobs; reserve/savings-plan compute for baseline load, on-demand for burst.

## 5. Disaster Recovery

- RPO target: <5 min (Postgres continuous backup + Redis is treated as ephemeral/rebuildable).
- RTO target: <1 hr for full service restoration in a secondary region.
- **Crisis-resource content (static hotline info etc.) is served from a CDN-cached, infra-independent path** — it must remain available even during a full backend outage.

---

## 6. QA & Testing Strategy

| Layer | Approach |
|---|---|
| Unit tests | Per-service, >85% coverage target on Safety/Agent logic specifically (not just aggregate codebase coverage) |
| Integration tests | Full pipeline: message → Emotion Agent → Safety Agent → Decision Router → response, asserting correct routing at each concern level |
| API tests | Contract tests per endpoint (schema, auth, RBAC enforcement) |
| Security tests | SAST/DAST in CI, periodic third-party penetration testing (at least annually, before any healthcare/enterprise deal) |
| Load tests | Simulate peak concurrent conversations; specifically load-test the Safety Agent path since it's the pipeline bottleneck by design |
| Accessibility tests | Automated (axe-core) + manual screen-reader pass, release-blocking for crisis-resource screens |
| AI evaluation | Fixed benchmark set of crisis/non-crisis/ambiguous scenarios, run on every Safety Agent or prompt change; tracked over time for regression |
| Usability tests | Moderated sessions with target user segments (including, carefully and with clinical oversight, individuals with lived mental-health experience) |
| Regression tests | Full suite on every release; Safety suite specifically cannot be skipped or marked non-blocking |
| **Clinical Safety Review** | Licensed clinical consultant reviews: (a) every Safety Agent prompt/logic change, (b) a sample of real (de-identified) HIGH/IMMEDIATE cases monthly, (c) false-negative/false-positive rates from the eval benchmark |

### Clinical Safety Review Cadence
- **Pre-release:** any Safety Agent change reviewed before deploy (blocking).
- **Monthly:** sampled case review + benchmark drift check.
- **Quarterly:** full audit of alert-queue SLA performance and reviewer decisions, feeding back into both product and the eval benchmark set.

---

## 7. Definition of "Ready to Launch" (MVP gate checklist)

- [ ] Safety pipeline passes full eval benchmark with clinical sign-off
- [ ] Human review queue staffed with defined SLA and on-call escalation
- [ ] Crisis resources available offline and infra-independent
- [ ] Encryption, RBAC, MFA, audit logging implemented and pen-tested
- [ ] Privacy Policy, ToS, consent flows reviewed by counsel
- [ ] Data export/delete endpoints functional and tested
- [ ] Load-tested at 2–3x expected launch traffic
- [ ] Incident response plan documented and drilled at least once

This checklist — not a calendar date — is what should gate launch.
