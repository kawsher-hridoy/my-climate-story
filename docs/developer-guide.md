# Developer and maintenance guide

Use the [complete handbook](complete-documentation.md), [architecture](architecture.md) and [data usage](data-usage.md) before changing source/feature behavior. The accepted scope retains rainfall pending and deterministic reviewed narration.

## Native development

Prerequisites: Python 3.12, `uv`, Node 22.12+ with npm, Docker/Compose. Production uses Node 24. Dependencies are locked in `uv.lock` and `package-lock.json`.

```bash
uv sync --extra dev
npm ci
uv run python scripts/bootstrap_data.py
make db
```

Bootstrap preserves an existing active release. `make db` starts the separate development PostGIS database at localhost:55432, migrates, initializes the queue and seeds. In three separate terminals run `make api`, `make worker` and `make web`. Frontend is localhost:5173 and API localhost:8000; Vite proxies `/api` and `/media`. `CLIMATE_API_PROXY` selects an isolated API for preview testing. Production remains localhost:8088 through Caddy.

Use `.env.example` for configuration. Leave `DATABASE_URL` blank for component construction or provide a compatible native/test URL. Compose sets its own database host/port and production environment. Never print full settings or commit credentials.

## Repository map

| Path | Responsibility |
|---|---|
| `apps/web/src/pages/` | Home, Explore, Story, Saved and authored information pages |
| `apps/web/src/components/` | Map, imagery, charts, quiz and shared UI |
| `apps/web/src/lib/` | API/types, localization/formatting, offline storage/connectivity |
| `apps/web/public/` | Icons, decorative assets and offline overview |
| `services/api/climate/` | API/models, config, catalog/files, CLI, worker and recovery |
| `services/api/migrations/` | Alembic changes |
| `pipelines/` | Science, providers, gazetteer, imagery, IMERG, refresh, build/validation/storage |
| `content/` | Bilingual content and source/image review records |
| `data/raw/`, `data/staging/`, `data/processed/` | Evidence, intermediates and publications |
| `infra/`, `scripts/` | Containers/proxy, startup, backup, bootstrap/pack/document generation |
| `tests/`, `apps/web/src/tests/` | Python/frontend regressions |
| `docs/` | Specifications, handbook, contracts and data registers |

## Common change workflows

### UI or mobile layout

Edit page/component/CSS and `i18n.ts`. Preserve both languages, visible focus, labeled native controls and mobile targets. Check the production build at 360 px, menu, slider/side-by-side and chart/table. UI changes need a new web image/service worker; existing users get the Refresh prompt. Keep scientific calculation/review logic in pipelines; charts/CSV consume prepared values.

### Place, quiz or action content

Edit the corresponding `content/` file; review translations, citations, correct index and tags/audiences. Build/seed/validate a new release, package it and regenerate the register. Packs stay pinned until Update. Quiz keys include content version; action selections use place ID.

### Scientific input or method

Preserve original evidence, stage refreshes and select corrected input explicitly. Add a meaningful regression for the actual scientific behavior. Changed source/hash/windows need a matching scoped comparison review. Validate the whole candidate before activation; never edit an immutable output under its old label. Update source cutoffs, units, missing-data rules and interpretation limits in the data/method guides.

### Imagery

Update candidates/policy, acquire actual matching windows, inspect alignment/QA/masks/season/haze, and review the new checksums. Old cached approval does not survive changed authority. Use `uv run climate imagery --places dhaka` for a focused run, then the review/build/seed/validate workflow. Illustrations cannot replace scientific evidence.

### Another curated place

Define reviewed bilingual metadata, independently requested POWER input, image candidates/processing/review, comparison and appropriate actions/questions. Audit twelve-place constants in API/configuration, validation, seed return values, tests and docs before expanding the curated set. Global selection already supports additional names/coordinates without assigning automatic curated approval.

### API or SQL changes

Edit Pydantic/API models and callers together. Regenerate OpenAPI/types/references, then typecheck:

```bash
uv run climate openapi
npm run generate:api -w apps/web
uv run python scripts/generate_documentation.py
npm run typecheck
```

Generated TypeScript is a compile-time contract; server/pipeline validation remains necessary. SQL changes need a new Alembic migration, not only edited ORM metadata. Test both fresh and existing database paths.

Recovery changes must preserve queue/application atomicity, capacity locking, active uniqueness, lease/generation/run-token fencing and complete bundle verification. Real queue fixtures run only against a separate PostGIS database named `climate_jobs_test`; they drop its public schema. See [testing](testing.md).

## Complete CLI inventory

Use `uv run climate ...` natively or `climate ...` inside the image.

| Command | Effect |
|---|---|
| `ingest` | Import/validate supplied POWER/GISTEMP archive and inventory |
| `imagery [--places ...]` | Reconcile or acquire/process real pairs |
| `review-temperature --reviewer ... --evidence ...` | Record source/window review after checking evidence |
| `review-imagery --place ... --reviewer ... --evidence ...` | Record checksum-bound visual review |
| `build` | Capture inputs, build/validate candidate and activate only when ready |
| `validate` | Recompute/check actual active release values/reviews/assets |
| `migrate` | Upgrade Alembic SQL schema |
| `queue-schema` | Initialize Procrastinate schema if absent |
| `seed` | Catalog active curated release |
| `gazetteer [--bangladesh-only]` | Import names/aliases, preserving curated places |
| `worker` | Reconcile/run one durable processing worker |
| `imerg-discover` | Refresh public IMERG catalog |
| `imerg` | Authenticated extraction, or pending without credentials |
| `refresh-power` | Stage fixed-window POWER refresh |
| `refresh-global` | Stage GISTEMP refresh |
| `openapi` | Generate `docs/openapi.json` |
| `publish` | Validate captured release; publish declared S3 outputs/assets, pointer last |

`make data` assumes approved imagery is already present. An empty source workspace needs imagery acquisition/review before the normal ready build; prefer the reviewed bootstrap for clean setup. Python `build_release(activate=False)` permits an unpublished draft and never promotes it as ready.

## Checks and handoff

Run checks relevant to the change:

```bash
uv run ruff check services pipelines scripts tests
uv run pytest -q
npm test
npm run typecheck
npm run build
uv run climate validate
```

Recovery changes also need disposable PostgreSQL integration. Data changes need actual release validation and regenerated bootstrap/registers. Offline changes need a production service worker, online save → disconnect → first Saved → pinned story, cold reload, language/media retention and repair checks. Vite development is not an offline production build.

Distribution commands:

```bash
uv run python scripts/pack_data.py
uv run python scripts/generate_documentation.py
docker compose -f infra/compose.yml build
docker compose -f infra/compose.yml up -d --no-build --wait
```

Retain the previous image/release/database backup until acceptance. Update data usage/dictionary, architecture, relevant specialist guides and verification. Generated registers describe the pinned snapshot rather than claiming present-day upstream coverage.

See [deployment](deployment.md), [operations](operations.md) and [troubleshooting](troubleshooting.md).
