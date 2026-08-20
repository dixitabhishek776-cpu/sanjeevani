#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL is required}"
OUT_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$OUT_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="$OUT_DIR/mindbridge_${STAMP}.dump"
pg_dump "$DATABASE_URL" --format=custom --no-owner --file="$FILE"
sha256sum "$FILE" > "$FILE.sha256"
echo "Backup created: $FILE"
