# Sanjeevani Real-World Launch Plan

## Product boundary
Sanjeevani is an AI mental-wellness companion and self-help/navigation product. It is not a clinician, emergency dispatch service, diagnostic system, or replacement for professional care.

## Required launch gates
1. Clinical/safety review by qualified mental-health professionals.
2. Independent safety red-team and multilingual evaluation.
3. Human on-call escalation with documented SLA.
4. Production PostgreSQL, Redis, KMS/secrets, backups and restore drill.
5. Real notification provider with delivery monitoring.
6. Penetration test and dependency/container vulnerability scanning.
7. Privacy/legal review for each launch jurisdiction.
8. Incident-response tabletop exercise.
9. Accessibility and usability testing.
10. Closed beta before public availability.

## Safety architecture
NORMAL -> DISTRESS -> ELEVATED -> HIGH_RISK -> IMMEDIATE_RISK -> HUMAN_REVIEW -> RESOLVED

The AI never gets authority to lower an already elevated safety state. A human process owns final escalation decisions.

## India crisis routing
For immediate danger, the product should direct users to India's emergency number 112 and to Tele-MANAS 14416 / 1800-89-14416. These are official government services.

## Beta exit criteria
- zero known critical security vulnerabilities
- documented false-negative analysis
- documented false-positive analysis
- 100% of immediate-risk test cases routed to the crisis UX in the approved benchmark
- reviewer escalation drill completed
- restore-from-backup drill completed
- privacy deletion/export tested end-to-end
