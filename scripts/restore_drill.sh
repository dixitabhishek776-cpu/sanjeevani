#!/usr/bin/env bash
set -euo pipefail
: "${BACKUP_FILE:?Set BACKUP_FILE to a pg_dump file}"
: "${RESTORE_DATABASE_URL:?Set RESTORE_DATABASE_URL to an isolated temporary database}"
export PGPASSWORD="${PGPASSWORD:-}"
pg_restore --clean --if-exists --no-owner --no-privileges --dbname "$RESTORE_DATABASE_URL" "$BACKUP_FILE"
psql "$RESTORE_DATABASE_URL" -v ON_ERROR_STOP=1 -c 'SELECT 1;'
echo "RESTORE_DRILL_OK"
