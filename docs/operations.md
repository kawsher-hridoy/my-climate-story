# Operations

## Routine checks

```bash
docker compose -f infra/compose.yml ps
docker compose -f infra/compose.yml logs --tail=50 api worker
curl -f http://localhost:8088/api/v1/health/ready
```

Monitor API latency/errors, worker failures, queue age, source freshness, database backups, disk and object-storage availability. A failed upstream acquisition must not replace an approved release.

## Source refresh

Run public source discovery/refresh monthly or when a correction is needed. The operator CLI stages POWER and GISTEMP acquisitions. Inspect them, validate units/completeness and update the selected source explicitly before rebuilding. Extending fixed comparison windows requires a new scientific/content review.

IMERG remains pending until access is configured. Its acquisition should process one granule at a time, preserve extraction manifests and remove completed staging files. Do not run a multi-gigabyte acquisition on every public map request.

## Worker recovery

The durable Procrastinate queue survives API restarts. Inspect terminal messages before retrying. Fixed HTTP providers have finite timeouts and bounded retries; invalid units/files should be investigated rather than retried indefinitely.

The API reconciles work every 30 seconds and on exploration submissions; the worker also reconciles at startup. Orphans and dead workers are requeued within a three-dispatch, one-hour bound. Expired or exhausted requests become failed and release capacity. Inspect `queue_job_id`, `generation`, `dispatch_attempts`, `lease_until`, and the terminal message when investigating recovery. Do not manually set a partial result to completed: completion requires a verified artifact directory and hash.

Restart an unhealthy worker with `docker compose -f infra/compose.yml restart worker`. Keep the API and approved curated stories available while resolving an upstream issue. Review stale pending/running jobs and queue logs before attempting administrative recovery.

## Backups

`sh scripts/backup.sh` creates a PostgreSQL custom-format dump under `output/backups/`. Save the app image tag, active release ID and matching `data` artifacts alongside it. Store off-machine backups encrypted using the organization's chosen backup system; the local dump itself is not encrypted by the script.

Test restoration into a separate temporary database. Never test destructive restoration against the only live copy. A database backup alone does not include image files or local student packs.

## Release updates

```bash
uv run climate build
uv run climate seed
uv run climate validate
uv run python scripts/pack_data.py
```

Preserve immutable old release directories. Update the active pointer only after complete files exist and validation succeeds. Publish a new app image when frontend/contracts change. Saved packs retain their recorded release until updated by the student.

## Rollback

Restore the previous application image, set `data/processed/active.json` to a known-good release ID, then reseed. Verify source endpoints, a curated story, image hashes and readiness. Do not silently mix a previous data payload with a newer release label.
