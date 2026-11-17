# Product scope and requirements

My Climate Story is a place-based climate-learning application for students in grades 6–10 and their teachers. It was developed for the [2026 NASA International Space Apps Challenge](https://www.spaceappschallenge.org/2026/).

The retained [project brief](../My_Climate_Story_NASA_Space_Apps.pdf), *My Climate Story — Learning Climate Change Through Your Own Backyard*, frames the problem: climate teaching can feel distant, English-heavy, and difficult to connect with everyday life in Bangladesh.

## Feature mapping

| Brief area | Implemented scope |
|---|---|
| Choose your place | Curated locations, gazetteer name/alias search, map selection, coordinates, and opt-in geolocation |
| See the change | Twelve aligned real Landsat pairs, exact acquisition dates, keyboard slider, and side-by-side view |
| Understand the records | Regional temperature history, reviewed descriptive decade averages, source/quality explanations, and explicit rainfall availability |
| Learn by playing | Five-question activities from 30 bilingual reusable questions plus twelve source-backed image questions |
| Take action | Relevant student/family/school action cards with device-local choices |
| NASA sources | POWER, Landsat, GIBS, and GISTEMP; IMERG acquisition tooling |
| Bangla first | Complete Bangla/English interface, stories, quiz options/rationales, actions, and guides |
| Low connectivity | Prepared data, owned imagery, and saved packs containing both languages |
| Storytelling | A six-chapter journey around a familiar place rather than a raw statistical dashboard |
| Teachers | Printable stories, worksheet, and a classroom activity without account management |
| Global exploration | Worldwide named points/coordinates with explicit provisional-data and review limits |

## Current scientific scope

- **Temperature:** complete 1981–2025 POWER records, with an older-record caveat and a default 2001–2025 chart view. Annual means use calendar-day weighting.
- **Comparisons:** scoped descriptive arithmetic for complete 2001–2010 and 2016–2025 windows. No statistical significance, forecasts, or causal attribution is inferred.
- **Rainfall:** the IMERG importer, schema, educational explanation, and pending state are implemented. Verified IMERG measurements are not included; POWER rainfall does not replace them.
- **Imagery:** reviewed Landsat pairs are historical/recent observations, not evidence of a single cause. Historical dates are in 1990, except Rangpur in 1995; recent dates are in 2025.
- **Global context:** GISTEMP anomalies remain separate from local absolute temperatures and retain the 1951–1980 baseline.
- **Location precision:** selected coordinates identify a place for regional gridded estimates, not an independent thermometer at that exact point.

## Acceptance criteria

Each curated place must open in both languages, display a currently approved image pair, expose correct temperature and source details, explain rainfall availability, provide five questions and relevant actions, save successfully, and reopen offline.

Global requests must remain provisional unless separately reviewed. Publication requires source agreement, complete verified artifacts, and committed job completion. Saved packs retain their release and local progress; changing hostname or device does not migrate browser storage automatically.

The [test guide](testing.md), [methodology](scientific-methodology.md), and [architecture decisions](decisions/001-core-architecture.md) define the engineering and review requirements.

## Outside the current scope

Student/teacher accounts, managed classes, community uploads, projections, daily extreme indices, sea-level analysis, messaging, additional languages, and automatic global imagery/comparison approval require separate designs and evidence.
