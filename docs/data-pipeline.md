# Reproducing and acquiring data

Run commands from the project root with Python 3.12 and the locked `uv` environment. The original source PDF and ZIP are retained unchanged.

## Restore the reviewed snapshot

```bash
uv run python scripts/bootstrap_data.py
make db
uv run climate validate
```

Restoration skips an existing active release. The public bootstrap archive contains prepared stories/images, source JSON/CSV, metadata, review manifests and downloaded gazetteer files. It contains no `.env`, credentials or signed URLs.

## Rebuild from source

```bash
uv run climate ingest
uv run climate imagery
uv run climate build
uv run climate seed
uv run climate validate
```

The archive importer checks all 12 locations and five POWER variables, calendars, units, physical ordering and annual aggregation. The image processor skips already prepared pairs and retrieves only required RGB/QA windows. Existing checksum-specific visual reviews can apply to matching images. New or changed images require a fresh visual review.

Release building now captures public source, processing and review inputs inside the candidate's `inputs/` directory. It checks the full candidate before activation, including recomputed scientific values, standalone series consistency, image files and current canonical reviews. Failed validation preserves the previous active pointer. A matching existing release must be byte-identical; it is never overwritten with different output.

The normal `climate build` requires approved imagery for all 12 places. For an unpublished numerical draft in development, call `build_release(activate=False)` from Python. This draft never changes the active pointer and cannot be published remotely. Earlier releases lacking pinned input manifests remain readable, but must be rebuilt before strict validation/publication.

Review operations are intentionally separate:

```bash
uv run climate review-temperature --reviewer "Reviewer name" --evidence "Describe source, units, complete windows, aggregation checks and descriptive scope."
uv run climate review-imagery --place dhaka --reviewer "Reviewer name" --evidence "Describe observed coverage, alignment, haze, masks and interpretation limits."
uv run climate build
uv run climate seed
```

Do not use a review command as a substitute for checking evidence. Temperature approvals are bound to source content and exact windows; image approvals are bound to image checksums and processing policy.

## IMERG

Populate Earthdata credentials locally from `.env.example`, then:

```bash
uv run climate imerg-discover
uv run climate imerg
```

Discovery is public metadata. Measurement extraction authenticates using `earthaccess`, downloads one granule at a time, reads the `Grid` group, checks units/dimensions, samples all 12 places and saves normalized point tables. A missing account leaves a pending result. The current delivery deliberately uses that pending state.

The initial full monthly archive is about 6 GB; the staging directory is bounded and each successfully extracted granule is removed. Cache entries are matched to granule IDs. Never mix product versions or silently substitute POWER rainfall.

## Names and refreshes

```bash
uv run climate gazetteer
uv run climate refresh-power
uv run climate refresh-global
```

Gazetteer ingestion uses the named TSV member of each ZIP, preserving curated centers. It replaces only GeoNames records. Refresh commands stage newly acquired sources; they do not replace the active release automatically. POWER release windows are pinned and extending them requires explicit method/content review.

## Contracts and distribution

```bash
uv run climate openapi
npm run generate:api -w apps/web
uv run python scripts/pack_data.py
```

`climate publish` validates the exact selected release before contacting S3, uploads only its declared public outputs/image dependencies, and publishes a pointer to that captured release last. Pinned raw input snapshots remain local rather than becoming public object-store files. Local storage works without it. Release/source inventories and validation evidence are under `data/manifests/`; downloaded inputs and image processing metadata are under `data/raw/`.
