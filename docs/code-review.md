# Implementation review

**Resolution:** All 11 findings were fixed and verified on 2026-11-08. See [fix report](review-fixes.md) for implementation details, regressions, live checks and the deployed release. The original review below is preserved as historical evidence.

Reviewed 2026-11-07. Scope: frontend/offline behavior, backend and jobs, scientific data/release handling, and deployment configuration. Application code, published data and production database were not changed. Reproductions used isolated browser state, temporary data copies and isolated database fixtures; deployment/API inspection was read-only.

Rainfall being pending is an explicitly accepted product decision and is not listed as a defect.

## Priority summary

| Priority | Finding |
|---|---|
| P1 | Offline SPA navigation can indefinitely hide saved stories |
| P1 | Visitors share one rate-limit bucket behind Caddy |
| P1 | Interrupted jobs can remain permanently pending/running |
| P1 | Candidate releases become active before validation |
| P2 | Published scientific values are not checked by release validation |
| P2 | Cached image pairs ignore changed or withdrawn review records |
| P2 | Shared series IDs overwrite place-specific provenance |
| P2 | Failed workers can expose incomplete stories |
| P2 | A release ID can be reused for different serialized content |
| P2 | Explicitly saved images are subject to browsing-cache eviction |
| P2 | Reserved characters in database passwords break deployment URLs |

## 1. P1 — Offline navigation does not run local reads

**Location:** [Saved.tsx](../apps/web/src/pages/Saved.tsx), line 23; [Story.tsx](../apps/web/src/pages/Story.tsx), line 59; [main.tsx](../apps/web/src/main.tsx), line 16.

**Normal reproduction:** Save Dhaka online, disconnect, then open Saved stories for the first time in the current SPA session. The page stays on its loading message. Reconnecting displays the pack. Disconnecting again and opening the release-pinned saved-story link also stalls.

TanStack Query defaults to `networkMode: online`; after an offline event it pauses the query function, including the purely local IndexedDB read and the story loader's offline fallback. An independent query-core reproduction returned `calls: 0, status: pending, fetchStatus: paused`. The same function ran successfully with `always` or `offlineFirst`.

**Improvement:** Use `always` for local saved-pack queries and an appropriate offline-capable mode for story loading. Add transition/navigation tests, not only cold offline reload tests.

## 2. P1 — Rate limiting becomes site-wide behind the proxy

**Location:** [start-api.sh](../scripts/start-api.sh), line 11; [main.py](../services/api/climate/main.py), line 67.

Uvicorn trusts loopback forwarded headers by default, but Caddy reaches it from a separate Docker address. The running API's trust list was `127.0.0.1,::1`; the web-container peer was `172.20.0.5`. `request.client.host` therefore identifies Caddy for every visitor.

An isolated reproduction using the installed Uvicorn middleware and actual limiter sent six distinct forwarded client addresses. All shared the same bucket; the sixth request received 429. The five-per-minute exploration allowance is effectively shared across the classroom/site.

**Improvement:** Configure a narrowly defined trusted proxy path and derive client identity correctly. Keep direct public API access disabled. Add a proxy-aware multi-client test.

## 3. P1 — Job submission and recovery can strand requests

**Location:** [main.py](../services/api/climate/main.py), lines 261 and 289; [jobs.py](../services/api/climate/jobs.py), line 32.

The application job is committed before its separate queue submission. Cancellation at that boundary leaves a pending row with no queued work. Subsequent requests reuse pending/running rows indefinitely, without reconciling queue existence or expiration.

Isolated reproductions confirmed both a cancellation before enqueue and a worker subprocess exiting immediately after committing `running`. Retrying returned 202 with the old job and zero enqueue calls. Twenty old orphan rows caused unrelated requests to receive 503 queue-full responses.

**Improvement:** Make submission transactional through a queue transaction or outbox. Reconcile missing/stalled work using bounded leases and idempotent retries. Add crash/restart tests against the real worker lifecycle.

## 4. P1 — Invalid releases are activated before validation

**Location:** [build.py](../pipelines/build.py), line 398; [storage.py](../pipelines/storage.py), line 21.

`build_release` changes the active pointer after serialization, without running release validation. Publishing also trusts the active pointer without validating that release.

In a temporary copy, an image URL was changed to reference a missing file. Building succeeded and activated the candidate. Subsequent validation raised `FileNotFoundError`, but the invalid release remained active.

**Improvement:** Build into a staging directory, validate that specified candidate, and change the active pointer only on success. Remote publishing should require validation of the exact release being uploaded. Test that failed updates preserve the old active pointer.

## 5. P2 — Validation does not compare published values with their sources

**Location:** [validation.py](../pipelines/validation.py), line 19.

The validator checks raw POWER inputs and output counts/status labels, but does not compare the actual published observations or comparison numbers with recomputed values.

In an isolated release, changing Dhaka's first annual temperature from approximately 25.7291 to 12345 and its comparison difference to 999 still produced `passed: true`.

**Improvement:** Recompute and compare monthly values, annual aggregation, comparison windows/results, source hashes and referenced series payloads. Add negative tests that alter output values while preserving counts.

## 6. P2 — Cached imagery retains stale approval

**Location:** [imagery.py](../pipelines/imagery.py), line 293; [validation.py](../pipelines/validation.py), line 36.

Prepared pairs with `needs_review` or `approved` status take a cache path that does not reconcile current scene candidates, processing policy or canonical review records. Validation checks an image against its asset checksum but not against the current review's checksums.

Changing Dhaka's canonical review checksum in a temporary copy, then preparing/building, returned `approved, cached: true`. The published pair kept its old embedded approval and validation passed.

**Improvement:** Reconcile all cached pairs against current candidates, processing configuration and review records. Invalidate withdrawn/stale approval. Independently bind the review to both image hashes and the processing version.

## 7. P2 — Shared series overwrite location-specific metadata

**Location:** [build.py](../pipelines/build.py), lines 295 and 372.

The series ID hashes monthly observations, while its serialized payload also contains a place's coordinates, comparison review ID and shared-series annotations. Identical values cause the later place to overwrite the earlier place's file.

The active Barishal story points to a series endpoint containing Bhola coordinates `(22.6859, 90.6482)` instead of `(22.701, 90.3535)`, and a Bhola review ID. The measurements are identical; the provenance is wrong for the requested story.

**Improvement:** Separate shared observations from location-specific metadata, or include place identity in component IDs. Test consistency between every story component and its series endpoint.

## 8. P2 — A failed worker can expose an incomplete story

**Location:** [jobs.py](../services/api/climate/jobs.py), line 121; [main.py](../services/api/climate/main.py), line 244.

The worker writes the story before its series and raw source evidence. The API treats an existing story file as a completed result.

An isolated failure of the second output write left a visible story and a failed job. Retrying the same named place returned HTTP 200 with that story, its referenced series returned 404, and no replacement job was queued.

**Improvement:** Stage all dependencies before exposing the story. Use a completion marker or completed-job gate, and publish the story last. Add a partial-filesystem-failure test.

## 9. P2 — Immutable release identity omits serialized provenance

**Location:** [build.py](../pipelines/build.py), line 247.

The fingerprint omits the archive inventory, but its retrieval timestamp is embedded in output files. Changing only `archive-inventory.json.imported_at` in a temporary copy and rebuilding retained the same release ID while changing story bytes.

**Improvement:** Include every serialized provenance dependency in release identity, and refuse to overwrite an existing release with different content. Verify byte-level immutability, not only repeatability with unchanged metadata.

## 10. P2, conditional — Saved media shares an expiring browsing cache

**Location:** [offline.ts](../apps/web/src/lib/offline.ts), lines 41 and 99; [vite.config.ts](../apps/web/vite.config.ts), line 49.

Explicitly saved media is placed in the same Workbox cache as ordinary browsing, capped at 80 entries and one year. The saved IndexedDB record is not linked to an eviction exemption.

In an isolated browser, a normal saved Dhaka pack lost its cached historical image after 82 distinct query variants of a local thumbnail were fetched. Workbox reduced the cache to 80 entries while the pack remained listed as complete.

**Scope of evidence:** Capacity eviction was reproduced using synthetic local URL variants. Current normal browsing of the 12-place release was not shown to exceed the cap. Later media/release growth can trigger it; configured one-year expiry was not separately time-tested. Ordinary HTTP caching may temporarily conceal the lost durable-cache entry.

**Improvement:** Keep saved media in a separate persistent pack cache, checked first by the service worker. Remove an asset only when no saved pack references it.

## 11. P2 — Database passwords are inserted into URLs without encoding

**Location:** [compose.yml](../infra/compose.yml), lines 23 and 47.

The database receives the raw password, while API/worker connection strings interpolate it into a URL. A password containing reserved characters changes URL parsing. For the controlled example `Example@Strong/Password42`, SQLAlchemy parsed host `Strong` and database `Password42@db:5432/climate`, rather than `db` and `climate`.

**Improvement:** Build connection URLs using encoded components or pass separate database connection parameters. Add deployment tests with reserved-character passwords.

## Recommended implementation order

1. Restore normal offline navigation and correct proxy-aware rate limiting.
2. Make queue submission/recovery and artifact publication transactional.
3. Strengthen scientific output validation and canonical review binding.
4. Fix shared-series provenance and release immutability.
5. Separate persistent pack storage and harden deployment configuration.

The positive scientific tests still pass: calendar weighting, leap-year conversion, missing-value handling and supplied annual aggregation. Their success does not cover the negative update, crash and offline-navigation scenarios above. Add focused regression tests for each confirmed defect instead of relying on a larger count of happy-path tests.
