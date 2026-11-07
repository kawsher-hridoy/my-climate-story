# Review fixes and integration verification

Completed 2026-11-08. All 11 findings in the [implementation review](code-review.md) are addressed. The rebuilt application is running at http://localhost:8088 with validated release `mcs-cbe101aec7584839`, release format `2`, and database migration `002`.

## Changes and regression evidence

| Finding | Result | Verification |
|---|---|---|
| 1. Offline local reads pause | Saved queries use `always`; story loading uses `offlineFirst` and reads a matching pack when disconnected. | Frontend disconnected navigation tests; live first Saved navigation and pinned story navigation after disconnecting. |
| 2. Shared rate-limit bucket | Caddy has a dedicated trusted address; API ports remain private. | Six simulated forwarded clients have independent limits; spoofing from an untrusted peer is ignored. Production network and Uvicorn allowlist checked. |
| 3. Stranded jobs | Queue insertion and application insertion share a transaction. Capacity is serialized and active deduplication enforced. Leases, bounded reconciliation and generation fencing recover interrupted work. | Real PostgreSQL/Procrastinate visibility, rollback, concurrent capacity and dead-worker tests; abrupt subprocess exit regression; live queued request completed. |
| 4. Invalid release activation | The complete candidate validates before activation. S3 publication validates a captured release and writes its captured pointer last. | Missing dependency and failed candidate tests preserve the previous active pointer; invalid releases never contact S3. |
| 5. Unchecked published values | Validation recomputes annual/monthly values, decade comparisons and GISTEMP context from pinned inputs, then compares published components and standalone series. | Altered values fail even if output checksums are rewritten. The actual 12-place release passed recomputation. |
| 6. Stale image approval | Cached pairs reconcile current candidates, processing policy, scene metadata and checksum-bound canonical reviews. | Withdrawn/changed reviews, changed candidates and changed processing invalidate cached approval and prevent publication. All 12 existing pairs still pass. |
| 7. Shared series provenance | Place identity is part of series IDs; shared observations retain place-specific metadata. | Full release consistency regression; live Barishal and Bhola endpoints have distinct IDs, correct coordinates and their own review IDs. |
| 8. Partial global results | Complete artifact directories are staged, validated, hashed and promoted atomically. Database completion and bundle integrity gate serving. | Dependency-write failure, pre-commit crash, stale generation and partial legacy regressions. Complete legacy artifacts migrate; partial ones fail. |
| 9. Reused release identity | Format 2 pins all source/review/processing inputs and hashes. Identity includes these inputs, asset hashes, policy, code and asset base. Effective timestamps come from pinned inputs. | Provenance changes produce new IDs; altered inputs cannot retain an old identity; differing bytes cannot overwrite an existing directory. |
| 10. Saved-image eviction | Explicit packs use persistent `climate-pack-media-v1`; bounded browsing uses `climate-media-v2`. Integrity-aware migration/repair and reference-aware deletion preserve saved assets. | Storage/migration/repair regressions; live migrated Dhaka and new Barishal packs reopened offline with the browsing cache deleted and ordinary HTTP cache cleared. |
| 11. Password URL parsing | Database components are passed separately; SQLAlchemy and libpq use their quoting APIs. | Reserved-character and whitespace passwords round-trip through both connection parsers; Compose wiring tested. |

Deployment also exposed an address allocation collision: the API dynamically acquired Caddy's reserved address. Both peers now have distinct fixed addresses (`172.30.249.3` for API, `172.30.249.2` for Caddy). A regression checks this configuration, and the corrected Compose deployment completed successfully.

## Automated verification

- Python: **67 passed** across the full normal suite (62 passed, 5 opt-in skips) and all five disposable PostgreSQL/PostGIS integration tests.
- Frontend: **17 passed** across three test files.
- Ruff, TypeScript and generated API types: passed.
- Native Vite/PWA production build and both Docker image builds: passed; 42 precached app entries.
- npm dependency audit: zero reported vulnerabilities.
- Real release validation: 12 places, 35,100 POWER values, 24 reviewed images, 12 descriptive temperature comparisons, 12 activities and 30 reusable questions.
- Migration paths: fresh install, existing `001`, native development upgrade and production upgrade all passed.

The test container was separate from production and removed afterward. The first migration run against plain PostgreSQL failed because PostGIS was absent; using the same PostGIS image as production passed all five integration tests. Framework deprecation warnings did not indicate test failures.

## Live acceptance checks

All 12 curated API stories match their temperature and rainfall series payloads; coordinates match the curated places. All 24 main images returned `image/webp` and matched their SHA-256 values. Release-pinned curated story responses remain immutable.

The live worker retrieved a new Paris point with 45 annual POWER observations. Both referenced series matched the story, the result used a verified completion directory and 64-character completion hash, and the story response used `Cache-Control: no-store`. It remains provisional, without an automatically approved local comparison.

A Dhaka pack saved with the old application migrated to the persistent cache after accepting the app's Refresh prompt. Barishal was saved using the updated app. Disconnecting before the first Saved navigation displayed both packs; their release-pinned links opened without a loading stall. Both were complete with zero missing assets, with eight media entries in the persistent cache.

After deleting the ordinary browsing cache and clearing HTTP caching, a fresh offline tab rendered both Barishal images. The migrated Dhaka pack also reopened offline with both images. Bangla switching, six chapters, two charts and quiz feedback remained available. The 360 px Bangla story layouts had no horizontal overflow. The screenshot was visually inspected.

DevTools' cache-disabled target was discarded before the final media test because it bypassed normal service-worker handling. The accepted check used cleared HTTP caching with service-worker handling enabled; network remained offline and the browsing media cache remained absent.

## Evidence and maintenance

- [API checks](evidence/api-smoke.json)
- [Global worker result](evidence/global-job.json)
- [Offline Bangla mobile screenshot](evidence/offline-bn-mobile.png)
- [Actual validation report](../data/manifests/validation.json)
- [Regression tests](../tests/test_release_integrity.py), [recovery tests](../tests/test_exploration_recovery.py), [PostgreSQL tests](../tests/test_exploration_postgres.py), [deployment tests](../tests/test_deployment_config.py)
- [Offline navigation tests](../apps/web/src/tests/offline-navigation.test.tsx) and [storage tests](../apps/web/src/tests/offline-storage.test.ts)

The previous release `mcs-1ff46cf7c027377b`, pre-update image tags `my-climate-story-api:pre-review-fixes` / `nasa-climate-web:pre-review-fixes`, and local database backup `output/backups/climate-20261107T175822Z.dump` were retained. Database dumps and Docker image tags are local operational artifacts, excluded from the public repository. For a full rollback to format 1, restore the matching old application image as well as its release pointer; the new strict validator requires format 2. Keep database and artifact backups paired.

Updated engineering documentation covers [backend recovery](backend.md), [database migration](database.md), [offline storage](offline.md), [release processing](data-pipeline.md), [deployment](deployment.md), [operations](operations.md) and [test setup](testing.md). The bootstrap snapshot and OpenAPI/client types were regenerated.

IMERG rainfall remains visibly pending by the user's explicit decision. No Earthdata credentials, additional measurements or public deployment are claimed. S3 publication is regression-tested with a controlled client; no remote bucket was configured or published during this fix.
