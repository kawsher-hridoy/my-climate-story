# First release

## 2026-11-08 reliability update

All 11 [review findings](code-review.md) are fixed. The update adds transactional exploration dispatch and bounded recovery, verified atomic result bundles, validated immutable format 2 releases, place-specific series provenance, canonical imagery-review reconciliation, persistent offline media with legacy migration/repair, proxy-aware client limits and safely quoted database credentials. The updated application is deployed locally with 67 passing Python tests and 17 passing frontend tests. See [fix report](review-fixes.md) and [verification](verification.md).

## Delivered functionality

Delivered scope:

- Bangla/English student interface with a warm illustrated design.
- Twelve curated Bangladesh stories and 24 retrieved, aligned, QA-checked and visually reviewed Landsat images.
- Corrected 1981–2025 temperature records, default 2001–2025 view, scoped descriptive decade comparisons and global GISTEMP context.
- Gazetteer search, coordinate/map selection and durable provisional global-temperature requests.
- Thirty bilingual reusable questions, source-backed image questions, local progress and relevant actions.
- Offline packs with checksums, source/release metadata, both languages and owned media.
- Printable classroom guide and complete engineering/data/operations documentation.
- Docker production build, database migrations and reproducible source/release tooling.

Accepted limitation: NASA IMERG measurements remain pending until backend Earthdata access is configured. Global imagery comparisons and numerical change narratives are not automatically approved. Student/teacher accounts, uploads, projections and messaging remain later work.

See [testing](testing.md) and `data/manifests/validation.json` for current evidence. The local production app is served at http://localhost:8088; no public host/domain was supplied.
