#!/usr/bin/env bash
# Dump the townsquare Postgres database to a gzipped SQL file.
#
# Usage:
#   scripts/backup.sh                    # writes to ./backups/<UTC-stamp>.sql.gz
#   scripts/backup.sh /path/to/dir       # writes there instead
#
# Restore:
#   gunzip -c backups/<stamp>.sql.gz | docker compose exec -T db psql -U townsquare townsquare

set -euo pipefail

OUT_DIR="${1:-./backups}"
mkdir -p "$OUT_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="$OUT_DIR/townsquare-$STAMP.sql.gz"

DB_USER="${DB_USER:-townsquare}"
DB_NAME="${DB_NAME:-townsquare}"

echo "backing up $DB_NAME → $FILE"
docker compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$FILE"
echo "done. size: $(du -h "$FILE" | cut -f1)"
