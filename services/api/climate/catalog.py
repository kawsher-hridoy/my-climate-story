import unicodedata

from sqlalchemy import delete, select

from .db import (
    ImageryRecord,
    ObservationRecord,
    PlaceAliasRecord,
    PlaceRecord,
    ReleaseRecord,
    ReviewRecord,
    SeriesRecord,
    Session,
    SourceRequestRecord,
)
from .files import active_release, digest, read_json
from .schemas import Place


def normalize_name(name: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", name).casefold().split())


def catalog_place(session, place: Place) -> None:
    row = session.get(PlaceRecord, place.id)
    if row is None:
        row = PlaceRecord(id=place.id)
        session.add(row)
    row.name = place.name.en
    row.name_bn = place.name.bn
    row.latitude = place.coordinates.latitude
    row.longitude = place.coordinates.longitude
    row.country = place.country
    row.division = place.division
    row.feature_type = place.feature_type
    row.featured = int(place.featured)
    row.payload = place.model_dump(mode="json")
    session.flush()
    session.execute(delete(PlaceAliasRecord).where(PlaceAliasRecord.place_id == place.id))
    aliases = {normalize_name(x): x for x in [place.name.en, place.name.bn, *place.aliases] if x}
    session.add_all(PlaceAliasRecord(place_id=place.id, normalized=k, name=v) for k, v in aliases.items())


def seed_release() -> dict:
    release_id, folder = active_release()
    manifest = read_json(folder / "release.json")
    with Session.begin() as session:
        record = session.get(ReleaseRecord, release_id)
        if record is None:
            session.add(ReleaseRecord(id=release_id, manifest=manifest))
        else:
            record.manifest = manifest
        for request in manifest["source_requests"]:
            session.merge(
                SourceRequestRecord(
                    id=request["id"],
                    dataset=request["dataset"],
                    release_id=release_id,
                    checksum=request["sha256"],
                    metadata_json=request,
                )
            )
        for raw_place in read_json(folder / "places.json"):
            place = Place.model_validate(raw_place)
            catalog_place(session, place)
            story = read_json(folder / "stories" / f"{place.id}.json")
            for component in [story["temperature"], story["rainfall"]]:
                series_id = component["series_id"]
                if not series_id:
                    continue
                record = SeriesRecord(
                    id=series_id,
                    dataset=component["source"]["id"],
                    unit=component["source"]["unit"],
                    content_hash=digest(component["monthly"]),
                    publication_state=component["publication_state"],
                    payload=component,
                )
                session.merge(record)
                session.flush()
                if (
                    session.scalar(
                        select(ObservationRecord.id).where(ObservationRecord.series_id == series_id).limit(1)
                    )
                    is None
                ):
                    for item in component["annual"]:
                        session.add(
                            ObservationRecord(
                                series_id=series_id,
                                period=str(item["year"]),
                                resolution="annual",
                                value=item["value"],
                            )
                        )
                    for item in component["monthly"]:
                        session.add(
                            ObservationRecord(
                                series_id=series_id,
                                period=item["date"],
                                resolution="monthly",
                                value=item["value"],
                            )
                        )
                comparison = component.get("comparison")
                if comparison:
                    session.merge(
                        ReviewRecord(
                            id=comparison["review_id"],
                            subject=series_id,
                            reviewer="Recorded dataset review",
                            status=comparison["publication_state"],
                            evidence=comparison,
                        )
                    )
            imagery = story["imagery"]
            session.merge(
                ImageryRecord(
                    id=f"{release_id}-{place.id}",
                    place_id=place.id,
                    status=imagery["status"],
                    payload=imagery,
                )
            )
    return {"release_id": release_id, "places": 12}
