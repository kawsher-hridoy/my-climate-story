# Security policy

## Reporting a vulnerability

Do not disclose credentials, personal exploration coordinates, database dumps, or exploitable deployment details in a public issue.

Use [GitHub private vulnerability reporting](https://github.com/kawsher-hridoy/my-climate-story/security/advisories/new) if it is enabled. Otherwise, contact the maintainer privately through the contact channels on [their profile](https://github.com/kawsher-hridoy). Include the affected revision, a minimal reproduction, impact, and any relevant redacted evidence.

Security fixes are prepared against `main`. This project does not promise a formal response SLA or security certification.

## Sensitive information

- Database, Earthdata, and optional object-storage credentials belong in a private backend `.env` or secret store, never frontend variables or public manifests.
- Student quiz/action progress and saved packs remain device-local.
- Global exploration coordinates are sent to the backend and NASA POWER and retained as operational provenance. Public result URLs are not private per-user storage.
- Database backups can contain coordinates and job data; restrict access and use encrypted off-instance storage.
- Production API/database ports must remain private; only the narrowly configured Caddy proxy is trusted for forwarded client identity.

Do not test destructive database cleanup, workload exhaustion, or release mutation against the live application. Use isolated fixtures and the dedicated disposable integration database.

See [security and privacy](docs/security-and-privacy.md), [deployment](docs/deployment.md), and [testing](docs/testing.md) for implemented controls and their limits.
