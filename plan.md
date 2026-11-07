# My Climate Story — implementation and documentation plan

## Accepted scope

Build the complete core application from `My_Climate_Story_NASA_Space_Apps.pdf` (both pages): place selection, historical image comparison, temperature/precipitation exploration, quizzes, and practical actions. The primary audience is students in grades 6–10 and teachers. The interface is Bangla first, with complete English support and a warm illustrated storybook design.

The user selected Bangladesh-first coverage with global map selection, a low-cost full-stack backend, reviewed deterministic story templates, and **reviewed imagery for all 12 supplied locations**. Student accounts, teacher dashboards, photo uploads, future projections, and messaging are later work.

**Execution amendment:** the user explicitly accepted rainfall being marked pending because no NASA Earthdata credentials are configured. Build the IMERG importer and display an honest pending component; do not substitute or manufacture rainfall measurements. This amendment permits delivery of the application with rainfall pending. The all-12 imagery requirement remains.

## Requirements and success criteria

| Requirement | Delivery |
|---|---|
| Pick a village/town/district | Featured places, local gazetteer search, map pins, coordinates, opt-in device location |
| See changes | Accessible synchronized before/after slider with real Landsat images, exact dates, sources, and QA |
| Understand records | Annual/monthly temperature, source metadata, approved descriptive decade comparisons, rainfall availability |
| Learn by playing | Five-question activities from a bilingual bank of at least 30 questions plus 12 image questions |
| Take action | Student/family/school cards; at least three relevant actions per place |
| Language accessibility | Bangla/English interface, content, explanations, labels, quiz rationales, and guides |
| Weak connectivity | Small prepared data, deferred maps/charts, complete owned-asset offline story packs |
| Global context | GISTEMP chart with explicit global scope and 1951–1980 anomaly baseline |
| Classroom use | Printable story/worksheet and 30–40 minute teacher guide |
| Scalability | Global coordinates and gazetteer; explicit availability limits on unreviewed places |

NASA POWER estimates regional grid conditions (about 0.5° × 0.625°), not a school-specific thermometer. Use “around your selected place.” Monthly data cannot count hot days, heatwaves, wet days, dry spells, or monsoon onset. Satellite differences alone do not prove climate causation.

## Evidence from the supplied data

The ZIP contains 45 files, 1,985,209 uncompressed bytes. Its SHA-256 is `467221d541546b1c4d9b535a4feafad0d711607bd35889c67e88a3d7079e94d5`. Preserve it and the PDF unchanged.

| Dataset | Verified inventory |
|---|---|
| Curated coordinates | 12 Bangladesh places |
| POWER | 12 JSON files × five variables × 585 keys (540 monthly + 45 annual) |
| Combined POWER CSV | 7,020 rows |
| Clean monthly POWER | 6,480 rows, 1981–2025 |
| Annual POWER | 540 month-13 rows |
| Existing temperature analysis | 275 rows, 11 places, 2001–2025 |
| Existing trend report | 22 rows including restricted rainfall results |
| GISTEMP | 146 annual and 1,752 monthly observations, 1880–2025 |
| IMERG | Placeholder, no measurements |
| Imagery | Empty scene catalog, no rasters |

All 35,100 combined POWER values match the supplied raw JSON. Monthly date sets are complete, unique, and free of blank/sentinel values. Temperature ordering and humidity/nonnegative-rain checks pass. A fresh NASA Dhaka request for 2024–2025 matched all 130 corresponding values; this is sample authenticity validation, not independent verification of every record.

Required corrections:

1. Regenerate annual temperature using calendar-day weighting; the existing unweighted means differ from NASA annual summaries by up to 0.0425°C.
2. Never treat `YYYY13` as a month. Preserve official annual summaries separately.
3. POWER precipitation is mm/day; monthly totals multiply by days, annual totals sum complete months. Do not publish its supplied rainfall-change claims because of the flagged ~2015–2016 discontinuity.
4. Preserve suspected ~1995–2000 temperature shifts as flags; the package's screening does not establish their cause.
5. Bhola and Barishal have identical POWER series. Preserve both places and request provenance; deduplicate numerical storage without inventing a verified grid-cell identity.
6. Existing Mann–Kendall calculations lack sufficient statistical handling. Use descriptive decade means rather than p-value stories in v1.
7. Correct stale script paths and GISTEMP missing-field documentation. Raw GISTEMP contains partial 2026; complete-year outputs stop at 2025.

## Data design

### Source catalog

| Feature | Source | Access and cutoff |
|---|---|---|
| Local temperature | NASA POWER monthly point API | Public; supplied complete 1981–2025 |
| Precipitation | GPM IMERG Final monthly V07B | Earthdata; catalog Jan 1998–Sep 2025, complete through 2024 |
| Global anomaly | NASA GISTEMP v4 | Public CSV; complete 1880–2025 |
| Historical imagery | USGS/NASA Landsat Collection 2 L2 | Public USGS STAC; matching Planetary Computer COGs |
| Regional exploration | NASA GIBS MODIS Terra | Public; starts 2000-02-24, native max zoom 9 |
| Place search | GeoNames BD.zip + cities500 + admin tables | Downloaded and indexed locally |
| Online map | Standard OpenStreetMap tiles | Human interactive viewing, attribution, normal HTTP cache |
| Offline overview | Natural Earth countries | Owned public-domain asset; not an offline street map |
| Education/actions | NASA education and UNICEF Bangladesh | Reviewed bilingual paraphrases and citations |

The first GeoNames BD snapshot contained 59,437 records, including 54,328 populated/administrative places; only 490 had Bengali-script names. Curate the 12 featured names completely. Search available aliases and retain map/coordinate fallback. Distinguish city/district names and do not claim worldwide village search completeness.

### Curated places and scene seeds

| ID | Bangla | Latitude | Longitude | Pair |
|---|---|---:|---:|---|
| dhaka | ঢাকা | 23.8103 | 90.4125 | A |
| chattogram | চট্টগ্রাম | 22.3569 | 91.7832 | B |
| khulna | খুলনা | 22.8456 | 89.5403 | A |
| rajshahi | রাজশাহী | 24.3745 | 88.6042 | C |
| sylhet | সিলেট | 24.8949 | 91.8687 | D |
| barishal | বরিশাল | 22.7010 | 90.3535 | A |
| rangpur | রংপুর | 25.7439 | 89.2752 | E |
| mymensingh | ময়মনসিংহ | 24.7471 | 90.4203 | F |
| coxs_bazar | কক্সবাজার | 21.4272 | 92.0058 | B |
| satkhira | সাতক্ষীরা | 22.7185 | 89.0705 | G |
| bhola | ভোলা | 22.6859 | 90.6482 | A |
| sunamganj | সুনামগঞ্জ | 25.0658 | 91.3950 | F |

Seven scene combinations use 14 distinct records. Exact IDs are committed in `content/imagery-candidates.json`.

| Pair | WRS | Before; scene cloud | After; scene cloud |
|---|---|---|---|
| A | 137/044 | 1990-01-07; 0% | 2025-02-08; 0.04% |
| B | 136/045 | 1990-01-16; 5% | 2025-01-16; 0.09% |
| C | 138/043 | 1990-01-30; 2% | 2025-01-14; 0% |
| D | 136/043 | 1990-01-16; 1% | 2025-01-16; 0.71% |
| E | 138/042 | 1995-01-28; 0% | 2025-01-14; 0.72% |
| F | 137/043 | 1990-01-07; 3% | 2025-02-08; 0% |
| G | 138/044 | 1990-01-30; 0% | 2025-02-15; 0.01% |

### POWER normalization and comparison

- Validate units, dates, physical bounds, sentinels, completeness, source metadata, and provenance.
- Preserve all original JSON and all variables. Derive annual mean T2M with calendar-day weighting and verify against NASA month-13 values within input rounding precision.
- Default charts to 2001–2025; expose the flagged 1981–2000 history separately.
- A decade temperature is the arithmetic mean of ten complete annual means.
- Compare 2001–2010 with 2016–2025. Round display to 0.1°C, keep full calculation precision.
- Approved explanation: “In this dataset, average temperature around [place] was [recent]°C in 2016–2025, [difference]°C higher/lower than in 2001–2010.”
- If the displayed difference is zero, explain that the decade means are similar at displayed precision. Do not infer absence of climate change or statistical significance.

Publication states are `unavailable`, `provisional`, `descriptive_only`, and `comparison_approved`. A comparison needs verified source/units/aggregation, complete windows, passing checks, and a scoped review record. Automatically fetched global points are provisional. Jobs cannot promote them to approved.

### IMERG acquisition

- Short name `GPM_3IMERGM`, version `07`, collection `C2723754851-GES_DISC`, DOI `10.5067/GPM/IMERG/3B-MONTH/07`.
- Discover and pin CMR granules. The inspected catalog had 333 consecutive months, including 324 months in complete 1998–2024 years.
- Use Earthdata server secrets and `earthaccess`. Download one ~18 MB file at a time, extracting every preset independently.
- Read `Grid/precipitation`, dimensions `(time, lon, lat)`, native mm/hr, documented missing marker -9999.9; normalize attribute names and verify units per file.
- Monthly mm = rate × 24 × calendar days. Annual mm = sum of 12 valid months. Bangladesh JJAS total requires all four June–September months.
- Record native 0.1° cell center/bounds. Bhola and Barishal must be independently sampled.
- Initial comparison windows are 2001–2010 and 2015–2024. Do not join POWER rain into IMERG.
- Keep partial years monthly-only. Determine future cutoffs from available complete granules.
- For global points, constrain/cache OPeNDAP subsets only after matching authenticated full-file extraction. Otherwise return pending/unavailable precipitation while temperature works.
- The ~6 GB initial archive must be streamed, with bounded staging storage and cleanup. No full-history synchronous downloads on map clicks.

### Imagery processing and approval

- Preserve official STAC JSON, stable item URLs, source checksums, QA metadata, and retrieval manifests. Sign COG URLs only at retrieval time.
- Construct a projected 20 km square for each curated coordinate. Validate its full polygon against both footprints.
- Read semantic RGB, QA_PIXEL, and QA_RADSAT windows. Landsat 5 and 8 use different band/QA mappings.
- Apply reflectance scaling, offset, fill, cloud/dilated-cloud/shadow/snow masks and sensor-specific cirrus/saturation/dropped-pixel rules. Keep water.
- Require ≥95% valid AOI pixels and visual review of haze/feature coverage.
- Reproject both windows to one 30 m grid, bounds, and dimensions. Apply one shared documented display transform.
- Produce owned WebP images and thumbnails with dates, sources, dimensions, bytes, checksums, valid fraction, resolution, caption, and alt text.
- If a candidate fails, search January–February alternatives in 1985–1995 / 2020–2025. Do not force identical years across places.
- Review all 12 crops/captions. City-center Khulna/Satkhira crops must not be described as Sundarbans/coastline unless visible. Do not quantify climate causation from images.

### GISTEMP and GIBS

GISTEMP is explicitly global land–ocean anomaly relative to 1951–1980, never local absolute temperature. Parse headers/missing markers, keep annual/monthly/seasonal fields separate, and exclude incomplete years from annual outputs.

GIBS uses the EPSG3857 `GoogleMapsCompatible_Level9` matrix and `maxNativeZoom:9`. Discover valid dates; label actual dates, handle gaps, and distinguish regional MODIS exploration from curated 30 m Landsat comparisons. No 1980s GIBS images or silent date snapping.

## Frontend implementation

Use React/TypeScript/Vite, React Router, React Leaflet, Chart.js, TanStack Query, i18next, Dexie, Workbox PWA, CSS tokens, self-hosted Bengali/Latin fonts, and accessible controls. Production build uses Node 24; supported local Node 22 is also acceptable.

### Screens and flow

Routes: `/{locale}/`, `/explore`, `/story/{placeId}`, `/explore/point`, `/saved`, `/learn`, `/teachers`, `/sources`, `/about`. Default Bangla; explicit route language then saved preference. Preserve place/chapter when changing language.

Journey: choose place → imagery → temperature/rainfall → global context → five-question activity → action → save/print. Chapters remain independently accessible. Desktop uses generous editorial columns; mobile uses stacked cards, a clear chapter navigator, and touch-sized controls.

Home uses a warm cream/green palette, an original vector landscape, clear NASA-source attribution, featured places, and no invented scientific numbers. Stories show source, unit, actual period, quality/availability, and represented-area explanation per component.

### Controls

- Search is debounced and limited to ten results; map click commits only on a deliberate exploration action. Provide coordinate fields and opt-in geolocation.
- Image divider supports pointer and keyboard input, exact dates, alternative side-by-side view, scale, alt text, captions, and source drawer.
- Temperature charts expose annual and monthly views plus an accessible table and CSV. Missing values create gaps.
- Rainfall honestly shows pending state until IMERG is ingested. No fake charts or POWER change narratives.
- Global chart labels the anomaly baseline prominently.
- Five questions use reviewed bilingual prompts/options/rationales and image questions where approved. Results and action checkboxes are local only.

### Offline and accessibility

Packs include both languages, source/release metadata, series, owned imagery, quizzes/actions, checksums, and a Natural Earth overview. Show size, verify before completion, support retry/interruption/delete/quota errors. Maximum 20 packs or 100 MB. Replace a pack only after the new one completes. Standard OSM street tiles are not prefetched or packaged.

Target WCAG 2.2 AA: keyboard controls, focus visibility, logical headings, tables for charts, reduced motion, non-color labels, 200% zoom, readable Bangla, 360 px layout, and print formatting. Target initial JS ≤200 KB compressed excluding deferred map/chart modules, story JSON ≤100 KB compressed, image pair ≤600 KB where quality allows, and packs around ≤2 MB.

## Backend and interfaces

Use Python 3.12, FastAPI/Pydantic, SQLAlchemy/Alembic, PostgreSQL 17/PostGIS, Procrastinate, and a single heavy worker. Scientific tooling includes numpy/pandas/xarray/earthaccess/rasterio/pyproj/Pillow. Caddy serves one frontend/API origin. Local artifacts work without S3; production can publish to S3-compatible storage/R2.

Browser → prepared story/API → PostgreSQL catalog + durable jobs. Worker → fixed NASA/USGS/mirror endpoints → validated immutable releases and owned assets. No student accounts or public administration endpoints.

Data model: Place/Alias, Dataset/SourceRequest, DataRelease, ClimateSeries/Observation, Comparison/PublicationReview, ImageryScene/Pair, version-controlled ContentRelease, StoryManifest, and durable exploration jobs. Preserve request provenance when deduplicating series. Constrain duplicate observations/granules and use indexed place search.

API prefix `/api/v1`:

| Endpoint | Contract |
|---|---|
| GET /config | Current release, locales, map layers, capabilities |
| GET /places/featured | Curated places |
| GET /places/search | Query/locale/limit, named results and coverage note |
| GET /places/{id} | Names, coordinates, source/admin context |
| GET /stories/{id} | Versioned prepared manifest |
| POST /explorations | Exactly one stable place ID or finite coordinates; available story or job |
| GET /jobs/{id} | Pending/running/completed/failed, result URL, retry guidance |
| GET /series/{id} | Observations, source, units, quality, release |
| GET /imagery/pairs/{id} | Approved assets and processing metadata |
| GET /sources/{id} | Citation, periods, resolutions, limitations |
| GET /releases/{id} | Version and evidence manifest |
| GET /exports/{id}.csv | Measurements with source/unit metadata |
| GET /health/live, /health/ready | Process/local dependency readiness |

Generate frontend types from OpenAPI. Stable DTOs include Place, SourceMetadata, ClimateComponent, Comparison, ImageryPair, StoryManifest, JobStatus, and ApiError.

### Reliability and privacy

Use durable deduplicated jobs, bounded retries, terminal failures, upstream timeouts/Retry-After, one heavy task, and ≤2 POWER calls concurrently. Validate real file signatures: a login HTML response is not imagery. Keep last approved release on refresh failures. Immutable URLs/ETags; no silent release replacement.

Bound expensive exploration to five requests/minute/client and a finite global queue. Accept no arbitrary provider URL/path/expression. Use server secrets/host allowlists/HTTPS/same origin. Avoid coordinates or tokens in ordinary logs. Share custom coordinates only through an explicit share action. Local quiz data is not uploaded.

## Documentation

Create tested, current documentation for the entire app:

| File | Contents |
|---|---|
| README.md | Purpose, prerequisites, quick start, commands, screenshots, limitations |
| docs/requirements.md | PDF mapping, acceptance, scientific corrections |
| docs/architecture.md | Component/data-flow diagrams and decisions |
| docs/frontend.md | Routes, components, tokens, state, accessibility |
| docs/backend.md | Services/jobs/cache/errors/configuration |
| docs/api.md + openapi.json | Endpoints/examples/errors/generated schemas |
| docs/database.md | Entities, constraints, migrations, retention/restoration |
| docs/data-catalog.md | Every dataset/variable/unit/period/resolution/license |
| docs/data-pipeline.md | Reproducible acquisition/validation/release commands |
| docs/scientific-methodology.md | Aggregation/windows/flags/interpretation |
| docs/imagery.md | Scenes, QA/alignment/display/review evidence |
| docs/content-and-localization.md | Schemas, glossary, content/review rules |
| docs/offline.md | Pack format/limits/update/failure behavior |
| docs/testing.md | Suites, fixtures, manual checks, acceptance |
| docs/deployment.md | Docker/TLS/secrets/backup/rollback |
| docs/operations.md | Refresh, failed jobs, monitoring, cleanup |
| docs/teacher-guide.md | 30–40 minute lesson and worksheet |
| docs/user-guide.md | Bangla and English student instructions |
| docs/sources-and-licenses.md | NASA/maps/fonts/illustration/content credits |
| docs/decisions/ | Significant architecture/science decisions |

Also provide secret-free environment examples, reproducible manifests, example story JSON, release notes, changelog, and troubleshooting. A published measurement/image must be traceable back to its source and processing release.

## Tests and release acceptance

- Data: raw equality/counts, weighted annual means, month 13, leap-year rain, nulls/duplicates/incomplete years, IMERG dimension/cell mapping, Bhola/Barishal identity, GISTEMP baseline, publication-policy blocks, reproducibility.
- Imagery: real file content, semantic bands, scaling/masks, shared grid/transform, ≥95% validity, correct dates/sources, all-12 visual review.
- API: schema/coordinate validation, search, deduplication, quotas, retries/failures, provisional publication, migrations/restore/rollback.
- UI: bilingual navigation, selection, chart/table parity, keyboard slider, quizzes/local state, offline interrupted save/update, print/CSV, narrow screens, accessibility.
- Real-browser acceptance for each of 12 places: open Bangla → choose → approved image pair → temperature/source → pending rainfall explanation → quiz/action → save → network off → reopen → English switch.
- Global acceptance covers pending/provisional/unavailable components without false precision or approved narratives.

Completion under the execution amendment means all core software, all-12 imagery, bilingual content, offline behavior, tests, and current documentation work; IMERG ingestion is implemented with rainfall explicitly pending. No public deployment is claimed without a configured production host.

## Milestones and operations

1. Establish monorepo, environment, dependency locks, database/worker, documentation.
2. Import and validate POWER/GISTEMP, gazetteer; implement IMERG acquisition and pending state.
3. Process/review all 12 imagery pairs.
4. Implement API contracts, durable exploration, exports, release tooling.
5. Implement warm bilingual student screens, maps/slider/charts/sources.
6. Complete question/action banks, classroom/print/offline/local progress.
7. Run scientific, accessibility, performance, browser, clean-install checks; finalize docs.
8. Verify local Docker production build, backups and rollback. A public host requires a configured domain/server.

Production default: modest Linux VPS (~2 vCPU/4 GB RAM/80 GB disk), Docker Compose Caddy/API/worker/PostgreSQL, optional S3/R2 artifacts, daily encrypted backups, monthly discovery, and deliberate promotion of validated releases. Monitor latency/errors/jobs/freshness/storage/backups; deploy code and data independently.

Future work: teacher classes, moderated community photos, daily extreme indices, NEX-GDDP-CMIP6 projections, sea-level context, more languages, SMS/WhatsApp, reviewed global imagery, global precipitation Zarr if scale warrants it.

## References

- https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/
- https://data.giss.nasa.gov/gistemp/
- https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imergm-07
- https://cmr.earthdata.nasa.gov/search/granules.json?collection_concept_id=C2723754851-GES_DISC&page_size=2000&sort_key=start_date
- https://github.com/nasa/gesdisc-tutorials/blob/main/notebooks/How_to_Read_IMERG_Data_Using_Python.ipynb
- https://www.usgs.gov/landsat-missions/spatiotemporal-asset-catalog-stac
- https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands
- https://planetarycomputer.microsoft.com/dataset/landsat-c2-l2
- https://nasa-gibs.github.io/gibs-api-docs/access-basics/
- https://download.geonames.org/export/dump/readme.txt
- https://operations.osmfoundation.org/policies/tiles/
- https://www.naturalearthdata.com/about/terms-of-use/
- https://science.nasa.gov/kids/earth/
- https://www.unicef.org/bangladesh/en/press-releases/children-are-high-risk-amid-countrywide-heatwave-bangladesh
