# Security and privacy behavior

This describes the implemented data movement and boundaries. It is operational documentation, not a certification of regulatory compliance.

## Student data

| Data | Destination | Retention / controls |
|---|---|---|
| Language preference | `localStorage['climate-locale']` | This device/origin; browser-data clearing removes it |
| Quiz answers/action choices | IndexedDB `progress` | Device only; no API submission or account synchronization |
| Saved stories/images | IndexedDB `packs` and Cache Storage | Device/origin only; remove packs or clear browser data |
| Selected coordinate/name for exploration | Backend job payload, NASA POWER request, completed source/result bundle | Operational provenance until operator retention/cleanup |
| Client address for rate limiting | API process derives an ephemeral fingerprint for the current date/bucket | In-memory request-window limiter; not a student profile |
| Online map requests | OSM or NASA GIBS tile provider | Provider receives normal network/tile requests; map use has attribution |
| Public tunnel traffic | Cloudflare when a quick tunnel is running | Temporary access path; provider handling is separate from device-local app progress |

Geolocation is opt-in through the browser. A new exploration sends its selected location to the backend and POWER. Coordinates are needed for acquisition and remain in source/job evidence even though ordinary API access logging is disabled. The app does not provide private per-user ownership of result URLs.

## Server boundaries

The public app has read/search/exploration/export routes; there is no public upload, content administration, arbitrary upstream-URL input or credential-entry route. Requests use typed finite bounded coordinates or known place IDs. Providers use fixed source endpoints and allowed hosts where implemented.

Caddy exposes one origin with CSP, `nosniff`, frame denial, a referrer policy and camera/microphone restrictions. API/database ports remain private in production Compose. Forwarded client identity is trusted only from the configured Caddy address and loopback.

The current client limiter is in-memory and assumes one API process. Exploration capacity/deduplication are enforced through PostgreSQL transactions/indexes. Replicas require shared rate limiting; arbitrary external headers must not become trusted merely because a reverse proxy is added.

Raw source files, backend environment and pinned release `inputs/` have no public file route. Prepared manifests include public source/review metadata; `/media` serves owned derivatives. Global completion manifests/hashes and committed state prevent partial files being treated as finished results.

## Secrets

Database, Earthdata and optional storage credentials belong to backend environment/private `.env`. Compose passes database components rather than interpolating passwords into a URI. Never dump the complete settings/environment, place secrets in `VITE_*` variables, include `.env` in bootstrap artifacts, or put temporary signed Landsat URLs in public source metadata.

Scientific source/review manifests should remain public and reproducible; credentials are unrelated to student access. Earthdata is needed only for operator IMERG measurements. The currently accepted delivery has no configured Earthdata acquisition and no remote S3 publication.

## Retention and deletion

Students can remove packs on Saved or clear browser data. Progress is not uploaded; changing devices/origins does not carry it over. A temporary tunnel's new hostname has a fresh storage context.

There is no public API to delete a global job/result. Operators should define an appropriate retention policy for exact request coordinates and operational jobs before a larger pilot. Back up/delete database rows and matching result directories deliberately; do not remove the only active approved release or shared assets without reference checks.

Raw scientific provenance and approved curated releases are retained to reproduce the numbers/images. Ordinary job cleanup and scientific-release retention serve different purposes. Backups may contain global request coordinates; restrict access accordingly and use the organization's chosen off-machine encrypted backup system.

## Verification and further scope

Reserved-character database connection tests, trusted/untrusted forwarded client tests, request validation, queue capacity/rollback, stale generation, partial publication, source integrity and offline pack integrity are covered by the implementation suite. This is not a penetration-test report. Accounts, private classrooms, uploads and private user-owned results require separate authentication/authorization/storage designs.

See [architecture](architecture.md), [backend](backend.md), [deployment](deployment.md), [operations](operations.md), [offline](offline.md) and [sources/licenses](sources-and-licenses.md).
