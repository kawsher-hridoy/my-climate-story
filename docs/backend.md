# Backend and jobs

FastAPI owns public contracts and prepared data access. Scientific work belongs in the pipelines and a durable Procrastinate worker. PostgreSQL serves both application catalog tables and the job queue.

## Common reads

Featured places, stories, sources and series are read from the active immutable release. The database handles the large alias index and request jobs. This avoids recomputing 45-year records for each student page load.

Source and image paths are constrained to known identifiers. The API accepts coordinates or registered place IDs, never arbitrary upstream URLs or expressions. Missing files produce explicit unavailable/error responses.

## Exploration

`POST /api/v1/explorations` returns a curated prepared story immediately. Other coordinates are normalized and deduplicated against the current release. A durable job returns pending/running/completed/failed state.

The worker requests fixed POWER parameters, validates the result, writes a provisional story and records a terminal result. It makes bounded upstream attempts and cannot approve itself. Precipitation and reviewed historical pairs remain unavailable for unprepared global points. Generic actions avoid inventing local hazard advice.

The application job and its Procrastinate queue entry commit in the same PostgreSQL transaction. An advisory transaction lock serializes capacity checks; a partial unique index prevents duplicate active requests. Queue IDs, dispatch generations and run tokens prevent an older worker from publishing after recovery.

Reconciliation runs every 30 seconds in the API, when an exploration is submitted, and at worker startup. Missing queue entries and dead workers can be requeued up to three dispatches. Pending leases last 15 minutes, running leases 10 minutes, and the total request lifetime is one hour. A live worker that exceeds its lease is cancelled and its application job fails rather than running concurrent copies.

The worker stages the story, both series and raw POWER evidence together, validates source/series agreement, writes a hashed completion manifest, and atomically promotes the directory. The API serves a global result only after its database row is completed and the bundle verifies. Complete legacy results migrate through the same verification; partial legacy files are rejected. Global story responses use `no-store`; release-pinned curated stories retain immutable caching.

## Limits and errors

- Expensive exploration: five requests per minute per client fingerprint.
- Pending/running queue capacity: 20 requests.
- Heavy worker concurrency: one.
- Upstream requests: finite timeouts and bounded retries, with Retry-After honored when supplied.
- Ordinary API access logging excludes exact query coordinates.

Use one API process for the in-memory client throttle. The deployment trusts only Caddy's dedicated proxy address for forwarded client identity, so separate visitors have separate buckets. A larger multi-process deployment needs a shared limiter before increasing replicas.

## Publication

Data refresh and release promotion are separate operations. A release is built completely before the active pointer changes. Ingestion cannot turn a provisional series into approved change copy; approval is recorded against source hashes and windows.

The public API has no administration or content-upload routes. Operators use `climate` commands for ingestion, validation, review, release building, metadata generation and optional storage publication.

## Configuration

Settings are read from environment variables and optional `.env`. See `.env.example` for database, Earthdata, storage and asset settings. Never place credentials in frontend environment variables, source manifests or logs. Local artifacts are sufficient for the default deployment; remote object storage is optional.
