# Content and localization

Student-facing content is deterministic and reviewed. There is no runtime language-model dependency or generated scientific narrative.

## Files

- `content/places.json`: curated names/aliases, coordinates, tags and bilingual introductions.
- `content/question-bank.json`: 30 reusable questions with category, both language versions, options, answer index, rationale and source.
- `content/actions.json`: student/family/school cards, relevance tags and citations.
- `content/imagery-candidates.json`: real source scene groups.
- Review JSON: source/image hashes, reviewer, dates and scoped evidence.
- `apps/web/src/lib/i18n.ts`: interface strings in Bangla and English.

The builder converts compact authored question text into the public typed schema. It chooses category-balanced activities with stable seeded option ordering, then adds a source-backed image question when imagery is approved. Correct answer indices are remapped after shuffling.

## Language policy

Bangla is the default. English is complete. Language switching preserves the selected place and route. Both versions are included in saved packs so a network connection is unnecessary to switch languages.

Curated place names are reviewed, including ঢাকা, চট্টগ্রাম, খুলনা, রাজশাহী, সিলেট, বরিশাল, রংপুর, ময়মনসিংহ, কক্সবাজার, সাতক্ষীরা, ভোলা and সুনামগঞ্জ. Gazetteer aliases are not guaranteed complete translations; preserve source names when a reviewed alias is absent.

## Writing rules

Use short sentences and familiar observations. Say “around this place” for regional estimates. Distinguish observation from explanation, anomaly from absolute temperature, missing from zero, and an annual total from a rate.

Numerical change copy must be supplied by the publication-policy-approved calculation, not a hardcoded warming assumption. Similar rounded decade means do not imply no climate change. Monthly data does not support hot-day counts.

Image captions mention sensor, season, haze and masked pixels where relevant. Do not interpret green colors as verified vegetation change or claim climate causation. Outdoor actions direct students toward safe adult-supervised activities.

## Review and checks

Verify both versions, source URLs, answer indices, labels and readable Bengali rendering. Test key parity for interface dictionaries and valid answer ranges. Data/content revisions create a new release; question progress is keyed by content version so a changed activity is not confused with an old answer set.
