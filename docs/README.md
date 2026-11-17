# Documentation

My Climate Story was built for the [2026 NASA International Space Apps Challenge](https://www.spaceappschallenge.org/2026/). The [live application](https://climate-story.hridoy.xyz) hosts the complete frontend, API, worker, and database on one AWS EC2 instance.

## Start here

- [Project README](../README.md): overview, live demo, setup, and quality checks.
- [Application handbook](complete-documentation.md): end-to-end product and engineering overview.
- [Architecture](architecture.md): components, request flows, storage authority, and deployment boundaries.
- [Requirements](requirements.md): product scope and the original brief's feature mapping.
- [Contributing](../CONTRIBUTING.md): development and review expectations.
- [Security policy](../SECURITY.md): private reporting and sensitive-data handling.

## Product and classroom use

- [User guide](user-guide.md): student instructions in Bangla and English.
- [Teacher guide](teacher-guide.md): a classroom activity and printable worksheet.
- [Content and localization](content-and-localization.md): authored content, glossary, and review rules.

## Engineering

- [Developer guide](developer-guide.md): setup, repository map, CLI commands, and maintenance workflows.
- [Frontend](frontend.md): routes, components, state, offline queries, and accessibility.
- [Backend](backend.md): services, durable jobs, recovery, limits, and publication.
- [API](api.md): endpoints, contracts, caching, errors, and exports; [OpenAPI](openapi.json).
- [Database](database.md): entities, migrations, seeding, authority, and retention.
- [Data dictionary](data-dictionary.md): public payloads, units, availability, hashes, and browser stores.
- [Offline](offline.md): pack integrity, migration, repair, updates, and limits.
- [Testing](testing.md): CI, automated coverage, and manual acceptance scenarios.
- [Changelog](../CHANGELOG.md): application capabilities and release changes.

## Data and imagery

- [Data catalog](data-catalog.md): sources, products, periods, units, and coverage.
- [Data usage](data-usage.md): source/variable → processing → story field → UI/API/storage mapping.
- [Data pipeline](data-pipeline.md): source reproduction, review, acquisition, and release commands.
- [Scientific methodology](scientific-methodology.md): aggregation, comparison windows, missing data, and interpretation limits.
- [Imagery](imagery.md): exact scene groups, processing, masks, and review evidence.
- [Sources and licenses](sources-and-licenses.md): scientific, map, font, icon, and educational attribution.

### Generated references

- [Per-location register](generated/place-data-register.md) / [JSON](generated/data-register.json): exact coordinates, files, hashes, series, review IDs, and imagery for all twelve places.
- [Database schema](generated/database-schema.md): application columns and constraints.
- [Queue schema](generated/queue-schema.sql): the locked Procrastinate queue DDL.
- [Story schema](generated/story-json-schema.json) and [exploration request schema](generated/exploration-json-schema.json).

Regenerate these references with `uv run python scripts/generate_documentation.py` after a validated data/model change. Scientific release format 2 and story schema version 1 are independent.

## Deployment and maintenance

- [Deployment](deployment.md): local production, configuration, private ports, storage, and rollback.
- [AWS EC2 deployment](aws-deployment.md): complete-app hosting, HTTPS, small-instance constraints, and updates.
- [Operations](operations.md): monitoring, source refresh, queue recovery, backups, and rollback.
- [Security and privacy](security-and-privacy.md): data movement, browser storage, credentials, coordinates, and retention.
- [Troubleshooting](troubleshooting.md): focused diagnosis of common setup and runtime problems.
- [Architecture decisions](decisions/001-core-architecture.md) and [scientific publication decision](decisions/002-scientific-publication.md).

Rainfall measurements remain pending. Source citations alone are not processing evidence: use the pinned release, source hashes, and review records to reproduce a number or image.
