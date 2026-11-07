import csv
import io

import httpx
from climate.config import settings
from climate.files import digest, write_json

from .build import places, utc_timestamp
from .providers import power_request
from .science import validate_power


def refresh_power():
    reports = []
    for place in places():
        payload = power_request(place.coordinates.latitude, place.coordinates.longitude)
        validate_power(payload)
        checksum = digest(payload)
        path = settings.raw_dir / "power-refresh" / f"{place.id}-{checksum[:16]}.json"
        write_json(path, payload)
        reports.append(
            {
                "place": place.id,
                "sha256": checksum,
                "path": str(path.relative_to(settings.raw_dir)),
                "review_required": True,
            }
        )
    # Refresh is acquisition only. It cannot silently replace the published source.
    write_json(
        settings.raw_dir / "power-refresh" / "manifest.json",
        {"retrieved_at": utc_timestamp(), "requests": reports},
    )
    return {
        "acquired": len(reports),
        "publication": "Separate validation, source selection, and review required.",
    }


def refresh_global():
    url = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"
    with httpx.Client(timeout=60) as client:
        response = client.get(url)
        response.raise_for_status()
    text = response.text
    lines = text.splitlines()
    header = next(i for i, line in enumerate(lines) if line.startswith("Year,"))
    rows = list(csv.DictReader(io.StringIO("\n".join(lines[header:]))))
    complete = [
        {"year": int(row["Year"]), "temperature_anomaly_c": float(row["J-D"])}
        for row in rows
        if row.get("J-D") not in [None, "***", ""]
    ]
    if not complete or complete[0]["year"] != 1880:
        raise ValueError("Unexpected GISTEMP series")
    checksum = digest(text)
    target = settings.raw_dir / "gistemp-refresh" / checksum[:16]
    target.mkdir(parents=True, exist_ok=True)
    (target / "source.csv").write_text(text)
    with (target / "annual.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["year", "temperature_anomaly_c"])
        writer.writeheader()
        writer.writerows(complete)
    write_json(
        target / "manifest.json",
        {
            "retrieved_at": utc_timestamp(),
            "source_url": url,
            "latest_complete_year": complete[-1]["year"],
            "review_required": True,
        },
    )
    return {
        "latest_complete_year": complete[-1]["year"],
        "publication": "New acquisition staged; existing release preserved.",
    }
