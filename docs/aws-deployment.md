# Host the backend on AWS EC2

This is the deployment procedure for the current app. The repository provides the Compose configuration; no AWS resources were created during documentation/configuration work.

One Ubuntu EC2 instance runs Caddy, FastAPI, the Procrastinate worker and PostgreSQL/PostGIS. Image/source/release files live on its EBS-backed disk. This supports the current continuous worker and shared filesystem without converting them into request-limited functions.

The existing Caddy image also serves the React frontend, so this setup can host the complete website. The optional Vercel integration is explained separately below.

## Costs and instance size

For an initial pilot, use an **x86 Ubuntu 24.04 LTS instance with 2 vCPU and 4 GB RAM**, such as `t3.medium`, and about **40–50 GB gp3 EBS storage**. The x86 path matches the tested Docker/dependency setup. A 1 GB micro instance is not the recommended capacity for concurrent API, worker, database and image/dependency builds.

This is not permanently free. EC2 compute, EBS, public IPv4 and any additional services can incur charges according to your account, region and eligibility. AWS currently advertises a new-customer Free plan with up to $200 in credits over at most six months; it ends when the period/credits run out. Older accounts have different eligibility. Check the account's plan and cost estimate before launching.

For this first setup, PostgreSQL runs in Docker on the EC2 instance. Separate RDS, load balancer, NAT gateway and S3 services are not required. Backups remain necessary; managed services can be introduced later.

## 1. Launch the instance

In the AWS console:

1. Open **EC2 → Launch instance** in your chosen region. Singapore is a reasonable regional choice for a Bangladesh pilot; compare available pricing/capacity.
2. Name it `my-climate-story`, select **Ubuntu Server 24.04 LTS, x86_64**, and choose the recommended size or a measured equivalent.
3. Create/select an SSH key pair and save the `.pem` file privately.
4. Use a public subnet with internet access and a public IP. Allocate an Elastic IP if you need a stable address across stop/start; include public-IP charges in the estimate.
5. Configure EBS storage. The host project data and named Docker volumes must remain on persistent disk.
6. Configure the security group below, then launch.

| Inbound port | Source | Purpose |
|---|---|---|
| TCP 22 | Your current public IP `/32` | SSH administration |
| TCP 80 | `0.0.0.0/0` | Caddy redirect and ACME HTTPS validation |
| TCP 443 | `0.0.0.0/0` | Public HTTPS API/media/site |
| UDP 443, optional | `0.0.0.0/0` | HTTP/3 |

Allow ordinary outbound HTTPS/DNS/provider access for package/image downloads, NASA requests and certificates. Database 5432 and API 8000 have no public Compose port and should have no public security-group rule. Add IPv6 rules only if the deployment uses IPv6.

## 2. Connect with SSH

On your computer, replacing the filename and address:

```bash
chmod 400 my-climate-story.pem
ssh -i my-climate-story.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

All remaining server commands run on the EC2 host. They do not deploy or expose your development computer.

## 3. Install Docker and Git

Use Docker's official Ubuntu repository:

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

```bash
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
```

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker compose version
```

The following examples use `sudo docker`; changing membership in the Docker group is not required. Clone as the `ubuntu` user so the shared data directory has the expected owner. The tested image uses UID 1000; a standard Ubuntu EC2 login account normally has this UID. Check `id -u` and directory ownership if data writes fail.

## 4. Clone and configure the app

```bash
git clone https://github.com/kawsher-hridoy/my-climate-story.git
cd my-climate-story
cp .env.example .env
chmod 600 .env
nano .env
```

Set at least:

```dotenv
POSTGRES_USER=climate
POSTGRES_DB=climate
POSTGRES_PASSWORD=REPLACE_WITH_A_LONG_UNIQUE_PASSWORD
SITE_ADDRESS=api.your-domain.com
APP_CONTACT_URL=https://your-frontend-domain/en/about
```

Use a newly generated password; keep it in this local file. Leave `DATABASE_URL` blank for the component-based connection setup. Compose sets database host `db`, port 5432 and `APP_ENV=production`. Keep the backend Earthdata fields empty while rainfall remains pending. S3 credentials are optional and can remain blank.

Point an **A record** for `api.your-domain.com` to the instance's public/Elastic IP. Confirm DNS resolves before requesting certificates. Using DNS-only routing during the first HTTPS setup avoids adding another reverse-proxy layer before Caddy is verified.

`SITE_ADDRESS` is a hostname, without `https://`. Caddy obtains/renews its certificate when the hostname and public TCP 80/443 routing are correct. If you are hosting the whole app here, use its main hostname instead and set the contact URL accordingly.

## 5. Start the Docker stack

```bash
sudo docker compose -f infra/compose.yml -f infra/compose.aws.yml up -d --build --wait
```

The AWS override adds public 80/443 bindings to Caddy. The original localhost:8088 binding remains usable on the server. API and database stay internal; the worker shares the same `data` directory.

Startup automatically preserves/restores prepared data, applies migration `002`, initializes Procrastinate, seeds the active release, validates the scientific data, and imports the gazetteer if absent. The worker starts after API readiness. There is no need to configure Earthdata or perform another Landsat acquisition for the shipped reviewed snapshot.

The first build can take several minutes. Inspect progress/errors with:

```bash
sudo docker compose -f infra/compose.yml -f infra/compose.aws.yml ps
sudo docker compose -f infra/compose.yml -f infra/compose.aws.yml logs --tail=60 api worker web
```

## 6. Verify the backend

```bash
curl -f https://api.your-domain.com/api/v1/health/ready
curl -f https://api.your-domain.com/api/v1/stories/dhaka
```

Readiness should report `ready` and the deployed release. Open a returned `/media/imagery/...webp` URL and verify image delivery. Then test a curated story, a new exploration job, offline saving and Bangla/English on the deployed HTTPS origin.

The native FastAPI `/docs` route is not exposed by the current Caddy routing. Use the committed [OpenAPI](openapi.json) and [API reference](api.md), or access the internal API deliberately for administration.

## 7. Optional Vercel frontend routing

The current frontend uses relative `/api/v1/...` requests and `/media/...` assets. A Vercel deployment therefore needs routing for both prefixes to this HTTPS AWS hostname. At repository root, an example `vercel.json` is:

```json
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "apps/web/dist",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.your-domain.com/api/:path*"
    },
    {
      "source": "/media/:path*",
      "destination": "https://api.your-domain.com/media/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

Replace the example backend hostname with the actual verified AWS hostname. Select Vite and the repository root in Vercel; use Node 24, `npm ci`, the build command and output directory above. The API/media rules must precede SPA fallback. This keeps browser requests on one origin, including service-worker saved-media routing.

This rewrite example establishes basic routing; production client identity needs a separate proxy check. The existing trusted Caddy → API configuration handles clients connecting directly to Caddy. If Vercel proxies a request, Caddy sees that additional proxy peer; blindly trusting arbitrary incoming forwarded headers is not appropriate. Configure a verified trusted/signed proxy path or a suitable shared limiter before using that path for a classroom-scale exploration service. Validate that separate visitors do not share one exploration bucket.

The complete app can already run directly on the AWS Caddy hostname. A live Vercel/AWS integration was not deployed or verified during the configuration work.

## 8. Persistence, updates and backups

Named volumes retain PostgreSQL and Caddy certificates; host `data/` retains reviewed releases/images and completed global results. Container replacement preserves these. Instance termination may delete EBS according to its settings; a container volume is not an off-instance backup.

Before updates, back up PostgreSQL and the matching data artifacts, and record image/release versions. The repository [backup script](../scripts/backup.sh) is run from the project root with access to Docker; the existing local-production Compose service names are the same.

Update commands:

```bash
git pull --ff-only
sudo docker compose -f infra/compose.yml -f infra/compose.aws.yml up -d --build --wait
```

Do not run `down -v` during a normal update. Maintain an access-controlled off-instance backup/snapshot and an appropriate retention policy. EBS snapshots, public IPs and storage can still have costs when compute is stopped; account resource cleanup and retention need deliberate choices.

## Troubleshooting

| Symptom | Check |
|---|---|
| Public connection fails | Public subnet/IP, security group TCP 80/443, DNS and Caddy published ports |
| TLS certificate fails | Correct `SITE_ADDRESS`, DNS A record, incoming 80/443, outbound certificate access and Caddy logs |
| API fails readiness | Database health, migrations/seed/validation errors, data ownership and available disk |
| Global job remains pending | Worker logs/status and queue recovery; both API/worker need the same DB and shared data |
| Images fail on Vercel | `/media` rewrite reaches the AWS image route; it must not return SPA HTML |
| Build gets killed | Host memory/disk and instance capacity; avoid assuming a micro instance fits the complete stack |
| Separate visitors share exploration limit | Additional reverse-proxy client identity/trust path |

## Sources and verification

- [AWS EC2 security groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html)
- [AWS Free Tier plans and credits](https://aws.amazon.com/free/)
- [Docker Engine installation on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Vercel Vite/SPA deployment](https://vercel.com/docs/frameworks/frontend/vite)

The merged Compose configuration is checked for public Caddy ports, private API/database ports and unchanged shared-data wiring. This verifies the repository configuration; it does not claim an AWS instance, certificate or public integration has been deployed. See [deployment](deployment.md), [operations](operations.md), [backend](backend.md) and [architecture](architecture.md).
