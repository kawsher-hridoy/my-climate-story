import asyncio
import csv
import hashlib
import io
import logging
import mimetypes
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session as SQLSession
from starlette.middleware.gzip import GZipMiddleware

from .catalog import normalize_name
from .config import settings
from .db import ExplorationJobRecord, PlaceAliasRecord, PlaceRecord, Session, engine, get_session
from .exploration_artifacts import IncompleteExploration, verified_bundle
from .exploration_lifecycle import (
    CAPACITY,
    completed_job,
    completed_story,
    dispatch_job,
    fail_job,
    lock_capacity,
    reconcile_jobs,
    reconcile_session,
    utcnow,
)
from .files import active_release, digest, read_json
from .jobs import defer_exploration
from .schemas import (
    ApiError,
    ClimateComponent,
    ExplorationRequest,
    ExplorationResponse,
    ImageryPair,
    JobStatus,
    Localized,
    Place,
    PlaceResults,
    SourceMetadata,
    StoryManifest,
)


async def recovery_loop(stop):
    while not stop.is_set():
        try:
            await asyncio.to_thread(reconcile_jobs)
        except Exception as error:
            logging.getLogger(__name__).warning("Exploration recovery deferred (%s)", type(error).__name__)
        try:
            await asyncio.wait_for(stop.wait(), timeout=30)
        except TimeoutError:
            pass


@asynccontextmanager
async def lifespan(_):
    if settings.app_env == "test":
        yield
    else:
        stop = asyncio.Event()
        task = asyncio.create_task(recovery_loop(stop))
        try:
            yield
        finally:
            stop.set()
            await task


# Slim Python images do not always include the OS WebP MIME registry.
mimetypes.add_type("image/webp", ".webp")

app = FastAPI(
    title="My Climate Story API",
    version="0.1.0",
    lifespan=lifespan,
    description="Prepared NASA climate records, reviewed imagery, and bilingual student activities.",
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
settings.data_dir.joinpath("assets").mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.data_dir / "assets"), name="media")

traffic: dict[str, deque] = defaultdict(deque)


def throttle(request: Request, bucket="read", limit=120):
    # Ephemeral fingerprint; neither address nor selected coordinates enter ordinary logs.
    client = request.client.host if request.client else "local"
    key = hashlib.sha256(f"{datetime.now(timezone.utc).date()}:{client}:{bucket}".encode()).hexdigest()
    now = time.monotonic()
    values = traffic[key]
    while values and values[0] <= now - 60:
        values.popleft()
    if len(values) >= limit:
        raise HTTPException(
            429, "Request limit reached. Please retry in a minute.", headers={"Retry-After": "60"}
        )
    values.append(now)
    if len(traffic) > 2000:
        for old in list(traffic):
            if not traffic[old] or traffic[old][-1] < now - 60:
                del traffic[old]


@app.exception_handler(HTTPException)
async def api_exception(_, error):
    return JSONResponse(
        status_code=error.status_code,
        content={"code": f"http_{error.status_code}", "message": str(error.detail)},
        headers=error.headers,
    )


def release_folder(release: str | None = None) -> tuple[str, Path]:
    if release:
        if not release.startswith("mcs-") or any(
            x not in "abcdefghijklmnopqrstuvwxyz0123456789-" for x in release
        ):
            raise HTTPException(422, "Invalid release identifier")
        folder = settings.data_dir / "releases" / release
        if not folder.exists():
            raise HTTPException(404, "Release not found")
        return release, folder
    try:
        return active_release()
    except (FileNotFoundError, ValueError):
        raise HTTPException(
            503, "Prepared data is unavailable. Run the documented ingestion and build commands."
        ) from None


def safe_identifier(identifier):
    if len(identifier) > 120 or any(
        x not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for x in identifier
    ):
        raise HTTPException(422, "Invalid identifier")


def load_story(
    identifier: str, release: str | None = None, session: SQLSession | None = None
) -> StoryManifest:
    safe_identifier(identifier)
    release_id, folder = release_folder(release)
    path = folder / "stories" / f"{identifier}.json"
    if path.exists():
        return StoryManifest.model_validate(read_json(path))
    try:
        if session is not None:
            return completed_story(session, release_id, identifier)
        with Session() as lookup:
            return completed_story(lookup, release_id, identifier)
    except IncompleteExploration:
        raise HTTPException(404, "Completed story not found") from None


def row_place(row: PlaceRecord) -> Place:
    if row.payload:
        return Place.model_validate(row.payload)
    return Place(
        id=row.id,
        name=Localized(en=row.name, bn=row.name_bn or row.name),
        division=row.division,
        coordinates={"latitude": row.latitude, "longitude": row.longitude},
        country=row.country,
        featured=bool(row.featured),
        feature_type=row.feature_type,
        description=Localized(
            en="A gazetteer place. Regional climate availability is checked when you explore.",
            bn="গেজেটিয়ারের একটি জায়গা। অনুসন্ধানের সময় আঞ্চলিক জলবায়ুর তথ্য আছে কি না দেখা হবে।",
        ),
    )


@app.get("/api/v1/config")
def config(response: Response):
    release_id, folder = release_folder()
    manifest = read_json(folder / "release.json")
    response.headers["Cache-Control"] = "public,max-age=60"
    return {
        "release_id": release_id,
        "locales": ["bn", "en"],
        "rainfall_pending": manifest["rainfall_pending"],
        "featured_places": 12,
        "imagery_approved": manifest["approved_imagery_count"],
        "map": {
            "osm_url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            "gibs_url": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpeg",
            "gibs_max_native_zoom": 9,
            "gibs_default_date": "2025-02-08",
        },
    }


@app.get("/api/v1/places/featured", response_model=list[Place])
def featured(response: Response):
    _, folder = release_folder()
    response.headers["Cache-Control"] = "public,max-age=300"
    result = read_json(folder / "places.json")
    for place in result:
        image = read_json(folder / "stories" / f"{place['id']}.json")["imagery"]
        if image["status"] == "approved" and image.get("after"):
            place["preview_image_url"] = image["after"]["thumbnail_url"]
    return result


@app.get("/api/v1/places/search", response_model=PlaceResults)
def search(
    request: Request,
    q: str = Query(min_length=2, max_length=100),
    locale: str = Query("bn", pattern="^(bn|en)$"),
    limit: int = Query(10, ge=1, le=10),
    session: SQLSession = Depends(get_session),
):
    throttle(request)
    query = normalize_name(q)
    # Escape LIKE metacharacters: user text is a literal name, not a wildcard query.
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    ids = select(PlaceAliasRecord.place_id).where(
        PlaceAliasRecord.normalized.like(f"%{escaped}%", escape="\\")
    )
    rows = session.scalars(
        select(PlaceRecord)
        .where(PlaceRecord.id.in_(ids))
        .order_by(PlaceRecord.featured.desc(), PlaceRecord.population.desc())
        .limit(limit)
    ).all()
    return PlaceResults(
        results=[row_place(x) for x in rows],
        coverage_note=Localized(
            en="Names come from a local gazetteer; not every village has a Bangla alias. You can always select a map point.",
            bn="নাম স্থানীয় গেজেটিয়ার থেকে; সব গ্রামের বাংলা নাম নেই। মানচিত্রে বিন্দু নির্বাচন করতে পারো।",
        ),
    )


@app.get("/api/v1/places/{identifier}", response_model=Place)
def place(identifier: str, session: SQLSession = Depends(get_session)):
    safe_identifier(identifier)
    row = session.get(PlaceRecord, identifier)
    if row is None:
        raise HTTPException(404, "Place not found")
    return row_place(row)


@app.get("/api/v1/stories/{identifier}", response_model=StoryManifest)
def story(
    identifier: str,
    response: Response,
    release: str | None = None,
    locale: str = Query("bn", pattern="^(bn|en)$"),
):
    result = load_story(identifier, release)
    response.headers["ETag"] = '"' + digest(result.model_dump(mode="json")) + '"'
    response.headers["Cache-Control"] = (
        ("public,max-age=31536000,immutable" if release else "public,max-age=300")
        if result.place.featured
        else "no-store"
    )
    return result


@app.post(
    "/api/v1/explorations",
    response_model=ExplorationResponse,
    responses={429: {"model": ApiError}, 503: {"model": ApiError}},
)
def explore(
    body: ExplorationRequest, request: Request, response: Response, session: SQLSession = Depends(get_session)
):
    throttle(request, "explore", 5)
    release_id, _ = release_folder()
    place_snapshot = None
    if body.place_id:
        try:
            return ExplorationResponse(story=load_story(body.place_id, session=session))
        except HTTPException as error:
            if error.status_code != 404:
                raise
        row = session.get(PlaceRecord, body.place_id)
        if row is None:
            raise HTTPException(404, "Place not found")
        coordinates = {"latitude": row.latitude, "longitude": row.longitude}
        place_snapshot = row_place(row).model_dump(mode="json")
    else:
        coordinates = body.coordinates.model_dump()
    coordinates = {key: round(value, 4) for key, value in coordinates.items()}
    key = digest({"coordinates": coordinates, "release": release_id, "place_id": body.place_id})
    try:
        # One transaction protects reconciliation, global capacity, deduplication and enqueue.
        lock_capacity(session)
        reconcile_session(session, defer_exploration)
        job = session.scalar(
            select(ExplorationJobRecord)
            .where(
                ExplorationJobRecord.request_key == key,
                ExplorationJobRecord.status.in_(["pending", "running", "completed"]),
            )
            .order_by(ExplorationJobRecord.created_at.desc())
            .limit(1)
        )
        if job is not None and job.status == "completed":
            try:
                result = verified_bundle(job)[1]
                session.commit()
                return ExplorationResponse(story=result)
            except IncompleteExploration:
                fail_job(job, "Stored result is incomplete; a new retrieval is required.", utcnow())
                session.flush()
                job = None
        if job is None:
            count = session.scalar(
                select(func.count())
                .select_from(ExplorationJobRecord)
                .where(ExplorationJobRecord.status.in_(["pending", "running"]))
            )
            if count >= CAPACITY:
                # Commit any reconciled state even though this new request cannot fit yet.
                session.commit()
                raise HTTPException(
                    503,
                    "Data retrieval queue is full. Choose a featured story or retry later.",
                    headers={"Retry-After": "30"},
                )
            job = ExplorationJobRecord(
                id=str(uuid4()),
                request_key=key,
                release_id=release_id,
                request_payload={"coordinates": coordinates, "place": place_snapshot},
            )
            session.add(job)
            dispatch_job(session, job, defer_exploration)
        session.commit()
    except HTTPException:
        session.rollback()
        raise
    except BaseException as error:
        # Includes task cancellation: neither the app row nor queue row may commit alone.
        session.rollback()
        if not isinstance(error, Exception):
            raise
        raise HTTPException(
            503, "The data queue is unavailable. Retry later or choose a featured story."
        ) from None
    response.status_code = 202
    return ExplorationResponse(job=job_response(job))


def job_response(job):
    return JobStatus(
        id=job.id,
        status=job.status,
        story_id=job.story_id,
        story_url=f"/api/v1/stories/{job.story_id}?release={job.release_id}" if job.story_id else None,
        message=job.message,
    )


@app.get("/api/v1/jobs/{identifier}", response_model=JobStatus)
def job(identifier: str, session: SQLSession = Depends(get_session)):
    safe_identifier(identifier)
    row = session.get(ExplorationJobRecord, identifier)
    if row is None:
        raise HTTPException(404, "Job not found")
    return job_response(row)


def component(series_id: str, release: str | None = None) -> ClimateComponent:
    safe_identifier(series_id)
    release_id, folder = release_folder(release)
    path = folder / "series" / f"{series_id}.json"
    if path.exists():
        return ClimateComponent.model_validate(read_json(path))
    suffixes = ("-temperature", "-rainfall-pending")
    story_id = next((series_id[: -len(suffix)] for suffix in suffixes if series_id.endswith(suffix)), None)
    if story_id:
        with Session() as lookup:
            job = completed_job(lookup, release_id, story_id)
            if job is not None:
                try:
                    result = verified_bundle(job)[1]
                    for value in [result.temperature, result.rainfall]:
                        if value.series_id == series_id:
                            return value
                except IncompleteExploration:
                    pass
    raise HTTPException(404, "Series not found in this release")


@app.get("/api/v1/series/{identifier}", response_model=ClimateComponent)
def series(identifier: str, release: str | None = None):
    return component(identifier, release)


@app.get("/api/v1/imagery/pairs/{identifier}", response_model=ImageryPair)
def image_pair(identifier: str, release: str | None = None):
    return load_story(identifier, release).imagery


@app.get("/api/v1/sources/{identifier}", response_model=SourceMetadata)
def source(identifier: str):
    safe_identifier(identifier)
    _, folder = release_folder()
    path = folder / "sources" / f"{identifier}.json"
    if not path.exists():
        raise HTTPException(404, "Source not found")
    return read_json(path)


@app.get("/api/v1/releases/{identifier}")
def release(identifier: str):
    _, folder = release_folder(identifier)
    return read_json(folder / "release.json")


@app.get("/api/v1/exports/{identifier}.csv")
def export(identifier: str, release: str | None = None):
    data = component(identifier, release)
    if data.publication_state == "unavailable":
        raise HTTPException(404, "No measurements are available for this series")
    release_id, _ = release_folder(release)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(["period", "resolution", "value", "unit", "dataset", "release", "publication_state"])
    for item in data.annual:
        writer.writerow(
            [
                item.year,
                "annual",
                item.value if item.value is not None else "",
                data.source.unit,
                data.source.id,
                release_id,
                data.publication_state,
            ]
        )
    for item in data.monthly:
        writer.writerow(
            [
                item.date,
                "monthly",
                item.value if item.value is not None else "",
                data.source.unit,
                data.source.id,
                release_id,
                data.publication_state,
            ]
        )
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv;charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{identifier}.csv"'},
    )


@app.get("/api/v1/health/live")
def live():
    return {"status": "ok"}


@app.get("/api/v1/health/ready")
def ready():
    try:
        release_id, _ = release_folder()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready", "release_id": release_id}
    except Exception:
        raise HTTPException(503, "Prepared data or database is unavailable") from None
