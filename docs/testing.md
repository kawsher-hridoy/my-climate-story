# Testing and acceptance

Run from the project root:

```bash
uv run pytest
npm test
npm run typecheck
npm run build
uv run ruff check services pipelines scripts tests
uv run climate validate
```

## Automated checks

Python tests independently check supplied source counts and annual aggregation, missing values, leap-year precipitation conversion, complete years, duplicated dates, source units, sensor masks, GISTEMP raw/clean equality, release reproducibility and publication-review binding. Negative release tests alter published observations/comparisons, withdraw imagery approval, change provenance and break dependencies; each must fail without promoting an invalid release. Place/series consistency and exact captured-release S3 publication are also covered.

API tests use an isolated database and mocked queue submission. They exercise bilingual search, literal wildcard handling, invalid coordinates/extras, immediate curated stories, duplicate jobs, unavailable workers, request limits, immutable release reads and CSV units.

Frontend tests verify localization key parity, numeric formatting, range/side-by-side behavior, refusal to display unapproved imagery, and answer-index/rationale behavior. Offline tests cover disconnected SPA navigation, persistent media storage, legacy migration, incomplete packs, repair, failed commits and shared asset deletion.

Recovery tests cover interrupted submissions, abrupt worker exit, stale generations and partial artifact writes. Five opt-in integration tests use real PostgreSQL/PostGIS and Procrastinate for transaction visibility/rollback, concurrent capacity, dead-worker recovery and both migration paths. Run them only against a disposable database named exactly `climate_jobs_test`:

```bash
TEST_DATABASE_URL=postgresql+psycopg://user:password@localhost:55439/climate_jobs_test \
  uv run pytest -q tests/test_exploration_postgres.py
```

The fixture drops/recreates its public schema. Use the same PostGIS image as Compose; plain PostgreSQL lacks the extension required by the fresh-install migration. Without `TEST_DATABASE_URL`, the normal suite explicitly skips these five tests.

`climate validate` checks the actual prepared release: 12 places, 35,100 source numeric values, 24 reviewed images with matching checksums and coverage, proper global baseline, five questions per activity, relevant actions and empty pending precipitation.

## Browser acceptance

Use a real browser on the production build. The Playwright CLI is the development inspection tool; preserve evidence under `output/playwright/`.

For each curated place:

1. Open Bangla and English story routes.
2. Confirm approved images, dates, source details and keyboard slider.
3. Read the temperature chart/table and the pending rainfall explanation.
4. Play a question, read feedback, and choose an action.
5. Save, wait for completion, set offline, reload, and switch language.

Additional checks: search, coordinate errors, mobile menu, 360 px width, no horizontal overflow, text enlargement, sources, teacher printing, interrupted saving, deletion/update, and provisional global retrieval.

## Accessibility and performance

Use axe plus manual keyboard/readability checks. Pay attention to contrast on cream/green panels, informative image alt text, range naming, form labels and chart table equivalents. Automated checks do not replace reviewing actual Bengali rendering.

Measure compressed bundles and actual prepared-story sizes. Maps/charts are deferred, while the service worker installs the offline shell. Local latency measurements are evidence for this environment rather than a hosted SLA.

## Limits

IMERG authenticated full-file/OPeNDAP parity cannot be asserted without acquired measurements. The extraction logic is tested with a controlled HDF5 fixture; the delivery explicitly keeps rainfall pending. Public deployment and its external infrastructure are separate from the verified local production build.
