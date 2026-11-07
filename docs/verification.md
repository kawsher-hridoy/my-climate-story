# Execution verification

Updated on 2026-11-08 against the local production application at http://localhost:8088, release `mcs-cbe101aec7584839`, format 2, database migration `002`. See [review fixes](review-fixes.md) for all 11 resolutions and detailed evidence.

| Check | Result |
|---|---|
| Python scientific/pipeline/API/recovery suite | 62 passed; 5 PostgreSQL tests skipped by default |
| Disposable PostgreSQL/PostGIS suite | All 5 passed; combined total 67 Python tests |
| Frontend interaction/offline suite | 17 passed |
| TypeScript build | Passed |
| Vite production/PWA build | Passed; 42 precached app entries |
| Dependency audit | No reported npm vulnerabilities |
| Actual release validation | 12 places, 35,100 POWER values, 24 reviewed images, 12 descriptive comparisons |
| Production API consistency | All 12 stories match all 24 standalone series; Barishal/Bhola provenance is distinct and correct |
| Docker deployment | Both image builds passed; all services running; trusted proxy/network addresses verified |
| Migration | Fresh/existing test databases and production upgrade passed |
| Accessibility sample | Initial 2026-11-07 check: no axe violations on English home and Dhaka story under WCAG A/AA tags |
| Mobile layout | Updated Bangla Barishal and Dhaka stories have no horizontal overflow at 360 px; home/teacher/source checks were performed on 2026-11-07 |
| Saved-pack integrity | WebP checksums verified; explicit WebP MIME mapping added for slim containers |
| Offline navigation | First Saved SPA navigation after disconnecting and release-pinned story navigation both succeed |
| Persistent saved media | Legacy Dhaka migrated; new Barishal saved; both reopen offline with both images after browse-cache deletion and HTTP-cache clearing |
| Offline language/quiz | Bangla stories, six chapters, two charts and quiz feedback work offline |
| Global backend job | New Paris point retrieved 45 annual POWER observations with verified atomic artifacts, provisional status and `no-store` story response |
| Database restoration | Custom-format backup restored into a separate test database; 291,026 place rows verified |
| Documentation | 35 Markdown documents including the complete handbook, architecture flows, source-to-feature map, field dictionary, generated per-location/SQL references and developer/privacy guides; 178 relative links passed validation |

Browser screenshots and review contact sheets are in `output/playwright/` and `output/imagery-review/`. Source and release evidence is in `data/manifests/` and the reviewed content files.

The Docker bridge in this environment could not reach npm reliably. The Linux frontend build uses host networking; its runtime remains on the Compose network. The lockfile was repaired with a clean Node 24 environment to include platform-specific optional packages.

Accepted limitation: IMERG measurements remain pending. The importer is implemented and tested with controlled HDF5 data, but authenticated measurement acquisition/parity is not claimed. The app is deployed locally; a public domain/server was not supplied.
