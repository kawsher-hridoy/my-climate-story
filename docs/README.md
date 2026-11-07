# Documentation index

Start with the [project README](../README.md) for setup and the [accepted plan](../plan.md) for scope and rationale.

For the entire implemented app, start with the [complete application handbook](complete-documentation.md). For exact source-to-screen mapping use [which data is used where](data-usage.md), the [data dictionary](data-dictionary.md), and the generated [per-location register](generated/place-data-register.md) / [JSON register](generated/data-register.json).

## Product and students

- [Requirements](requirements.md): complete PDF mapping and the accepted rainfall amendment.
- [User guide](user-guide.md): student instructions in Bangla and English.
- [Teacher guide](teacher-guide.md): a 35-minute classroom activity and printable worksheet.
- [Content and localization](content-and-localization.md): schemas, glossary and editing/review rules.

## Engineering

- [Architecture](architecture.md): components, data flow and boundaries.
- [Developer guide](developer-guide.md): setup, repository map, every CLI command and common changes.
- [Frontend](frontend.md): routes, components, design, state and accessibility.
- [Backend](backend.md): services, worker, caching and failures.
- [API](api.md): contracts and examples; [OpenAPI JSON](openapi.json) is generated.
- [Database](database.md): entities, constraints, search indexes and migrations.
- [Generated database schema](generated/database-schema.md): every actual application column/type/constraint.
- [Queue SQL schema](generated/queue-schema.sql): exact Procrastinate queue tables/functions from the locked dependency.
- [Data dictionary](data-dictionary.md): public payload fields, units, statuses and browser stores; [Story JSON Schema](generated/story-json-schema.json) and [request JSON Schema](generated/exploration-json-schema.json).
- [Offline](offline.md): pack storage, integrity, updates and limits.
- [Testing](testing.md): checks and acceptance scenarios.
- [Verification](verification.md): current automated and live acceptance results.
- [Review fixes](review-fixes.md): all 11 implementation review resolutions and regression evidence.

## Data and imagery

- [Data catalog](data-catalog.md): sources, units, coverage and licenses.
- [Data usage](data-usage.md): source/variable → processing → story field → page/chart/API/SQL/offline mapping.
- [Per-location register](generated/place-data-register.md): current coordinates, source hashes, series/review IDs, image dates/products, quiz/action IDs.
- [Data pipeline](data-pipeline.md): reproduction and acquisition commands.
- [Scientific methodology](scientific-methodology.md): calculations and publication limits.
- [Imagery](imagery.md): exact scenes, processing, masks and review evidence.
- [Sources and licenses](sources-and-licenses.md): attribution and references.

## Deployment and maintenance

- [Deployment](deployment.md): localhost production build and public-server adaptation.
- [Operations](operations.md): monitoring, refreshes, backups and rollback.
- [Security and privacy](security-and-privacy.md): device data, coordinates, providers, secrets, public results and retention.
- [Troubleshooting](troubleshooting.md): missing data, workers, browser storage and setup failures.
- [Decisions](decisions/001-core-architecture.md): rationale for major choices.
- [Release notes](release-notes.md): delivered functionality and known limits.

Generated measurements and image URLs are versioned by release. A source citation alone is not a processing record; use the release and source manifests to reproduce a number or crop.
