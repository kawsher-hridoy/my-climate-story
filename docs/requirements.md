# Requirements and acceptance

The source is the two-page `My_Climate_Story_NASA_Space_Apps.pdf`: **My Climate Story — Learning Climate Change Through Your Own Backyard**. It identifies English-heavy, data-heavy, distant climate teaching as a problem for students in Bangladesh and similar vulnerable communities.

## Complete requirement mapping

| PDF area | Implemented interpretation |
|---|---|
| Choose your place | Curated selection, local name/alias search, map pins, coordinates, opt-in geolocation |
| See the change | 12 aligned, real Landsat pairs with exact dates, keyboard slider and side-by-side alternative |
| Understand the trend | Temperature records, reviewed descriptive decade averages, source/quality explanations; precipitation visibly pending |
| Learn by playing | Five questions per activity; 30 bilingual reusable questions and 12 imagery questions |
| Take action | Relevant student/family/school cards and local-only choices |
| NASA sources | POWER, Landsat, GIBS and GISTEMP; IMERG acquisition tooling |
| Bangla first | Bangla/English interface, place copy, quiz options/rationales, actions and guides |
| Low connectivity | Prepared JSON and imagery; saved packs containing both languages |
| Storytelling | A chapter sequence around a named place, not a raw statistical dashboard |
| Teachers | Printable narrative and a 35-minute facilitation guide, without account management |
| Global scalability | Worldwide coordinates and gazetteer; provisional data and explicit imagery/precipitation limits |

The user selected a complete core app, Bangladesh first with global selection, a low-cost backend, a warm storybook style, deterministic narration, and imagery for all 12 places.

## Accepted amendment

During execution the user chose **“Build with rainfall marked pending for now”** because NASA Earthdata access is not configured. This changes the first delivery criterion: the importer, schema, learning explanation and pending state must work, but acquired IMERG measurements are not claimed.

## Scientific interpretation

The PDF's “exact location” means a selected coordinate, not a precise independent measurement. POWER meteorology is regional gridded data. Monthly records cannot count hot days. GIBS cannot provide 1980s MODIS images. Landsat pairs are 1990/2025 except Rangpur 1995/2025. Their visible differences do not independently establish causes.

The app shows 1981–2025 temperature history with an older-record caveat and defaults to 2001–2025. The restricted POWER rainfall series is not used for public change explanations. GISTEMP remains separate global anomaly context.

## Delivery acceptance

Each of 12 places must open in both languages, show an approved pair and correct temperature/source information, explain pending rainfall, provide five questions and relevant actions, save successfully, and reopen offline. Worldwide requests must never automatically produce approved change claims. The production Docker build, tests, source manifests and current documentation form the handoff.

Future work stays separate: student/teacher accounts, classes, community contributions, projections, daily extreme indices, coastal sea level, messaging, more languages and automatically reviewed global imagery.
