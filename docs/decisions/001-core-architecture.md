# Decision 001: prepared stories and a small full-stack service

Status: accepted and implemented.

The PDF proposes a lightweight browser-only app, while the user explicitly requested a complete backend and low-cost deployment. Large imagery processing, data validation and source credentials need a server boundary.

Use a static React PWA, FastAPI, PostgreSQL/PostGIS and one Procrastinate worker, served on one origin by Caddy. Publish small prepared JSON and owned image assets. This avoids runtime language-model dependency and keeps the student flow usable with weak connectivity.

Reviewed templates bind explanations to actual calculations. Global requests are provisional. Student progress and packs remain local. Future accounts, projections, community photos and messaging require separate designs.
