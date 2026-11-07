import hashlib
from uuid import uuid4

import procrastinate
from sqlalchemy import select

from .config import settings
from .db import ExplorationJobRecord, Session
from .exploration_artifacts import publish_bundle
from .exploration_lifecycle import RUNNING_LEASE, aware, fail_job, reconcile_jobs, utcnow
from .files import read_json
from .schemas import ActionCard, ClimateComponent, Coordinates, Localized, Place, StoryManifest

app = procrastinate.App(
    connector=procrastinate.PsycopgConnector(
        conninfo=settings.queue_conninfo,
        min_size=1,
        max_size=4,
    )
)


@app.task(queue="climate", retry=False)
def explore_point(exploration_id: str, generation: int = 0):
    from pipelines.build import (
        activity,
        imerg_source,
        pending_imagery,
        power_source,
        quiz_bank,
        utc_timestamp,
    )
    from pipelines.providers import power_request
    from pipelines.science import validate_power

    token = str(uuid4())
    with Session.begin() as session:
        job = session.scalar(
            select(ExplorationJobRecord).where(ExplorationJobRecord.id == exploration_id).with_for_update()
        )
        if job is None or job.generation != generation or job.status != "pending":
            return
        job.status = "running"
        job.message = "Retrieving NASA POWER observations; precipitation remains pending."
        job.run_token = token
        job.lease_until = utcnow() + RUNNING_LEASE
        job.updated_at = utcnow()
        request, release_id = job.request_payload, job.release_id
    try:
        coordinates = request["coordinates"]
        payload = power_request(coordinates["latitude"], coordinates["longitude"])
        parsed = validate_power(payload, strict=False)
        if not any(item["value"] is not None for item in parsed["annual"]):
            raise ValueError("NASA has no usable temperature observations at this point")
        story_id = (
            "point-"
            + hashlib.sha256(
                f"{coordinates['latitude']:.4f},{coordinates['longitude']:.4f}".encode()
            ).hexdigest()[:20]
        )
        folder = settings.data_dir / "releases" / release_id
        base = StoryManifest.model_validate(read_json(folder / "stories" / "dhaka.json"))
        place = Place(
            id=story_id,
            name=Localized(en="Your selected place", bn="তোমার নির্বাচিত জায়গা"),
            division="",
            coordinates=Coordinates(**coordinates),
            featured=False,
            country="",
            feature_type="point",
            description=Localized(
                en="Explore the regional observations around this map point. Its data is provisional and has not had a local scientific review.",
                bn="মানচিত্রের এই বিন্দুর আশপাশের আঞ্চলিক তথ্য দেখো। এই তথ্য প্রাথমিক; স্থানীয় বৈজ্ঞানিক যাচাই এখনো হয়নি।",
            ),
        )
        if request.get("place"):
            requested_place = Place.model_validate(request["place"])
            place.name = requested_place.name
            place.division = requested_place.division
            place.country = requested_place.country
            place.feature_type = requested_place.feature_type
            story_id = requested_place.id
            place.id = story_id
        temperature = ClimateComponent(
            series_id=f"{story_id}-temperature",
            publication_state="provisional",
            source=power_source(payload, utc_timestamp()),
            annual=parsed["annual"],
            monthly=[
                {"date": f"{k[:4]}-{k[4:]}-01", "value": parsed["data"]["T2M"][k]}
                for k in parsed["monthly_keys"]
            ],
            quality_flags=["local_review_pending", *parsed["issues"]],
            requested_coordinates=place.coordinates,
            warning=Localized(
                en="Newly retrieved regional data. Change comparisons require a scoped review; no local change claim is generated automatically.",
                bn="সদ্য সংগ্রহ করা আঞ্চলিক তথ্য। পরিবর্তনের তুলনার জন্য নির্দিষ্ট যাচাই দরকার; স্বয়ংক্রিয়ভাবে স্থানীয় পরিবর্তনের দাবি তৈরি হয় না।",
            ),
        )
        rain = ClimateComponent(
            series_id=f"{story_id}-rainfall-pending",
            publication_state="unavailable",
            source=imerg_source(utc_timestamp()),
            quality_flags=["earthdata_acquisition_pending"],
            warning=Localized(
                en="Verified precipitation is not available for this point yet.",
                bn="এই বিন্দুর যাচাই করা বৃষ্টির তথ্য এখনো নেই।",
            ),
        )
        imagery = pending_imagery(place)
        imagery.caption = Localized(
            en="Reviewed historical Landsat pairs are available for the 12 featured Bangladesh locations. Use the explorer for regional NASA imagery.",
            bn="যাচাই করা ঐতিহাসিক ল্যান্ডস্যাট জোড়া বাংলাদেশের ১২টি পরিচিত জায়গায় আছে। আঞ্চলিক NASA ছবির জন্য এক্সপ্লোরার ব্যবহার করো।",
        )
        story = StoryManifest(
            place=place,
            release=base.release,
            temperature=temperature,
            rainfall=rain,
            global_context=base.global_context,
            imagery=imagery,
            quiz=activity(place, imagery, quiz_bank()),
            actions=[
                ActionCard.model_validate(item)
                for item in read_json(settings.content_dir / "actions.json")
                if not item["tags"]
            ][:4],
        )
        # The row lock and generation token fence stale workers off from publication.
        with Session.begin() as session:
            job = session.scalar(
                select(ExplorationJobRecord)
                .where(ExplorationJobRecord.id == exploration_id)
                .with_for_update()
            )
            if (
                job is None
                or job.generation != generation
                or job.run_token != token
                or job.status != "running"
            ):
                return
            if job.lease_until is None or aware(job.lease_until) <= utcnow():
                fail_job(job, "Retrieval lease expired before publication. Please try again.", utcnow())
                return
            directory, checksum = publish_bundle(job.id, generation, story, payload)
            job.result_dir, job.result_hash = directory, checksum
            job.status, job.story_id, job.message = (
                "completed",
                story_id,
                "Regional observations are ready; comparisons remain provisional.",
            )
            job.run_token = None
            job.lease_until = None
            job.updated_at = utcnow()
    except Exception as error:
        with Session.begin() as session:
            job = session.scalar(
                select(ExplorationJobRecord)
                .where(ExplorationJobRecord.id == exploration_id)
                .with_for_update()
            )
            if (
                job is not None
                and job.generation == generation
                and job.run_token == token
                and job.status == "running"
            ):
                fail_job(
                    job,
                    f"NASA retrieval could not complete ({type(error).__name__}). Try again later or choose a featured story.",
                    utcnow(),
                )


def defer_exploration(session, job):
    """Use the app transaction's psycopg connection; Procrastinate must not commit it."""
    if session.bind.dialect.name != "postgresql":
        raise RuntimeError("The durable queue requires PostgreSQL")
    connection = session.connection().connection.driver_connection
    return explore_point.configure(
        connection=connection,
        queueing_lock=f"exploration:{job.id}:g{job.generation}",
    ).defer(exploration_id=job.id, generation=job.generation)


@app.task(queue="maintenance", retry=3)
def rebuild_release():
    from pipelines.build import build_release

    from .catalog import seed_release

    build_release()
    seed_release()


@app.task(queue="maintenance", retry=3)
def refresh_gistemp():
    from pipelines.refresh import refresh_global

    refresh_global()


def worker():
    reconcile_jobs()
    with app.open():
        app.run_worker(concurrency=1, queues=["climate", "maintenance"])
