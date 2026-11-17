# Contributing

Start with the [README](README.md), [architecture](docs/architecture.md), and [developer guide](docs/developer-guide.md). For behavior involving observations or imagery, also read the [scientific methodology](docs/scientific-methodology.md) and [source-to-feature map](docs/data-usage.md).

## Development workflow

1. Describe the problem or proposed change, especially for API, schema, scientific-method, or curated-place changes.
2. Keep changes focused and add a regression for changed behavior.
3. Preserve Bangla and English, accessible controls, and offline behavior.
4. Run the relevant checks and describe what was tested in the pull request.

```bash
uv sync --locked --extra dev
npm ci
uv run ruff check services pipelines scripts tests
uv run pytest -q
uv run python scripts/check_docs.py
npm test
npm run typecheck
npm run build
```

Actual-data changes also require `uv run climate validate`. PostgreSQL integration tests must use a disposable PostGIS database named exactly `climate_jobs_test`; the fixture drops its public schema. Never use production credentials or a live database for tests.

## Scientific and content changes

- Preserve the original PDF/ZIP and raw measurement/image bytes. Do not normalize scientific file line endings for formatting.
- Stage new inputs, review their source/units/completeness, and build a new validated release. Never overwrite immutable outputs under an existing release ID.
- Keep each curated place's coordinates, series identity, and review provenance distinct, including places with identical observations.
- A changed image, candidate, processing policy, or source comparison needs a new matching review. Do not relabel old approval or reviewer identity for presentation.
- Keep rainfall explicitly pending until verified IMERG data is acquired. Do not substitute POWER precipitation or invent daily extremes, significance, forecasts, or causal attribution.
- Keep quiz/action progress device-local and preserve saved-pack checksums, migration/repair, and reference-aware media deletion.

## Generated contracts and documentation

After an API/schema change:

```bash
uv run climate openapi
npm run generate:api -w apps/web
uv run python scripts/generate_documentation.py
```

Update the relevant product, engineering, science, privacy, and operations guides. Generated data references describe the pinned snapshot, not an unverified current upstream dataset.

## Repository hygiene

Keep secrets, machine-specific configuration, working plans, agent instructions, browser reports, logs, database dumps, and temporary downloads out of Git. Local artifacts belong under ignored `output/` or staging directories. Scientific inputs, canonical reviews, owned assets, lockfiles, migrations, and published releases are intentional repository dependencies.

Report vulnerabilities privately according to [SECURITY.md](SECURITY.md). Third-party data and asset attribution is documented in [sources and licenses](docs/sources-and-licenses.md).
