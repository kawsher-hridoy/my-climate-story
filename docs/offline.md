# Offline packs

The production app installs a Workbox service worker. It caches the app shell and owned media. IndexedDB stores the full saved story and local progress. Standard OSM tiles are excluded from pack downloads.

Explicitly saved images use `climate-pack-media-v1`, which has no application-driven entry or age eviction. Ordinary browsing continues to use the bounded, expiring `climate-media-v2` cache. The service-worker cache hook gives saved responses precedence after the browsing expiration check, including when the browsing response has expired or disappeared. A repair download using `cache: reload` bypasses both cache responses.

## Pack contents

Each pack contains a place ID, complete bilingual story manifest, release ID, saved date, estimated/actual size and an asset list. The manifest embeds temperature/global data, quizzes, actions and source metadata. Referenced native/thumbnail image responses are stored in Cache Storage.

The app waits for the offline shell to be ready, fetches each required owned image, verifies successful image content and SHA-256 for main images, and only then commits a complete pack record. A failed or interrupted download does not appear as a completed saved story. New unreferenced cache entries are removed after failed commits. Cache and pack-reference changes are serialized within the tab and, where supported, across tabs with Web Locks.

At startup and when saved packs are read, the app checks their expected media and migrates valid responses from the old browsing caches. It never marks a partial migration complete: missing or changed images produce an `incomplete` pack with a repair notice. Text and chart data remain readable. Repair restores that pack's pinned release, while Update explicitly fetches the latest release. Shared media is removed only after its final referring pack is deleted or updated.

## Limits and updates

- Maximum 20 packs or 100 MB of counted pack content.
- Check browser storage availability before committing.
- Display size and errors clearly.
- Updating fetches the new story/assets before replacing the old pack.
- Deletion removes unshared image responses as well as the pack record.
- The service worker may be refreshed independently of a data release; saved content remains version-pinned.

## Reading offline

Known-offline story loading checks the matching saved pack first. Otherwise it requests the selected release and falls back to a matching pack on failure. Saved-list queries use TanStack Query's `always` network mode; story queries use `offlineFirst` with retries disabled while disconnected. This lets local reads run after an online-to-offline SPA transition instead of pausing indefinitely. Language switching, charts, quizzes and actions remain available. The explorer shows a Natural Earth overview instead of an offline street map. New source requests require connectivity.

Browser storage is local and may be cleared by the user or browser. Use the saved page to verify what is on this device. There is no account synchronization or uploaded quiz history.

## Testing

Use the production build, wait for service-worker readiness, save a story, set the browser offline, navigate to Saved stories for the first time, then open its release-pinned link without reloading. Also test cold offline reload and language switching. Delete/expire the browsing cache and verify saved media still renders. Exercise partial migration, checksum mismatch, failed writes, shared-reference deletion and repair. Development Vite modules are not an offline release.
