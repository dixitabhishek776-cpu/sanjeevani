# Sanjeevani Staging Runbook

## 1. Local prerequisites

- Docker Engine + Docker Compose v2
- Git
- A connected network for image/package pulls

## 2. Generate local staging secrets

```bash
python scripts/generate_staging_env.py
```

The generated `.env.staging` is ignored by git.

## 3. Start staging

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml up -d --build
```

## 4. Verify services

```bash
curl -fsS http://localhost:8000/livez
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:3000/
```

## 5. Run smoke checks

```bash
bash scripts/staging_smoke.sh
```

## 6. Run application checks

```bash
cd backend
python -m pytest tests -q
cd ..
python scripts/security_smoke.py
python scripts/launch_gate.py
```

## 7. Stop staging

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml down
```

## Production warning

Never use `local_dev` encryption or localhost CORS/hosts in production. Production requires AWS KMS (or another explicitly approved managed key provider), managed secrets, TLS, explicit origins/hosts, monitored backups, and a staffed safety escalation operation.
