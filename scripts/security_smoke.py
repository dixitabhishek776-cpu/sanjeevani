#!/usr/bin/env python3
"""Non-destructive production/staging security smoke checks.
Usage: python scripts/security_smoke.py https://staging.example.com
"""
import sys
import httpx

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
checks = []
with httpx.Client(timeout=10, follow_redirects=False) as c:
    r = c.get(BASE + "/livez")
    checks.append(("livez", r.status_code == 200))
    r = c.get(BASE + "/docs")
    checks.append(("docs_not_public", r.status_code in (404, 401, 403)))
    r = c.get(BASE + "/metrics")
    checks.append(("metrics_not_public", r.status_code in (404, 401, 403)))
    r = c.get(BASE + "/health")
    checks.append(("health_endpoint", r.status_code in (200, 503)))

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(f"{'PASS' if ok else 'FAIL'} {name}")
if failed:
    raise SystemExit("Security smoke failed: " + ", ".join(failed))
