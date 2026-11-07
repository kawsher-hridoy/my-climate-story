import csv
import hashlib
import io
import zipfile

import httpx
from climate.catalog import normalize_name
from climate.config import settings
from climate.db import PlaceAliasRecord, PlaceRecord, Session
from climate.files import write_json
from sqlalchemy import delete, insert

from .build import utc_timestamp

BASE = "https://download.geonames.org/export/dump/"


def download(filename: str) -> bytes:
    path = settings.raw_dir / "gazetteer" / filename
    if not path.exists():
        with httpx.Client(timeout=120, follow_redirects=True) as client:
            response = client.get(BASE + filename)
            response.raise_for_status()
            raw = response.content
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return path.read_bytes()


def bengali(value):
    return any("\u0980" <= c <= "\u09ff" for c in value)


def import_places(include_global=True):
    administrative = {}
    for row in csv.reader(io.StringIO(download("admin1CodesASCII.txt").decode("utf-8")), delimiter="\t"):
        if len(row) >= 2:
            administrative[row[0]] = row[1]
    filenames = ["BD.zip"] + (["cities500.zip"] if include_global else [])
    records, aliases, manifests, seen = [], [], [], set()
    for filename in filenames:
        raw = download(filename)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            member = filename.removesuffix(".zip") + ".txt"
            rows = csv.reader(io.StringIO(archive.read(member).decode("utf-8")), delimiter="\t")
            count = 0
            for row in rows:
                if len(row) != 19 or not (row[6] == "P" or (row[6] == "A" and row[7].startswith("ADM"))):
                    continue
                identifier = f"geonames-{row[0]}"
                if identifier in seen:
                    continue
                seen.add(identifier)
                names = [row[1], row[2], *row[3].split(",")]
                name_bn = next((name for name in names if bengali(name)), "")
                feature = {
                    "ADM1": "division",
                    "ADM2": "district",
                    "ADM3": "subdistrict",
                    "PPLC": "capital",
                    "PPLA": "city",
                }.get(row[7], "village" if row[6] == "P" else "administrative")
                records.append(
                    {
                        "id": identifier,
                        "name": row[1],
                        "name_bn": name_bn,
                        "latitude": float(row[4]),
                        "longitude": float(row[5]),
                        "country": row[8],
                        "division": administrative.get(f"{row[8]}.{row[10]}", ""),
                        "feature_type": feature,
                        "population": int(row[14] or 0),
                        "featured": 0,
                        "payload": {},
                    }
                )
                chosen = list(dict.fromkeys([row[1], row[2], name_bn, *names[:12]]))
                normalized = {normalize_name(name): name for name in chosen if name}
                aliases.extend(
                    {"place_id": identifier, "normalized": key, "name": value}
                    for key, value in normalized.items()
                )
                count += 1
        manifests.append(
            {
                "filename": filename,
                "source_url": BASE + filename,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "imported_places": count,
            }
        )
    # Replace only GeoNames records; curated centers and reviewed aliases are preserved.
    with Session.begin() as session:
        session.execute(delete(PlaceAliasRecord).where(PlaceAliasRecord.place_id.like("geonames-%")))
        session.execute(delete(PlaceRecord).where(PlaceRecord.id.like("geonames-%")))
        for start in range(0, len(records), 5000):
            session.execute(insert(PlaceRecord), records[start : start + 5000])
        for start in range(0, len(aliases), 5000):
            session.execute(insert(PlaceAliasRecord), aliases[start : start + 5000])
    report = {
        "retrieved_at": utc_timestamp(),
        "source": "GeoNames CC BY 4.0",
        "places": len(records),
        "aliases": len(aliases),
        "files": manifests,
        "note": "Global cities500 does not contain every village; available aliases are not guaranteed translated.",
    }
    write_json(settings.raw_dir / "gazetteer" / "manifest.json", report)
    return report
