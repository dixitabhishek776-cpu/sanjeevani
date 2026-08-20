# Sanjeevani Release Checklist

## Engineering
- [ ] CI green on a clean runner
- [ ] Alembic migrations verified on a fresh PostgreSQL database
- [ ] PostgreSQL/Redis integration tests green
- [ ] Frontend production build green
- [ ] E2E smoke suite green
- [ ] Load test evidence captured
- [ ] Backup and restore drill successful

## Security
- [ ] Secret scan clean
- [ ] Dependency/container scans clean or risk accepted
- [ ] BOLA/IDOR tests green
- [ ] Authentication/session tests green
- [ ] Prompt-injection regression suite green
- [ ] External penetration test completed
- [ ] Critical/high findings closed or formally accepted

## Safety
- [ ] Crisis detection benchmark reviewed
- [ ] English/Hindi/Hinglish benchmark reviewed
- [ ] False-negative analysis completed
- [ ] False-positive analysis completed
- [ ] Evidence-based interventions clinically reviewed
- [ ] Human escalation SOP tested
- [ ] Crisis resources verified

## Privacy/legal
- [ ] Privacy notice reviewed for launch jurisdictions
- [ ] Terms reviewed
- [ ] Data retention/deletion policy approved
- [ ] Consent flows reviewed
- [ ] Data export/deletion tested

## Operations
- [ ] Monitoring and alerting active
- [ ] On-call owner assigned
- [ ] Incident response drill completed
- [ ] Rollback procedure tested
- [ ] Model/prompt rollback tested

## Launch
- [ ] Closed beta completed
- [ ] Safety incidents reviewed
- [ ] Support process active
- [ ] Public launch approval recorded
