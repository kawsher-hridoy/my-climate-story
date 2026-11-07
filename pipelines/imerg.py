"""Authenticated monthly extraction. No POWER rainfall fallback."""

import hashlib
import os
from pathlib import Path

import earthaccess
import numpy as np
import xarray as xr
from climate.config import settings
from climate.files import read_json, write_json
from climate.schemas import ClimateComponent, Coordinates, Localized

from .build import imerg_source, places, utc_timestamp
from .providers import get_public_json
from .science import annual_rainfall, monthly_rain_total

COLLECTION = "C2723754851-GES_DISC"
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"


def discover() -> dict:
    entries = []
    page = 1
    while True:
        payload = get_public_json(
            CMR,
            {
                "collection_concept_id": COLLECTION,
                "page_size": 500,
                "page_num": page,
                "sort_key": "start_date",
            },
            {"cmr.earthdata.nasa.gov"},
        )
        rows = payload["feed"]["entry"]
        entries.extend(rows)
        if len(rows) < 500:
            break
        page += 1
    by_month = {}
    for row in entries:
        month = row["time_start"][:7]
        if month in by_month:
            raise ValueError(f"Duplicate IMERG granule for {month}")
        by_month[month] = row
    full_years = [
        year
        for year in sorted({int(x[:4]) for x in by_month})
        if all(f"{year}-{m:02}" in by_month for m in range(1, 13))
    ]
    result = {
        "collection": COLLECTION,
        "discovered_at": utc_timestamp(),
        "granule_count": len(entries),
        "latest_month": max(by_month) if by_month else None,
        "latest_complete_year": max(full_years) if full_years else None,
        "granules": entries,
    }
    write_json(settings.raw_dir / "imerg" / "catalog.json", result)
    return result


def extract_grid(file: Path, selected_places) -> list[dict]:
    records = []
    with xr.open_dataset(file, group="Grid", engine="h5netcdf", mask_and_scale=True) as dataset:
        variable = dataset["precipitation"]
        unit = variable.attrs.get("units", variable.attrs.get("Units", ""))
        if unit not in ["mm/hr", "mm/hour"]:
            raise ValueError(f"Unexpected IMERG precipitation units: {unit}")
        if set(variable.dims) != {"time", "lon", "lat"}:
            raise ValueError("Unexpected IMERG dimensions")
        date = np.datetime_as_string(dataset.time.values[0], unit="D")
        year, month = int(date[:4]), int(date[5:7])
        for place in selected_places:
            sample = variable.sel(
                lon=place.coordinates.longitude, lat=place.coordinates.latitude, method="nearest"
            )
            rate = float(sample.values.reshape(-1)[0])
            if not np.isfinite(rate) or rate <= -9999:
                rate = None
            total = monthly_rain_total(rate, year, month, "mm/hr")
            records.append(
                {
                    "place_id": place.id,
                    "date": f"{year}-{month:02}-01",
                    "value": total,
                    "native_rate_mm_hr": rate,
                    "cell_longitude": float(sample.lon),
                    "cell_latitude": float(sample.lat),
                }
            )
    return records


def ingest() -> dict:
    if not (settings.earthdata_token or (settings.earthdata_username and settings.earthdata_password)):
        return {
            "status": "pending",
            "message": "Configure NASA Earthdata credentials locally to acquire IMERG measurements.",
        }
    for key, value in [
        ("EARTHDATA_USERNAME", settings.earthdata_username),
        ("EARTHDATA_PASSWORD", settings.earthdata_password),
        ("EARTHDATA_TOKEN", settings.earthdata_token),
    ]:
        if value:
            os.environ[key] = value
    auth = earthaccess.login(strategy="environment", persist=False)
    if not auth.authenticated:
        raise ValueError("Earthdata authentication failed")
    catalog = discover()
    selected = places()
    results = {p.id: [] for p in selected}
    output = settings.raw_dir / "imerg" / "point-samples"
    staging = settings.staging_dir / "imerg"
    staging.mkdir(parents=True, exist_ok=True)
    if sum(x.stat().st_size for x in staging.glob("*") if x.is_file()) > 100_000_000:
        raise ValueError("IMERG staging limit exceeded; inspect and clean interrupted downloads")
    inventory = []
    for granule in catalog["granules"]:
        month = granule["time_start"][:7]
        cache = output / f"{month}.json"
        if cache.exists():
            sample = read_json(cache)
        else:
            matches = earthaccess.search_data(
                short_name="GPM_3IMERGM",
                version="07",
                temporal=(granule["time_start"], granule["time_start"]),
                count=2,
            )
            if len(matches) != 1:
                raise ValueError(f"Expected one IMERG granule for {month}")
            files = earthaccess.download(matches, local_path=str(staging), threads=1)
            if len(files) != 1:
                raise ValueError("Unexpected IMERG download count")
            path = Path(files[0])
            sample = {
                "granule_id": granule["id"],
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "records": extract_grid(path, selected),
            }
            write_json(cache, sample)
            path.unlink()
        if sample["granule_id"] != granule["id"]:
            raise ValueError("Cached IMERG sample belongs to a different granule")
        inventory.append({"month": month, "granule_id": sample["granule_id"], "sha256": sample["sha256"]})
        for record in sample["records"]:
            results[record["place_id"]].append(record)
        print(f"IMERG {month}: extracted all {len(selected)} points", flush=True)
    for place in selected:
        records = results[place.id]
        monthly = [{"date": x["date"], "value": x["value"]} for x in records]
        annual = annual_rainfall(monthly)
        source = imerg_source(catalog["discovered_at"])
        source.end = str(catalog["latest_complete_year"])
        component = ClimateComponent(
            series_id=f"imerg-{place.id}-{catalog['latest_month']}",
            publication_state="descriptive_only",
            source=source,
            annual=annual,
            monthly=monthly,
            quality_flags=["comparison_review_pending"],
            requested_coordinates=place.coordinates,
            native_cell_center=Coordinates(
                latitude=records[0]["cell_latitude"], longitude=records[0]["cell_longitude"]
            ),
            warning=Localized(
                en="Annual totals use complete years only. A descriptive comparison requires a separate review.",
                bn="বার্ষিক মোটে শুধু সম্পূর্ণ বছর ব্যবহার করা হয়। বর্ণনামূলক তুলনার জন্য আলাদা যাচাই দরকার।",
            ),
        )
        write_json(settings.data_dir / "imerg" / f"{place.id}.json", component.model_dump(mode="json"))
    write_json(
        settings.raw_dir / "imerg" / "extraction-manifest.json",
        {"source": catalog["collection"], "granules": inventory, "places": len(selected)},
    )
    return {"status": "ready", "places": len(selected), "complete_through": catalog["latest_complete_year"]}
