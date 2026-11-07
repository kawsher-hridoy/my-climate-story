# Data catalog

## NASA POWER / MERRA-2

Source: [POWER monthly point API](https://power.larc.nasa.gov/api/temporal/monthly/point). Community `AG`; parameters `T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M`.

| Variable | Native unit | Meaning and handling |
|---|---|---|
| T2M | °C | Mean air temperature at 2 m; annual derivation weights months by calendar days |
| T2M_MAX | °C | Maximum field; preserve its source meaning, do not turn monthly values into hot-day counts |
| T2M_MIN | °C | Minimum field; preserve its source meaning |
| RH2M | % | Relative humidity; validate 0–100 |
| PRECTOTCORR | mm/day | Mean precipitation rate; preserved for audit, restricted for change claims |

Coverage: 12 supplied coordinates, 1981–2025. Per location: 540 month keys and 45 annual keys. Month `13` is the annual summary. Total combined numeric values: 35,100. Native spatial resolution is 0.5° latitude × 0.625° longitude; ground width varies with latitude. Returned geometry must not be assumed to be a verified grid-cell center.

All combined values match the supplied JSON. A live Dhaka 2024–2025 sample matched 130 values. Suspected older temperature discontinuities and the rainfall shift remain documented. Bhola and Barishal return identical complete source series but are separate places.

## GPM IMERG Final monthly V07B

Source: [NASA collection catalog](https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imergm-07). Short name `GPM_3IMERGM`; version `07`; concept `C2723754851-GES_DISC`; DOI `10.5067/GPM/IMERG/3B-MONTH/07`.

Inspected coverage: January 1998–September 2025, 333 consecutive granules. Complete 1998–2024 years account for 324 months. Q4 2025 was not available in the inspected catalog.

Native `Grid/precipitation` is mm/hr on a 0.1° grid with dimensions `(time, lon, lat)`. Missing marker: -9999.9 in documented source attributes. Convert hourly mean rate to accumulated monthly millimeters using calendar duration; sum complete months for annual millimeters. Never zero-fill missing periods or join POWER rainfall into this record.

**Measurement acquisition is pending.** Metadata is public, but measurements redirect to Earthdata Login. All 12 places, including Bhola, must be sampled independently when access is configured. Global precipitation includes snow as well as rain.

## GISTEMP v4

Source: [NASA GISS](https://data.giss.nasa.gov/gistemp/), global `GLB.Ts+dSST.csv`.

The prepared series has 146 annual observations, 1880–2025, and the supplied monthly derivative has 1,752 observations. Values are global land–ocean anomalies relative to 1951–1980, not local absolute temperature. Raw input contains partial 2026 data; it is not used as a complete annual observation.

## Landsat

Landsat 5 TM historical and Landsat 8 OLI recent surface-reflectance imagery, Collection 2 Level 2, 30 m optical pixels. Fourteen distinct scenes provide 12 cropped pairs. Exact IDs and date windows are in [the imagery guide](imagery.md) and `content/imagery-candidates.json`.

Each published asset has acquisition date, sensor/product ID, stable source URL, checksum, dimensions, bytes, valid-pixel fraction, cloud metadata and a visual review record.

## Maps and names

- GeoNames BD snapshot: 54,328 populated/administrative records; only 490 include Bengali-script aliases.
- The combined index contains 291,014 unique gazetteer records and 1,095,645 searchable aliases in the inspected snapshot.
- GeoNames is CC BY 4.0. Coordinates are named points, not authoritative boundary geometry.
- OSM standard tiles are viewed online with attribution and normal caching; no offline prefetch.
- Natural Earth country outlines are a public-domain offline overview.

See `data/manifests/latest.json`, raw acquisition manifests, [methodology](scientific-methodology.md), and [licenses](sources-and-licenses.md).
