#!/usr/bin/env python3
"""Generate an untracked local staging env file with random secrets."""
from pathlib import Path
import secrets

root=Path(__file__).resolve().parents[1]
out=root/'.env.staging'
if out.exists():
    raise SystemExit(f"Refusing to overwrite {out}; remove it first if you really want to rotate secrets.")

def token(n=48): return secrets.token_urlsafe(n)

content=f'''POSTGRES_USER=sanjeevani_staging
POSTGRES_PASSWORD={token(32)}
POSTGRES_DB=sanjeevani_staging
SANJEEVANI_JWT_SECRET={token(48)}
SANJEEVANI_MASTER_KEY={token(48)}
SANJEEVANI_ENV=staging
SANJEEVANI_ENCRYPTION_PROVIDER=local_dev
SANJEEVANI_CORS_ORIGINS=http://localhost:3000
SANJEEVANI_ALLOWED_HOSTS=localhost,127.0.0.1,backend
SANJEEVANI_MAX_BODY_BYTES=262144
SANJEEVANI_METRICS_TOKEN={token(32)}
'''
out.write_text(content, encoding='utf-8')
print(f'Created {out}. Keep it untracked and never commit it.')
