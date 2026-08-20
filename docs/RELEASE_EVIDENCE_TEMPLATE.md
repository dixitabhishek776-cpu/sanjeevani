# Sanjeevani Release Evidence Pack

This document is an evidence template. A checked box means the evidence exists and has been reviewed; it must never be checked merely because a script exists.

## Engineering
- [ ] Clean CI runner: build + tests
- [ ] Fresh PostgreSQL migration from empty database
- [ ] Redis integration
- [ ] Frontend production build
- [ ] E2E report
- [ ] Load report: requests, concurrency, RPS, p50/p95/p99, errors
- [ ] Backup + restore report

## Security
- [ ] Dependency scan
- [ ] Container scan
- [ ] Secret scan
- [ ] Auth/session tests
- [ ] BOLA/IDOR tests
- [ ] Prompt-injection red-team report
- [ ] Independent penetration test

## Safety / Clinical
- [ ] Approved safety benchmark version
- [ ] False-negative analysis
- [ ] False-positive analysis
- [ ] English/Hindi/Hinglish evaluation
- [ ] Intervention clinical review
- [ ] Human escalation drill
- [ ] Crisis resource verification

## Privacy / Legal
- [ ] Privacy notice approved
- [ ] Terms approved
- [ ] Retention/deletion policy approved
- [ ] Consent review
- [ ] Export/deletion E2E evidence

## Operations
- [ ] On-call roster
- [ ] Incident tabletop
- [ ] Rollback drill
- [ ] Model/prompt rollback drill
- [ ] Monitoring dashboards
- [ ] Alert delivery test

## Launch decision
- [ ] All P0 findings closed or formally accepted by authorized owners
- [ ] Clinical sign-off
- [ ] Security sign-off
- [ ] Privacy/legal sign-off
- [ ] Product/operations sign-off
- [ ] Public launch approval recorded
