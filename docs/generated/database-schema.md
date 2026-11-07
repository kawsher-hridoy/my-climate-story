# Application database schema

Generated from `services/api/climate/db.py`. Procrastinate manages its separate queue tables.

Relationships between IDs are application-managed; these models do not declare SQL foreign keys. JSON stores manifests/evidence. Migration-added PostGIS/trigram indexes are documented separately.

## `climate_series`

| Column | PostgreSQL type | Nullable | Primary key | Default |
|---|---|---|---|---|
| `id` | `VARCHAR(100)` | no | yes | — |
| `dataset` | `VARCHAR(100)` | no | no | — |
| `unit` | `VARCHAR(50)` | no | no | — |
| `content_hash` | `VARCHAR(64)` | no | no | — |
| `publication_state` | `VARCHAR(30)` | no | no | — |
| `payload` | `JSON` | no | no | — |

Declared indexes/constraints:

- `ix_climate_series_content_hash` (content_hash).

## `data_releases`

| Column | PostgreSQL type | Nullable | Primary key | Default |
|---|---|---|---|---|
| `id` | `VARCHAR(100)` | no | yes | — |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | no | no | Python: utcnow() |
| `manifest` | `JSON` | no | no | — |
| `status` | `VARCHAR(30)` | no | no | Python: "prepared" |

Declared indexes/constraints:

- No additional declared indexes/unique constraints beyond the primary key.

## `exploration_jobs`

| Column | PostgreSQL type | Nullable | Primary key | Default |
|---|---|---|---|---|
| `id` | `VARCHAR(36)` | no | yes | — |
| `request_key` | `VARCHAR(64)` | no | no | — |
| `release_id` | `VARCHAR(100)` | no | no | — |
| `status` | `VARCHAR(20)` | no | no | Python: "pending" |
| `story_id` | `VARCHAR(100)` | yes | no | — |
| `request_payload` | `JSON` | no | no | — |
| `message` | `TEXT` | no | no | Python: "Queued for NASA data retrieval." |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | no | no | Python: utcnow() |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | no | no | Python: utcnow() |
| `queue_job_id` | `BIGINT` | yes | no | — |
| `generation` | `INTEGER` | no | no | Python: 0; SQL: 0 |
| `dispatch_attempts` | `INTEGER` | no | no | Python: 0; SQL: 0 |
| `lease_until` | `TIMESTAMP WITH TIME ZONE` | yes | no | — |
| `run_token` | `VARCHAR(36)` | yes | no | — |
| `result_dir` | `VARCHAR(100)` | yes | no | — |
| `result_hash` | `VARCHAR(64)` | yes | no | — |

Declared indexes/constraints:

- `ix_exploration_jobs_request_key` (request_key).
- `uq_exploration_active_request` (request_key); unique; partial predicate `status IN ('pending', 'running')`.

## `imagery_pairs`

| Column | PostgreSQL type | Nullable | Primary key | Default |
|---|---|---|---|---|
| `id` | `VARCHAR(100)` | no | yes | — |
| `place_id` | `VARCHAR(100)` | no | no | — |
| `status` | `VARCHAR(30)` | no | no | — |
| `payload` | `JSON` | no | no | — |

Declared indexes/constraints:

- `ix_imagery_pairs_place_id` (place_id).

## `observations`

| Column | PostgreSQL type | Nullable | Primary key | Default |
|---|---|---|---|---|
| `id` | `INTEGER` | no | yes | — |
| `series_id` | `VARCHAR(100)` | no | no | — |
| `period` | `VARCHAR(20)` | no | no | — |
| `resolution` | `VARCHAR(20)` | no | no | — |
| `value` | `FLOAT` | yes | no | — |

Declared indexes/constraints:

- `ix_observations_series_id` (series_id).
- Unique: series_id, period, resolution.

## `place_aliases`

| Column | PostgreSQL type | Nullable | Primary key | Default |
|---|---|---|---|---|
| `id` | `INTEGER` | no | yes | — |
| `place_id` | `VARCHAR(100)` | no | no | — |
| `normalized` | `TEXT` | no | no | — |
| `name` | `TEXT` | no | no | — |

Declared indexes/constraints:

- `ix_place_aliases_normalized` (normalized).
- `ix_place_aliases_place_id` (place_id).
- Unique: place_id, normalized.

## `places`

| Column | PostgreSQL type | Nullable | Primary key | Default |
|---|---|---|---|---|
| `id` | `VARCHAR(100)` | no | yes | — |
| `name` | `VARCHAR(200)` | no | no | — |
| `name_bn` | `VARCHAR(200)` | no | no | Python: "" |
| `latitude` | `FLOAT` | no | no | — |
| `longitude` | `FLOAT` | no | no | — |
| `country` | `VARCHAR(2)` | no | no | Python: "BD" |
| `division` | `VARCHAR(200)` | no | no | Python: "" |
| `feature_type` | `VARCHAR(30)` | no | no | Python: "city" |
| `population` | `INTEGER` | no | no | Python: 0 |
| `featured` | `INTEGER` | no | no | Python: 0 |
| `payload` | `JSON` | no | no | Python: dict() |

Declared indexes/constraints:

- `ix_places_coords` (latitude, longitude).

## `publication_reviews`

| Column | PostgreSQL type | Nullable | Primary key | Default |
|---|---|---|---|---|
| `id` | `VARCHAR(100)` | no | yes | — |
| `subject` | `VARCHAR(100)` | no | no | — |
| `reviewer` | `VARCHAR(200)` | no | no | — |
| `status` | `VARCHAR(30)` | no | no | — |
| `evidence` | `JSON` | no | no | — |

Declared indexes/constraints:

- `ix_publication_reviews_subject` (subject).

## `source_requests`

| Column | PostgreSQL type | Nullable | Primary key | Default |
|---|---|---|---|---|
| `id` | `VARCHAR(64)` | no | yes | — |
| `dataset` | `VARCHAR(100)` | no | no | — |
| `release_id` | `VARCHAR(100)` | no | no | — |
| `checksum` | `VARCHAR(64)` | no | no | — |
| `metadata_json` | `JSON` | no | no | — |

Declared indexes/constraints:

- `ix_source_requests_release_id` (release_id).
