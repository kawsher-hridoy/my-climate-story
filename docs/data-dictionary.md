# Data dictionary and contracts

The application uses Pydantic models in `services/api/climate/schemas.py`. Generated references are [Story JSON Schema](generated/story-json-schema.json), [exploration request JSON Schema](generated/exploration-json-schema.json), [OpenAPI](openapi.json) and [SQL columns/constraints](generated/database-schema.md). Frontend types are generated into `apps/web/src/lib/api.generated.ts`.

This guide explains field meaning. Required/default rules and precise validation are in the generated schemas. JSON numbers retain processing precision; presentation rounds/localizes them. A `null` observation means missing/unknown, never zero.

## Top-level story

| Field | Type | Meaning / consumer |
|---|---|---|
| `schema_version` | Integer, currently 1 | Public story payload version; distinct from release format 2 |
| `place` | Place object | Selected name, coordinate, description, tags |
| `release` | ReleaseRef object | Version, provenance timestamp, content/processing versions and rainfall availability |
| `temperature` | ClimateComponent | Local/regional temperature chart, table, comparison and export |
| `rainfall` | ClimateComponent | IMERG component or explicit unavailable state |
| `global_context` | GlobalContext | Separate GISTEMP anomaly chart/context |
| `imagery` | ImageryPair | Historical/recent satellite evidence and review |
| `quiz` | QuizQuestion array | Five deterministic questions for each current curated activity |
| `actions` | ActionCard array | Four current relevant student/family/school activities |

The returned manifest contains both languages. It is the complete document saved for offline use; the browser does not recalculate annual means or approve a comparison.

## Shared values

`Localized` is `{ "bn": "...", "en": "..." }`. Both strings are required. `Coordinates` is `{ "latitude": number, "longitude": number }`; latitude must be finite and −90…90, longitude finite and −180…180.

IDs are identifiers, not translated labels. Use the corresponding `name`, `title`, `description`, `question` or `explanation` for display. Dates are ISO dates; source/review/release timestamps retain timezone information.

## Place

| Field | Type / default | Meaning |
|---|---|---|
| `id` | String | Curated slug, `geonames-...`, or generated `point-...` |
| `name` | Localized | Display name; gazetteer fallback may use its source name for both languages |
| `division` | String | Administrative context, not boundary geometry |
| `coordinates` | Coordinates | Selected point, not assumed exact instrument or verified POWER grid-cell center |
| `aliases` | String array, empty | Search names; curated names are reviewed |
| `tags` | String array, empty | Relevance tags such as `urban`, `river`, `agriculture`, `heat` |
| `featured` | Boolean, true | Prepared curated story versus provisional/global point |
| `feature_type` | String, `city` | Gazetteer/point classification |
| `country` | String, `BD` | Country code or blank for unnamed coordinates |
| `description` | Localized | Story introduction or provisional-place explanation |
| `preview_image_url` | String or null | Approved recent thumbnail used by featured cards |

## SourceMetadata

| Field | Meaning |
|---|---|
| `id` | `nasa-power`, `nasa-gistemp` or `nasa-imerg` |
| `name`, `version` | Provider/product and selected processing/product version |
| `unit` | °C for local air temperature, °C anomaly for GISTEMP, mm for accumulated IMERG rainfall |
| `source_url`, `citation` | Stable public source documentation and citation |
| `spatial_resolution` | Represented grid/global scale; not a house-level accuracy claim |
| `start`, `end` | Source period labels; pending source labels are not evidence that measurements were acquired |
| `retrieved_at` | Acquisition/provenance timestamp |
| `license` | Source license attribution label |
| `notes` | Bilingual scale/interpretation explanation |

Use a pinned story's embedded source for that story. `/sources/{id}` returns active-release general metadata and has no release parameter.

## ClimateComponent

| Field | Type | Meaning |
|---|---|---|
| `series_id` | String | Place/release-specific prepared component or global story series ID |
| `publication_state` | Enum | Interpretation state, defined below |
| `source` | SourceMetadata | Product, period, units and represented area |
| `annual` | AnnualObservation array | Year, value, completeness; empty when unavailable |
| `monthly` | MonthlyObservation array | Month date and value; empty when unavailable |
| `comparison` | Comparison or null | Reviewed descriptive decade arithmetic, not regression/causal attribution |
| `warning` | Localized or null | Data quality/scale/review caveat |
| `quality_flags` | String array | Processing/availability flags; source-specific explanations |
| `shared_series_with` | String array | Places with identical supplied normalized values; metadata still stays separate |
| `requested_coordinates` | Coordinates or null | Point for which values were requested |
| `native_cell_center` | Coordinates or null | Verified sampled cell center when available, such as acquired IMERG; not inferred from POWER geometry |
| `native_cell_bounds` | Number array or null | Optional verified native bounds; not filled with invented geometry |

`AnnualObservation` has `year: integer`, `value: number|null`, `complete: boolean` (default true). `MonthlyObservation` has `date: string` and `value: number|null`; current month dates use `YYYY-MM-01`.

For temperature, both resolutions carry °C. For acquired rainfall, a monthly value is accumulated mm/month and an annual value is accumulated mm/year; period/resolution supplies the duration while `source.unit` is `mm`. Native rates remain in raw IMERG samples. For GISTEMP, annual values are global °C anomalies.

## Interpretation states

| Climate state | Allowed interpretation | Current examples |
|---|---|---|
| `unavailable` | No usable measurements; explicit explanation and empty arrays | Pending IMERG rainfall |
| `provisional` | Newly acquired regional data without local review; no approved comparison | Global point temperature |
| `descriptive_only` | Observations may be read; reviewed change comparison absent | Curated data without matching comparison review; future acquired IMERG before review |
| `comparison_approved` | Scoped descriptive arithmetic comparison with exact review binding | Current twelve curated temperature components |

These states do not constitute statistical significance, homogeneity testing or causal attribution. Imagery has its own independent status enum.

## Comparison

| Field | Meaning |
|---|---|
| `baseline_period`, `recent_period` | Complete windows, currently 2001–2010 and 2016–2025 |
| `baseline_value`, `recent_value` | Mean of ten complete annual means for each window |
| `difference` | Recent mean minus baseline mean; retained at calculation precision |
| `unit` | °C for current local comparison |
| `publication_state` | Scoped approval state |
| `method` | Literal `complete-decade-means` |
| `review_id` | Matching source-hash/window review identifier |
| `explanation` | Bilingual copy generated from approved arithmetic; zero-rounded differences use similar-precision wording |

`GlobalContext` separately has `source`, `baseline` (1951–1980) and `annual`. It is not a local ClimateComponent and has no standalone global series API in the current implementation.

## ImageryPair and ImageryAsset

| Pair field | Meaning |
|---|---|
| `id` | Curated place/pair identifier |
| `status` | `pending`, `needs_review`, `approved`, `unavailable` |
| `before`, `after` | ImageryAsset or null; displayed as the scientific comparison only when approved |
| `bounds`, `crs` | Shared processed crop bounds and projected coordinate reference system; interpret bounds in that CRS |
| `resolution_m` | 30 m native optical/output grid spacing |
| `attribution` | USGS/NASA producer, Planetary Computer host and processing credit |
| `processing_version` | Version of crop/display/QA processing |
| `caption` | Bilingual qualitative interpretation limits |
| `review` | Canonical checksum-bound review details or null |
| `error` | Optional processing failure information |

| Asset field | Meaning |
|---|---|
| `url`, `thumbnail_url` | Stable owned main and navigation-preview paths |
| `date`, `sensor`, `product_id` | Actual acquisition date, instrument/product identity |
| `source_url` | Stable USGS metadata URL; not a temporary signed COG URL |
| `sha256` | Exact main WebP byte checksum |
| `width`, `height`, `bytes` | Main image dimensions and byte count |
| `valid_pixel_fraction` | Valid pixel fraction after masking; not classification accuracy |
| `scene_cloud_percent` | Source scene-level cloud metadata; distinct from crop valid fraction |
| `alt` | Bilingual scientific-image description |

Current crops are 667 × 667 on the common 30 m grid, approximately 20.01 km across. Thumbnail rendering is for navigation; scientific interpretation uses the full processed pair. RGB differences cannot identify a single cause.

## Quiz and actions

`QuizQuestion`: `id`, `category`, bilingual `question`, bilingual `options[]`, zero-based `correct_index`, bilingual `explanation`, `source_url`, and `image_question` (default false). The correct index refers to the serialized shuffled options. Image questions use the actual reviewed historical date; selecting a language does not reshuffle them.

`ActionCard`: `id`, relevance `tags[]`, `audience` (`student|family|school`), bilingual `title`, bilingual `description`, and `source_url`. Chosen action IDs stay on the device; the backend does not record participation.

## ReleaseRef and full release manifest

`ReleaseRef` embeds `id`, `created_at`, `processing_version`, `content_version`, and `rainfall_pending`. `created_at` is a stable effective pinned-input time, not necessarily the wall-clock time when the current container was started.

The full `release.json` adds format, publication state, full identity, input/output/asset hashes, selected source requests, archive inventory, place IDs, approved counts, source periods, question count and the accepted rainfall amendment. `GET /releases/{id}` returns this manifest; it does not serve the pinned raw input directory.

Release format 2 and story schema version 1 are independent version numbers. The active pointer is only `{ "id": "mcs-..." }` and must reference an existing validated release.

## Exploration contracts

Request exactly one of `place_id` or `coordinates`. Extra top-level fields are forbidden. `place_id` is 1–100 characters matching letters/numbers/underscore/hyphen. Coordinates use finite bounded numbers. HTTP 200 returns a prepared/completed `story`; HTTP 202 returns a `job`.

`JobStatus` fields: `id`, `status` (`pending|running|completed|failed`), nullable `story_id`, nullable `story_url`, `message`, and `retry_after` (default 5 seconds). `ExplorationResponse` carries nullable `story` and `job`; clients inspect the HTTP status/result rather than assuming a story is always present.

Application HTTP errors use `{ "code": "http_...", "message": "..." }`. Pydantic request validation uses FastAPI's `detail` array. A 404 export for unavailable rainfall means no measurements, not a CSV of zeros.

## Browser stores

Database name: `my-climate-story-v1`, Dexie schema version 1.

| Store / record | Fields / meaning |
|---|---|
| `packs` | `id`, full `story`, `release`, `bytes`, `savedAt`, `assets[]`, optional `mediaStatus`, `missingAssets[]`, `mediaStorageVersion` |
| `progress` | `id`, selected `answers[]`, `questionIndex`, `finished`, selected `actions[]` |
| `packs` indexes | `id` primary key; `release`, `savedAt` indexes |
| `progress` key | `id`; quiz keys include content version; action keys use place ID |

Pack `mediaStatus` is `complete` or `incomplete`; old records migrate and get storage version 1. Repair restores the pack's pinned story, while Update selects the latest story. One pack per place is retained; replacing/updating a pack checks shared media references. The current limit is 20 packs/100 MB of counted content.

Cache names: `climate-pack-media-v1` for explicit packs; `climate-media-v2` for ordinary media; `climate-api-v1` for eligible API reads; Workbox's scoped precache for the app shell. Storage is device/browser/origin local. Clearing browser data or changing the tunnel origin creates a new storage context.

## SQL schema

See [generated database schema](generated/database-schema.md) for every current application column, PostgreSQL type, nullability, default, primary key, index and uniqueness constraint. [Database documentation](database.md) explains seeding, migrations, authority and application-managed relationships.

JSON fields preserve prepared payloads/evidence; SQL observation values are nullable. The uniqueness rule is `(series_id, period, resolution)`, so monthly and annual rows cannot overwrite each other. Queue DDL belongs to the installed Procrastinate version and is initialized with `climate queue-schema`.

Regenerate these references after model/release changes with `uv run python scripts/generate_documentation.py`. After an API schema change also regenerate OpenAPI and frontend types using the commands in [API documentation](api.md).
