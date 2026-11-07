# Troubleshooting

| Symptom | Check and resolution |
|---|---|
| UI cannot load featured stories | Verify API/readiness and active data pointer; run bootstrap/build and seed |
| Development proxy returns 500 | Confirm the API is running on port 8000; inspect logs before retrying |
| Blank or unavailable image pair | Check processing/review status and owned asset files; the UI suppresses unapproved pairs |
| Metadata fetch succeeds but image is HTML | A source login redirect is not image data; use the verified Landsat mirror pipeline |
| Temporary satellite request failure | Use bounded retries; do not expose signed URLs in error output |
| Rainfall chapter is pending | Expected for this release; configure Earthdata locally and run the importer if measurements are required |
| IMERG authentication fails | Check local environment configuration and Earthdata account access; never paste secrets into logs/issues |
| No place-search match in Bangla | Alias coverage is incomplete; try another spelling, map pin or coordinates |
| Global request stays pending | Confirm a worker and queue schema are running; inspect job message and queue age |
| New global story has no change explanation | Expected: the series is provisional until a scoped review |
| Saving fails | Wait for the production offline shell, check connection/quota, and retry; incomplete packs are not committed |
| Offline street map is unavailable | Expected: standard OSM tiles are not packaged; use the saved story/overview |
| Docker cannot bind localhost:8088 | Inspect existing listeners and choose an explicit alternative port mapping |
| Database migration fails | Inspect the error, verify PostGIS permissions and correct database; migrations are separate from raw source files |

## Useful commands

```bash
docker compose -f infra/compose.yml ps
docker compose -f infra/compose.yml logs --tail=50 api worker
uv run climate validate
uv run climate openapi
npm run typecheck
```

Use a focused imagery acquisition with `--places` when investigating a scene. Do not approve a missing, changed or cloud-obscured crop just to clear a pending UI state.

If the source changes, preserve the old files, stage the new acquisition and produce a new release. Existing review hashes must not be rewritten to falsely match a changed dataset.
