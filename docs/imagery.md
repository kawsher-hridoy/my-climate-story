# Historical imagery and visual review

Every first-release location has an approved historical and recent image. There are 12 pairs, using 14 distinct Landsat scenes. These are real Collection 2 Level 2 surface-reflectance sources, not illustrative or AI-created satellite views.

## Scene groups

| Group | Locations | WRS path/row | Historical | Recent |
|---|---|---|---|---|
| A | Dhaka, Khulna, Barishal, Bhola | 137/044 | 1990-01-07 | 2025-02-08 |
| B | Chattogram, Cox’s Bazar | 136/045 | 1990-01-16 | 2025-01-16 |
| C | Rajshahi | 138/043 | 1990-01-30 | 2025-01-14 |
| D | Sylhet | 136/043 | 1990-01-16 | 2025-01-16 |
| E | Rangpur | 138/042 | 1995-01-28 | 2025-01-14 |
| F | Mymensingh, Sunamganj | 137/043 | 1990-01-07 | 2025-02-08 |
| G | Satkhira | 138/044 | 1990-01-30 | 2025-02-15 |

Exact identifiers are in `content/imagery-candidates.json`. The official source URL for an ID is `https://landsatlook.usgs.gov/stac-server/collections/landsat-c2l2-sr/items/{id}`. Matching Planetary Computer item IDs omit processing date and `_SR`.

## Retrieval

Official USGS metadata is public. Its asset links can redirect to a login page; HTTP 200 alone is insufficient. The processor retrieves matching Planetary Computer COG assets using temporary signed URLs, which are never placed in public manifests. Source attribution remains USGS/NASA Landsat, with Planetary Computer named as host.

## Shared processing

- Center a projected approximately 20 km square on the supplied coordinate.
- Validate full polygon containment in each source footprint.
- Read semantic RGB and QA_PIXEL/QA_RADSAT windows.
- Source optical resolution: 30 m; output grid: 667 × 667 pixels, a 20.01 km square.
- Surface reflectance: scale `0.0000275`, offset `−0.2`.
- Fixed display range: 0–0.30 reflectance, gamma 1.5; same transform for both dates.
- Mask fill, dilated cloud, cloud, shadow, snow and relevant saturation. Apply cirrus only where sensor-defined, and TM dropped-pixel handling. Preserve water.
- Align the same CRS, bounds, grid and dimensions; preserve native-resolution attribution.
- Render invalid pixels pale and disclose them in captions.

No independent image auto-contrast is used to manufacture differences. Homepage thumbnails may crop/desaturate for navigation; use the full comparison for inspection.

## Acceptance and evidence

All 24 images passed ≥95% valid coverage; the lowest inspected fraction was approximately 98.5%. Six contact sheets under `output/imagery-review/` were visually inspected. Review records in `content/imagery-reviews.json` bind the specific checksums to a named reviewer and location-specific evidence.

Historical haze is stronger in some crops, particularly Chattogram. It is explicitly disclosed. Visible shapes remain suitable for qualitative comparison; colors are not treated as a quantitative vegetation classification.

Rajshahi has some masked historical patches; they are displayed and described. Khulna/Satkhira are city-centered views and are not labeled as Sundarbans or coastline evidence. Water, tide, sediment, season and human activity remain possible influences in river/coastal stories.

## Changes and failures

If an image changes, its checksum-specific review no longer applies. Inspect the new crop and source metadata before approving it. If a candidate fails, choose another January–February scene within the documented historical/recent windows and update the manifest with its actual date. Do not pretend an unavailable scene was acquired.

Cached pairs are reconciled against current scene candidates, requested crop, display/QA policy, owned image bytes and canonical review records on every preparation/build. A changed, removed or withdrawn review clears approval. Changed candidates or processing evidence require regeneration; the cache status alone is never treated as approval. Release validation independently checks the same bindings against pinned inputs, and publication also verifies that the current authority still agrees.

Use `uv run climate imagery --places dhaka` for a focused acquisition and `uv run climate review-imagery` only after review. The UI displays an image pair only when its status is `approved`.
