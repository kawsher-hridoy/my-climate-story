#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p output/backups
backup_file="output/backups/climate-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose -f infra/compose.yml exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > "$backup_file"
printf 'Database backup: %s\n' "$backup_file"
