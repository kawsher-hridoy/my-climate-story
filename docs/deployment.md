# Deployment

The complete public application is hosted at https://climate-story.hridoy.xyz on one AWS EC2 instance. Follow the [EC2 guide](aws-deployment.md) for the merged server configuration and host-owned small-instance overlay. The local deployment below is separate and binds Caddy only to localhost.

## Local production build

```bash
cp -n .env.example .env
docker compose --env-file .env -f infra/compose.yml up -d --build --wait
```

Open http://localhost:8088. The default Compose ports bind only to localhost. The database is internal to the production network. Caddy serves the compiled PWA and proxies `/api` and `/media` to FastAPI.

The API startup restores/preserves prepared data, applies migrations, initializes the durable queue, seeds the catalog and indexes the downloaded gazetteer if absent. The worker starts after API readiness. Persistent volumes retain database and Caddy state; the host `data` directory retains source/releases/assets.

The Linux frontend build defaults to host networking; runtime services use isolated Compose networks. Set `BUILD_NETWORK=default` when host build networking is unavailable, such as some Docker Desktop installations.

### Database credentials and proxy identity

Compose passes `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` as separate backend settings. SQLAlchemy and libpq connection strings are constructed with their respective quoting APIs, so passwords containing `@`, `/`, spaces or other reserved characters remain intact. In native development an explicitly supplied `DATABASE_URL` takes precedence; leave it blank to use the component settings.

Pass `--env-file .env` to Compose so the project root credentials/hostname file is used even though the Compose files are under `infra/`. If a database was already initialized using a different password, changing its environment does not change the stored PostgreSQL role password; align that role deliberately before switching API/worker credentials. Preserve its data volume.

Caddy reaches the API through a dedicated proxy network. Its default address is `172.30.249.2` on `172.30.249.0/29`; the API has the distinct fixed address `172.30.249.3`. Pinning both prevents startup-order address collisions. Uvicorn trusts only Caddy's address and loopback for forwarded client identity. Other containers and external callers cannot supply trusted client headers directly. If the subnet conflicts with a local network, change `PROXY_SUBNET`, `PROXY_IP` and `PROXY_API_IP` together before deployment. API/database ports remain private.

The API image caches third-party dependencies before copying application code; source edits no longer reinstall and recursively change ownership of the whole Python environment.

## Public server adaptation

Use a Linux server with Docker and sufficient disk for source artifacts. Start around 2 vCPU/4 GB RAM/80 GB disk for a small pilot, then measure real usage.

1. Copy the project and bootstrap artifact, preserving source/review files.
2. Configure a strong database password in a private environment file.
3. Set `SITE_ADDRESS` to the real domain and the contact URL to the deployed project.
4. Change the web port mapping deliberately to public 80/443 and point DNS at the server.
5. Keep database/API ports internal, run Compose, and verify HTTPS, stories, owned images and health.
6. Run the offline browser journey on the deployed origin.

Caddy obtains TLS certificates for a configured public hostname. Security headers keep scripts/fonts local and permit only expected map image hosts. If using a separate asset origin, configure its URL, CORS and CSP allowance deliberately rather than exposing raw signed satellite URLs.

## Secrets and storage

Student access needs no Earthdata credentials. Only operator IMERG acquisition needs `EARTHDATA_USERNAME`/`EARTHDATA_PASSWORD` or token. Keep them in backend environment variables, never frontend builds or public manifests.

S3-compatible credentials are optional. `climate publish` uploads prepared public release/assets and writes the active pointer last. Local file serving remains the default; upload alone does not change frontend routing.

## Updates and rollback

Rebuild application images after code changes. Build a new validated data release after scientific/content changes. Keep the previous image tag and release ID. Roll back code by restoring its image and data by restoring the known-good active pointer, then reseed the catalog.

Never prune the only approved data release before a replacement passes validation. Back up PostgreSQL and the matching artifacts. Test restoration separately before replacing a live database.

Local shutdown and restart commands apply only to the local Compose project. Public-server operations must run on the EC2 host with its environment and overlays. Use `stop` for routine local shutdown; do not delete volumes or releases.
