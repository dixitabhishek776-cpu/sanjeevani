#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL is required}"
FILE="${1:?Usage: restore_postgres.sh /path/to/backup.dump}"
[[ -f "$FILE" ]] || { echo "Backup not found: $FILE" >&2; exit 1; }
pg_restore --clean --if-exists --no-owner --dbname="$DATABASE_URL" "$FILE"
echo "Restore completed from: $FILE"
