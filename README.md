# My Climate Story · আমার জলবায়ুর গল্প

A Bangla-first educational app for grades 6–10: explore a familiar place, compare real Landsat views, read NASA temperature records, play a quiz, and choose an action with your family or school.

The first release includes all 12 curated Bangladesh places, 24 reviewed satellite images, 1981–2025 POWER records, GISTEMP global context, a 30-question bilingual bank and 12 image questions, global place search, background climate retrieval, printable classroom material, and offline story packs.

**Rainfall is pending by the user's explicit choice.** The IMERG importer is implemented, but measurements require NASA Earthdata credentials. No fabricated rainfall chart or POWER rainfall-change story is shown.

## Open the application

Prerequisite: Docker Engine and Docker Compose. From this directory:

```bash
docker compose -f infra/compose.yml up -d --build --wait
```

Open **http://localhost:8088/bn/** or **http://localhost:8088/en/**. The app runs as a static Caddy frontend, FastAPI API, PostgreSQL/PostGIS database, and Procrastinate worker. The first boot restores the shipped reviewed snapshot and indexes the downloaded gazetteer. Later boots preserve prepared data.

```bash
docker compose -f infra/compose.yml ps
docker compose -f infra/compose.yml logs --tail=50 api worker
docker compose -f infra/compose.yml down
```

`down` preserves database volumes. The default database password is for this localhost-only setup. For a public server, use [the deployment guide](docs/deployment.md) and change credentials.

## Develop locally

Use Python 3.12 through `uv`, Node 22.12+ or Node 24, npm, and Docker. `.nvmrc` selects Node 24 for those using nvm.

```bash
uv sync --extra dev
npm ci
uv run python scripts/bootstrap_data.py
make db
```

Run these in separate terminals:

```bash
make api
make worker
make web
```

Development UI: http://localhost:5173. API/OpenAPI: http://localhost:8000/docs. Offline navigation must be checked against the production build, where the service worker is installed.

## Verify and reproduce

```bash
uv run pytest
npm test
npm run typecheck
npm run build
uv run climate validate
uv run ruff check services pipelines scripts tests
```

```bash
uv run climate ingest
uv run climate imagery
uv run climate build
uv run climate seed
uv run climate openapi
npm run generate:api -w apps/web
```

The original PDF and ZIP stay unchanged. Data imports verify date completeness, units, missing markers, and day-weighted annual means. Imagery approval requires aligned crops, ≥95% valid pixels, actual visual review, and checksum-specific evidence. Existing review records are applied only to matching data/images.

## Layout

| Directory | Responsibility |
|---|---|
| `apps/web` | React/TypeScript UI, charts, maps, localization, PWA and local progress |
| `services/api/climate` | API contracts, database catalog, durable jobs, operator CLI |
| `pipelines` | NASA imports, scientific calculations, imagery, gazetteer, releases and storage |
| `content` | Reviewed place copy, quizzes, actions, scene candidates and review records |
| `data/manifests` | Source/release inventory and validation evidence |
| `data/bootstrap-release.tar.gz` | Portable public, reviewed source/data snapshot |
| `docs` | Complete product, engineering, science, user and operations documentation |
| `infra` | Docker, Caddy, database and production configuration |
| `tests` | Science, pipeline and API verification |

## Important behavior

- POWER is a regional estimate, not a thermometer at a specific home.
- The default temperature view starts in 2001; older records have an explicit quality caveat.
- Decade comparisons describe dataset averages without causal attribution or hot-day counts.
- Satellite colors, haze, season and water levels can differ. Captions distinguish observations from causes.
- Global points are provisional. The 12 curated locations have reviewed image pairs; arbitrary global points do not.
- Saved stories and quiz/action progress stay on the device. No student account is required.
- Offline packs include owned images and an overview, not prefetched OSM street tiles.

Start with the [complete application handbook](docs/complete-documentation.md), then [architecture](docs/architecture.md), [which data is used where](docs/data-usage.md), [data dictionary](docs/data-dictionary.md), and the [actual per-location data register](docs/generated/place-data-register.md). The [documentation index](docs/README.md) links all developer, API, database, offline, deployment, operations, science and user guides. The [implementation plan](plan.md) retains the original requirements/design rationale.
