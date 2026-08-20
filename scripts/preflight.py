#!/usr/bin/env python3
"""Sanjeevani staging/production preflight checker.

Never prints secret values. Returns non-zero when required configuration is missing
or obviously unsafe for the selected environment.
"""
from __future__ import annotations
import os, sys, secrets, re

ENV = os.getenv("SANJEEVANI_ENV", "development").lower()
PROD = ENV in {"production", "prod"}
STAGING = ENV in {"staging", "stage"}
errors=[]; warnings=[]

def required(name):
    value=os.getenv(name)
    if not value:
        errors.append(f"missing {name}")
        return None
    return value

def check_secret(name, minimum=32):
    value=os.getenv(name)
    if not value:
        errors.append(f"missing {name}")
    elif len(value) < minimum:
        errors.append(f"{name} is shorter than {minimum} characters")
    elif value.lower() in {"change-me", "changeme", "secret", "password"}:
        errors.append(f"{name} uses an unsafe placeholder")

if PROD:
    for name in ("DATABASE_URL","REDIS_URL","SANJEEVANI_JWT_SECRET","SANJEEVANI_MASTER_KEY","SANJEEVANI_CORS_ORIGINS","SANJEEVANI_ALLOWED_HOSTS"):
        required(name)
    for name in ("SANJEEVANI_JWT_SECRET","SANJEEVANI_MASTER_KEY"):
        check_secret(name, 32)
    if os.getenv("SANJEEVANI_ENCRYPTION_PROVIDER", "").lower() != "aws_kms":
        errors.append("production must use SANJEEVANI_ENCRYPTION_PROVIDER=aws_kms")
    if not os.getenv("SANJEEVANI_KMS_KEY_ID"):
        errors.append("production requires SANJEEVANI_KMS_KEY_ID")
    if os.getenv("SANJEEVANI_CORS_ORIGINS", "").strip() in {"*", ""}:
        errors.append("production CORS must be explicit; wildcard is forbidden")
    if "localhost" in os.getenv("SANJEEVANI_ALLOWED_HOSTS", ""):
        errors.append("production ALLOWED_HOSTS must not contain localhost")
elif STAGING:
    for name in ("DATABASE_URL","REDIS_URL","SANJEEVANI_JWT_SECRET","SANJEEVANI_MASTER_KEY"):
        required(name)
    for name in ("SANJEEVANI_JWT_SECRET","SANJEEVANI_MASTER_KEY"):
        check_secret(name, 32)
    if os.getenv("SANJEEVANI_ENCRYPTION_PROVIDER", "local_dev") == "local_dev":
        warnings.append("staging is using local_dev encryption; use KMS before production")
else:
    warnings.append(f"environment is {ENV}; this script is primarily intended for staging/production")

if os.getenv("SANJEEVANI_ALERT_WEBHOOK_URL") or os.getenv("SANJEEVANI_SMTP_HOST"):
    pass
elif PROD or STAGING:
    errors.append("no alert/notification provider configured")

print(f"Sanjeevani preflight: {ENV}")
for w in warnings: print(f"WARNING: {w}")
for e in errors: print(f"ERROR: {e}")
if errors:
    print(f"FAILED: {len(errors)} blocking issue(s)")
    sys.exit(1)
print("PASS: configuration preflight succeeded")
