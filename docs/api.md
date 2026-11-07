# API reference

Base path: `/api/v1`. Interactive documentation is at `/docs` on the API server. [OpenAPI JSON](openapi.json) is generated from Pydantic models; frontend TypeScript types are generated from that file.

Native API `/docs` and `/openapi.json` are available on localhost:8000. The production Caddy configuration proxies `/api` and `/media`, so it does not expose those native documentation routes; use the committed OpenAPI file for the production contract. See the [data dictionary](data-dictionary.md) and [data usage map](data-usage.md) for field meaning and source ownership.

## Endpoints

| Method/path | Result |
|---|---|
| GET `/config` | Active release, supported languages, rainfall/imagery availability and map configuration |
| GET `/places/featured` | Twelve bilingual curated places, including approved preview images |
| GET `/places/search?q=…&locale=bn&limit=10` | Literal alias/name search; query length 2–100, limit 1–10 |
| GET `/places/{id}` | Gazetteer or curated place details |
| GET `/stories/{id}?release=…&locale=bn` | Complete bilingual story; omit release for current version |
| POST `/explorations` | Prepared story or durable retrieval job |
| GET `/jobs/{id}` | State, message, result URL and polling guidance |
| GET `/series/{id}?release=…` | Observations, units, source, quality and comparison status |
| GET `/imagery/pairs/{id}?release=…` | Pair metadata, asset URLs, QA and review |
| GET `/sources/{id}` | `nasa-power`, `nasa-gistemp`, or `nasa-imerg` |
| GET `/releases/{id}` | Release manifest and source-request evidence |
| GET `/exports/{id}.csv?release=…` | Period, resolution, value, unit, dataset, release and publication state |
| GET `/health/live` | Process liveness |
| GET `/health/ready` | Prepared release and database readiness |

## Exploration requests

Provide exactly one location form:

```json
{"place_id":"dhaka"}
```

```json
{"coordinates":{"latitude":52.52,"longitude":13.405}}
```

Latitude must be finite and within −90…90; longitude within −180…180. Extra request fields are rejected. A prepared result is HTTP 200 with `story`. A queued result is HTTP 202 with `job`; poll its ID until terminal state.

```json
{"story":null,"job":{"id":"<uuid>","status":"pending","story_id":null,"story_url":null,"message":"Queued for NASA data retrieval.","retry_after":5}}
```

Both localized versions are returned; locale selects the client presentation rather than discarding offline content.

## Publication and availability

Climate states: `unavailable`, `provisional`, `descriptive_only`, `comparison_approved`. Imagery states: `pending`, `needs_review`, `approved`, `unavailable`. These are distinct: imagery processing approval does not approve a climate inference.

The pending IMERG component contains empty observation arrays and no comparison. A new global temperature series is provisional and receives no automatic numerical change explanation.

## Versioning, errors and exports

Pinned story reads use immutable cache headers; current reads have a short cache lifetime. Stories have an ETag. Preserve a manifest's release ID when requesting its series/export.

Those immutable headers apply to curated pinned stories. Global result stories require verified completed job artifacts and use `no-store`. `/sources/{id}` always selects general metadata from the active release; an older pinned story carries its own embedded source metadata. The generic source page in the frontend is authored educational guidance.

HTTP 404 means an unknown/unavailable resource, 422 means invalid input, 429 means a client limit, and 503 means unavailable local dependencies or a full/unavailable queue. Application HTTP errors use `{code,message}`; schema validation uses FastAPI's `detail` array.

CSV keeps missing values empty and never converts them to zero. Temperature values are °C; precipitation accumulation values are millimeters with the period/resolution carried separately.

The UI temperature CSV button generates its download locally from the embedded component and works offline. The API export endpoint is an equivalent external-client route. GISTEMP is an embedded global context, not a standalone series/export endpoint in the current implementation. Unavailable rainfall export returns 404.

Generate contracts after a schema change:

```bash
uv run climate openapi
npm run generate:api -w apps/web
npm run typecheck
```
