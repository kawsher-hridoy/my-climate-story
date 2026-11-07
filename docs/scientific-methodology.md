# Scientific methodology

The application teaches reading evidence. It does not estimate a causal local climate attribution or create forecasts from these observations.

## Temperature aggregation

POWER monthly `T2M` values are mean temperatures. Annual mean temperature is:

```text
sum(monthly_mean × days_in_month) / days_in_year
```

Use the Gregorian calendar including leap years. All 12 valid months are required. Month 13 is an official annual summary and never enters the monthly series. Independently derived means are compared against NASA's annual values within the precision allowed by rounded monthly inputs.

The supplied older analysis used equal month weights. Its values differed by up to approximately 0.0425°C. Corrected calculations keep precision until display.

## Descriptive decade comparisons

Initial temperature windows: 2001–2010 and 2016–2025. Each decade mean is the arithmetic mean of ten complete annual means. Display temperatures and differences to 0.1°C.

Copy states that the difference occurs **in this dataset**. If the displayed difference rounds to zero, explain that the means are similar at shown precision. This does not imply identical days, absence of climate change, or a statistical significance result.

Comparison approval is scoped to source hashes, variable and windows. Current review records approve descriptive arithmetic only. They are not formal homogeneity tests or climate-attribution findings. The older suspected discontinuity is excluded from default comparisons and remains visible in the full-history caveat.

Release validation recomputes monthly/annual temperature and comparison metrics from pinned source files and verifies the published arrays, windows and review identities. GISTEMP values are checked against its original annual source fields. Output checksums are an additional integrity check, not a substitute for comparing scientific values. Identical observations may share a content hash, while place-specific components have distinct IDs so coordinates and review provenance cannot overwrite another place.

## Precipitation

IMERG native monthly mean precipitation is mm/hr:

```text
monthly_mm = rate_mm_hr × 24 × calendar_days
annual_mm = sum(12 complete monthly_mm)
```

POWER precipitation uses mm/day, not monthly accumulated millimeters. Its documented discontinuity prevents public change narratives. Never splice it into IMERG. Missing data means unknown, not no rainfall.

IMERG extraction is pending for this delivery. The future initial descriptive windows are 2001–2010 and 2015–2024 if the inspected 2024 complete-year cutoff remains valid. Future releases must discover the actual cutoff and receive a new review.

## Satellite interpretation

Compare actual same-area, similar-season scenes. Mask invalid/cloud/shadow/saturated pixels, retain water, align the shared 30 m grid, and apply one fixed display transform.

Visible differences can reflect human activity, vegetation season, sensor response, atmospheric haze, tides, water levels or sediment. The captions explicitly mention these limitations. No quantitative vegetation/coastline-change metric or climate cause is inferred from the two RGB images.

## Global context

GISTEMP anomalies describe global land–ocean temperature differences from the 1951–1980 mean. They are displayed separately from local absolute °C values. Partial-year input is excluded from annual comparisons.

## Unsupported claims

Monthly inputs cannot establish hot-day/heatwave counts, wet-day frequency, dry spells or monsoon onset. Those require daily data, defined thresholds, completeness checks and additional validation. Their absence must not be filled with invented explanations.
