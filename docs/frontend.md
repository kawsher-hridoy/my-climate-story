# Frontend

The web application uses React 19, TypeScript, Vite, React Router, TanStack Query, i18next, Leaflet, Chart.js, Dexie and Workbox. Exact dependency versions are in `package-lock.json`. The production build uses Node 24; local development supports Node 22.12+.

## Routes and components

| Route below `/bn` or `/en` | Behavior |
|---|---|
| `/` | Illustrated introduction, project coverage and featured stories |
| `/explore` | Gazetteer search, map/coordinate selection and queued global retrieval |
| `/story/:placeId` | Six chapters: images, temperature, rainfall, global context, quiz, actions |
| `/explore/point?id=…` | Provisional story for a selected non-curated point |
| `/saved` | Local pack listing, opening, updating and deletion |
| `/learn` | Weather/climate/data vocabulary |
| `/teachers` | Lesson and printable worksheet |
| `/sources` | Dataset explanations, scope and attribution |
| `/about` | Project purpose and local-storage/privacy explanation |

`App` provides the shared layout and language routes. `Story` uses an `offlineFirst` query with an immediate matching-pack read when disconnected and fallback after request failure. Saved-list local reads use `always`. ImageComparison, ClimateChart and Quiz own their interaction state. SourceDetails exposes citation, units, coverage and represented area.

## Design

The cream/green paper palette and original vector landscape establish a friendly editorial layout. Real satellite imagery appears only after approval. Homepage thumbnails are navigation previews; the scientific comparison displays the original processed square without that thumbnail crop/filter.

CSS tokens, responsive grids, clear chapter numbers and self-hosted fonts support low-end devices. Bangla uses Noto Sans Bengali; English uses DM Sans. Controls have visible focus, sufficient target sizes and a reduced-motion alternative.

## State and data

TanStack Query caches prepared API requests. Locale comes from the route and is saved locally. Both language versions remain in story manifests. IndexedDB stores complete packs and progress; Cache Storage holds verified owned image responses. No quiz score is submitted to the backend.

Map and chart modules are deferred. Charts also expose real-value tables and downloadable CSV. A pending rainfall chapter contains no chart values. Provisional global data never receives an automatic approved comparison.

## Accessibility

Use semantic headings, labeled forms, native radio/checkbox/range controls, screen-reader chart descriptions and table equivalents. The image slider has a side-by-side alternative. Every scientific image carries alternative text and source/date metadata.

Check both languages at 360 px and at enlarged text sizes. Test keyboard slider movement, menu access, radio selection and focus visibility. Browser accessibility reports and screenshots belong under `output/playwright/`.

## Editing

UI strings are in `src/lib/i18n.ts`. Educational text lives in `content/`. Generate `src/lib/api.generated.ts` from OpenAPI instead of maintaining an independent wire schema. Validate with typechecking, Vitest, a production build, and actual browser checks.
