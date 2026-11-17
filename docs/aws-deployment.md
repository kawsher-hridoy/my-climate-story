# AWS EC2 deployment

The complete application is hosted at **https://climate-story.hridoy.xyz**: Caddy serves the React frontend and proxies the FastAPI API and owned imagery; PostgreSQL/PostGIS and the Procrastinate worker run on the same EC2 instance. The architecture does not require a separate frontend hosting service.

This guide is for commands run **on the EC2 host**, not on a developer's computer. Local Compose shutdown must not stop or modify the public deployment.

## Host and network

Use Ubuntu x86_64, Docker Engine, Docker Compose, Git, and persistent EBS storage. Follow [Docker's Ubuntu installation guide](https://docs.docker.com/engine/install/ubuntu/) and enable Docker at boot.

The current 2 GB `t3.small` deployment is a pilot with 30 GB root storage and 2 GB swap. It uses an operator-managed small-instance overlay. This is not evidence of sustained classroom capacity; allow more memory/disk headroom and measure real usage before scaling.

| Inbound port | Source | Purpose |
|---|---|---|
| TCP 22 | Administrator's current IP only | SSH |
| TCP 80 | Public | Caddy redirect and certificate validation |
| TCP 443 | Public | HTTPS |
| UDP 443, optional | Public | HTTP/3 |

API 8000 and PostgreSQL 5432 stay private. Permit required outbound HTTPS/DNS access. Verify the domain's A record against the instance's current address; do not assume an auto-assigned public IP survives stop/start. An Elastic IP can provide a stable address, with applicable AWS charges.

## Configure the application

Clone the repository as the deployment user, then work from its root:

```bash
git clone https://github.com/kawsher-hridoy/my-climate-story.git
cd my-climate-story
cp -n .env.example .env
chmod 600 .env
```

Set a unique database password and the deployed hostname in the private `.env`. For this site's configuration:

```dotenv
SITE_ADDRESS=climate-story.hridoy.xyz
APP_CONTACT_URL=https://climate-story.hridoy.xyz/en/about
POSTGRES_PASSWORD=REPLACE_WITH_A_LONG_UNIQUE_PASSWORD
```

Forks should use their own hostname and contact URL. Leave `DATABASE_URL` blank for component-based database connections. Earthdata and S3 fields can remain empty; neither is required for the supplied reviewed snapshot.

Always pass `--env-file .env`: the environment file is at the repository root, while Compose files are under `infra/`. Omitting it can leave Caddy HTTP-only and use default database credentials.

**Existing database:** changing `POSTGRES_PASSWORD` in a container environment does not change the stored PostgreSQL role password. Align existing credentials deliberately before recreating API/worker services. Do not delete the database volume to fix a password mismatch.

## Compose overlays

The base `infra/compose.yml` supplies all four services. `infra/compose.aws.yml` adds public Caddy 80/443 bindings. The existing 2 GB pilot also uses an operator-created `infra/compose.small.yml`, which is private host configuration rather than a repository file.

Before using a 2 GB host, verify that overlay and swap are present. Its pilot limits are API 1024 MiB, worker 256 MiB, database 256 MiB, and gateway 64 MiB; PostgreSQL uses 64 MB shared buffers, 4 MB work memory, and 30 maximum connections. These leave limited operating-system headroom and are not a load-test guarantee.

The helper below includes the host's overlay when present, without creating or replacing it:

```bash
compose() {
  if [ -f infra/compose.small.yml ]; then
    sudo docker compose --env-file .env \
      -f infra/compose.yml -f infra/compose.aws.yml \
      -f infra/compose.small.yml "$@"
  else
    sudo docker compose --env-file .env \
      -f infra/compose.yml -f infra/compose.aws.yml "$@"
  fi
}
```

Use it from the repository root. Build images sequentially on small hosts:

```bash
compose build api
compose build web
compose up -d --no-build --wait
compose ps
```

Startup preserves/restores prepared data, migrates the database, initializes the queue, seeds the active release, validates data, and imports the gazetteer if needed. The worker starts after API readiness. Containers run detached with `restart: unless-stopped`; SSH logout does not stop them.

## Verify HTTPS and application behavior

```bash
curl -f https://climate-story.hridoy.xyz/api/v1/health/ready
compose logs --tail=60 api worker web
```

For another deployment, substitute its hostname. Check a curated story and its owned image URLs, a new provisional global job, both languages, and an online-save → offline-reopen journey on the deployed origin. Native FastAPI `/docs` is not exposed by Caddy; use the committed [OpenAPI](openapi.json) for the public contract.

If HTTP works but HTTPS fails, check DNS, security-group routing, Caddy logs, and the web container's `SITE_ADDRESS`. Inspect only the relevant non-secret setting; do not dump the environment.

## Updates, persistence, and backups

Before updates, back up PostgreSQL and matching data artifacts and record image/release versions. Keep an access-controlled off-instance backup; Docker volumes on the same EBS disk are not a disaster-recovery backup.

```bash
git pull --ff-only
compose build api
compose build web
compose up -d --no-build --wait
```

Preserve `.env`, the host's small-instance overlay, database/Caddy volumes, scientific releases, and completed-result artifacts. Older pinned stories and packs depend on their recorded releases. See [operations](operations.md) for backups and compatible rollback.

Do not run `down -v`, prune shared Docker resources, or remove releases during routine updates. EC2 compute, EBS, public IPv4, snapshots, and other configured resources can incur charges; monitor costs and retention deliberately.

See [deployment](deployment.md), [backend](backend.md), and [security and privacy](security-and-privacy.md) for configuration and operational boundaries.
