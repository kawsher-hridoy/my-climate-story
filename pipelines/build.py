import csv
import hashlib
import io
import json
import os
import random
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from climate.config import ROOT, settings
from climate.files import digest, read_json, write_json
from climate.schemas import (
    ActionCard,
    ClimateComponent,
    Comparison,
    GlobalContext,
    ImageryPair,
    Localized,
    Place,
    QuizQuestion,
    ReleaseRef,
    SourceMetadata,
    StoryManifest,
)

from .release_io import (
    FORMAT_VERSION,
    Inputs,
    capture_inputs,
    directory_hashes,
    publication_lock,
    sha256,
    snapshot_time,
)
from .science import decade_comparison, validate_power

PROCESSING_VERSION = "calendar-aware-v3"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def places() -> list[Place]:
    return [Place.model_validate(x) for x in read_json(settings.content_dir / "places.json")]


def import_archive() -> dict:
    archive_path = ROOT / "climate_data.zip"
    with zipfile.ZipFile(archive_path) as archive:
        report = {
            "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
            "archive_files": len(archive.infolist()),
            "archive_uncompressed_bytes": sum(x.file_size for x in archive.infolist()),
            "imported_at": utc_timestamp(),
            "locations": [],
            "numeric_values": 0,
        }
        for place in places():
            member = f"climate_data/raw_nasa_power/NASA_POWER_{place.id}.json"
            raw = archive.read(member)
            payload = json.loads(raw)
            validation = validate_power(payload)
            destination = settings.raw_dir / "power" / f"{place.id}.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and read_json(destination) != payload:
                raise ValueError(
                    f"Existing source for {place.id} differs; select its source explicitly before reimport"
                )
            if not destination.exists() or destination.read_bytes() != raw:
                destination.write_bytes(raw)
            report["numeric_values"] += validation["numeric_values"]
            report["locations"].append(
                {
                    "id": place.id,
                    "monthly_records": len(validation["monthly_keys"]),
                    "annual_records": len(validation["annual_keys"]),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
        for filename in [
            "Global_Temperature_Data_GISTEMP.csv",
            "Global_Temperature_Annual_Clean.csv",
            "Global_Temperature_Monthly_Clean.csv",
        ]:
            destination = settings.raw_dir / "gistemp" / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(archive.read(f"climate_data/global_gistemp/{filename}"))
    destination = settings.raw_dir / "archive-inventory.json"
    if destination.exists():
        previous = read_json(destination)
        report["imported_at"] = previous["imported_at"]
    write_json(destination, report)
    return report


def power_source(payload: dict, retrieved_at: str) -> SourceMetadata:
    return SourceMetadata(
        id="nasa-power",
        name="NASA POWER / MERRA-2",
        version=payload["header"]["api"]["version"],
        unit="°C",
        source_url="https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/",
        citation="NASA POWER Project, NASA Langley Research Center. MERRA-2 meteorology; monthly point API.",
        spatial_resolution="0.5° latitude × 0.625° longitude; ground width varies with latitude",
        start=payload["header"]["start"][:4],
        end=payload["header"]["end"][:4],
        retrieved_at=retrieved_at,
        license="NASA open data",
        notes=Localized(
            en="Regional gridded estimates around your selected place, not a thermometer at your home.",
            bn="তোমার নির্বাচিত এলাকার আশপাশের আঞ্চলিক গ্রিডের অনুমান; বাড়ির থার্মোমিটারের মাপ নয়।",
        ),
    )


def imerg_source(retrieved_at: str) -> SourceMetadata:
    return SourceMetadata(
        id="nasa-imerg",
        name="NASA GPM IMERG Final",
        version="V07B",
        unit="mm",
        source_url="https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imergm-07",
        citation="NASA GPM IMERG Final monthly V07, DOI:10.5067/GPM/IMERG/3B-MONTH/07.",
        spatial_resolution="0.1° × 0.1° (approximately 10 km)",
        start="1998",
        end="2024",
        retrieved_at=retrieved_at,
        license="NASA open data",
        notes=Localized(
            en="Precipitation includes rain and snow. Full years require all 12 valid months.",
            bn="প্রিসিপিটেশনে বৃষ্টি আর তুষার থাকে। পুরো বছরের জন্য ১২ মাসের বৈধ তথ্য দরকার।",
        ),
    )


def global_context(retrieved_at: str, annual_csv: bytes | None = None) -> GlobalContext:
    if annual_csv is None:
        annual_csv = (settings.raw_dir / "gistemp" / "Global_Temperature_Annual_Clean.csv").read_bytes()
    annual = [
        {"year": int(row["year"]), "value": float(row["temperature_anomaly_c"]), "complete": True}
        for row in csv.DictReader(io.StringIO(annual_csv.decode("utf-8-sig")))
    ]
    return GlobalContext(
        baseline="1951–1980",
        annual=annual,
        source=SourceMetadata(
            id="nasa-gistemp",
            name="NASA GISS GISTEMP",
            version="v4",
            unit="°C anomaly",
            source_url="https://data.giss.nasa.gov/gistemp/",
            citation="GISTEMP Team, GISS Surface Temperature Analysis v4, NASA GISS (2026). Lenssen et al. (2024), doi:10.1029/2023JD040179.",
            spatial_resolution="Global land–ocean mean",
            start=str(annual[0]["year"]),
            end=str(annual[-1]["year"]),
            retrieved_at=retrieved_at,
            license="NASA open data",
            notes=Localized(
                en="Global temperature differences from the 1951–1980 average, not local Bangladesh temperatures.",
                bn="১৯৫১–১৯৮০ সালের গড় থেকে বৈশ্বিক তাপমাত্রার পার্থক্য; বাংলাদেশের স্থানীয় তাপমাত্রা নয়।",
            ),
        ),
    )


def quiz_bank(entries: list[dict] | None = None) -> list[QuizQuestion]:
    result = []
    for entry in entries if entries is not None else read_json(settings.content_dir / "question-bank.json"):
        result.append(
            QuizQuestion(
                id=entry["id"],
                category=entry["category"],
                question=Localized(en=entry["question"][0], bn=entry["question"][1]),
                options=[Localized(en=x[0], bn=x[1]) for x in entry["options"]],
                correct_index=entry["correct"],
                explanation=Localized(en=entry["explanation"][0], bn=entry["explanation"][1]),
                source_url=entry["source"],
            )
        )
    return result


def activity(place: Place, imagery: ImageryPair, bank: list[QuizQuestion]) -> list[QuizQuestion]:
    rng = random.Random(place.id)
    chosen = []
    for category in ["concept", "data", "imagery", "action"]:
        chosen.append(rng.choice([q for q in bank if q.category == category]).model_copy(deep=True))
    if imagery.status == "approved" and imagery.before:
        old_option = rng.randrange(2)
        chosen.append(
            QuizQuestion(
                id=f"image-{place.id}",
                category="imagery",
                image_question=True,
                question=Localized(
                    en=f"Which view of {place.name.en} is the historical image?",
                    bn=f"{place.name.bn}-এর কোন দৃশ্যটি পুরোনো?",
                ),
                options=[Localized(en="Image A", bn="ছবি ক"), Localized(en="Image B", bn="ছবি খ")],
                correct_index=old_option,
                explanation=Localized(
                    en=f"The historical image was acquired on {imagery.before.date}. The source records confirm its date.",
                    bn=f"পুরোনো ছবিটি {imagery.before.date} তারিখের। উৎসের রেকর্ড তারিখটি নিশ্চিত করে।",
                ),
                source_url=imagery.before.source_url,
            )
        )
    else:
        remaining = [q for q in bank if q.id not in {x.id for x in chosen} and q.category == "concept"]
        chosen.append(rng.choice(remaining).model_copy(deep=True))
    for question in chosen:
        if not question.image_question:
            original = list(enumerate(question.options))
            rng.shuffle(original)
            question.correct_index = next(
                i for i, (old, _) in enumerate(original) if old == question.correct_index
            )
            question.options = [option for _, option in original]
    return chosen


def pending_imagery(place: Place) -> ImageryPair:
    return ImageryPair(
        id=place.id,
        status="pending",
        caption=Localized(
            en="A historical comparison is being prepared. Only retrieved and reviewed real imagery will appear here.",
            bn="পুরোনো আর নতুন ছবির তুলনা তৈরি হচ্ছে। শুধু সংগ্রহ করা ও যাচাই করা আসল ছবি এখানে দেখানো হবে।",
        ),
    )


def _render_release(inputs: Inputs, folder: Path, release_id: str, identity: dict) -> dict:
    inventory = inputs.json("archive-inventory.json")
    all_places = [Place.model_validate(x) for x in inputs.json("content/places.json")]
    bank = quiz_bank(inputs.json("content/question-bank.json"))
    action_bank = [ActionCard.model_validate(x) for x in inputs.json("content/actions.json")]
    reviews = inputs.json("content/temperature-reviews.json")
    payloads = {place.id: inputs.json(f"power/{place.id}.json") for place in all_places}
    imagery = {}
    rainfall = {}
    for place in all_places:
        path = f"imagery/{place.id}.json"
        imagery[place.id] = (
            ImageryPair.model_validate(inputs.json(path)) if path in inputs.files else pending_imagery(place)
        )
        rain_path = f"imerg/{place.id}.json"
        if rain_path in inputs.files:
            rainfall[place.id] = ClimateComponent.model_validate(inputs.json(rain_path))
            rainfall[place.id].series_id = f"imerg-{place.id}-{release_id[4:12]}"
    content = {Path(name).name: inputs.json(name) for name in inputs.files if name.startswith("content/")}
    release = ReleaseRef(
        id=release_id,
        created_at=snapshot_time(inputs.files),
        processing_version=PROCESSING_VERSION,
        content_version=digest(content)[:12],
        rainfall_pending=len(rainfall) < len(all_places),
    )
    global_data = global_context(
        inventory["imported_at"], inputs.files["gistemp/Global_Temperature_Annual_Clean.csv"]
    )
    normalized = {key: validate_power(value) for key, value in payloads.items()}
    hashes = {key: digest(value["data"]) for key, value in normalized.items()}
    requests = []
    approved_comparisons = 0
    for place in all_places:
        payload, parsed = payloads[place.id], normalized[place.id]
        raw_hash = sha256(inputs.files[f"power/{place.id}.json"])
        request = {
            "id": raw_hash,
            "dataset": "nasa-power",
            "place_id": place.id,
            "sha256": raw_hash,
            "requested_coordinates": place.coordinates.model_dump(),
            "version": payload["header"]["api"]["version"],
            "retrieved_at": inventory["imported_at"],
            "source_url": f"https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M&community=AG&longitude={place.coordinates.longitude}&latitude={place.coordinates.latitude}&start=1981&end=2025&format=JSON",
        }
        requests.append(request)
        monthly = [
            {"date": f"{key[:4]}-{key[4:]}-01", "value": parsed["data"]["T2M"][key]}
            for key in parsed["monthly_keys"]
        ]
        series_id = f"power-t2m-{place.id}-{digest(monthly)[:16]}-{release_id[4:12]}"
        review = reviews.get(place.id, {})
        approved = (
            review.get("data_hash") == hashes[place.id]
            and review.get("status") == "comparison_approved"
            and review.get("windows") == ["2001–2010", "2016–2025"]
        )
        comparison = None
        metrics = decade_comparison(parsed["annual"])
        if approved and metrics:
            approved_comparisons += 1
            rounded = round(metrics["difference"], 1)
            recent = f"{metrics['recent_value']:.1f}"
            difference = f"{abs(rounded):.1f}"
            if rounded == 0:
                explanation = Localized(
                    en="The two decade averages are similar at the precision shown. This does not describe every day or the whole climate system.",
                    bn="দেখানো নির্ভুলতার মাত্রায় দুই দশকের গড় কাছাকাছি। এটি প্রতিটি দিন বা পুরো জলবায়ু ব্যবস্থা বোঝায় না।",
                )
            else:
                direction, bn_direction = ("higher", "বেশি") if rounded > 0 else ("lower", "কম")
                explanation = Localized(
                    en=f"In this dataset, average temperature around {place.name.en} was {recent}°C in 2016–2025, {difference}°C {direction} than in 2001–2010.",
                    bn=f"এই তথ্য অনুযায়ী, {place.name.bn}-এর আশপাশে ২০১৬–২০২৫ সালে গড় তাপমাত্রা {recent}°C, যা ২০০১–২০১০ সালের তুলনায় {difference}°C {bn_direction}।",
                )
            comparison = Comparison(
                **metrics,
                unit="°C",
                publication_state="comparison_approved",
                review_id=review["id"],
                explanation=explanation,
            )
        temperature = ClimateComponent(
            series_id=series_id,
            publication_state="comparison_approved" if comparison else "descriptive_only",
            source=power_source(payload, inventory["imported_at"]),
            annual=parsed["annual"],
            monthly=monthly,
            comparison=comparison,
            quality_flags=["pre_2001_suspected_discontinuity"],
            warning=Localized(
                en="The older record has a suspected discontinuity. The default view starts in 2001; comparisons are descriptive, not a claim about cause.",
                bn="পুরোনো রেকর্ডে ধারাবাহিকতার সমস্যা সন্দেহ করা হয়েছে। মূল দৃশ্য ২০০১ থেকে; তুলনা বর্ণনামূলক, কারণের দাবি নয়।",
            ),
            shared_series_with=[
                key for key, value in hashes.items() if key != place.id and value == hashes[place.id]
            ],
            requested_coordinates=place.coordinates,
        )
        rain = rainfall.get(place.id) or ClimateComponent(
            series_id=f"imerg-pending-{place.id}-{release_id[4:12]}",
            publication_state="unavailable",
            source=imerg_source(inventory["imported_at"]),
            quality_flags=["earthdata_acquisition_pending"],
            warning=Localized(
                en="Verified NASA IMERG rainfall measurements have not been downloaded yet. We do not use the discontinuous POWER rainfall record for change claims.",
                bn="যাচাই করা NASA IMERG বৃষ্টির তথ্য এখনো সংগ্রহ করা হয়নি। ধারাবাহিকতার সমস্যা থাকা POWER বৃষ্টির তথ্য দিয়ে পরিবর্তনের দাবি করা হয় না।",
            ),
        )
        matched = [a for a in action_bank if not a.tags or set(a.tags).intersection(place.tags)]
        matched.sort(key=lambda a: (not bool(set(a.tags).intersection(place.tags)), a.id))
        chosen_actions = [
            next(a for a in matched if a.audience == audience) for audience in ["student", "family", "school"]
        ]
        chosen_actions.extend(a for a in matched if a.id not in {item.id for item in chosen_actions})
        story = StoryManifest(
            place=place,
            release=release,
            temperature=temperature,
            rainfall=rain,
            global_context=global_data,
            imagery=imagery[place.id],
            quiz=activity(place, imagery[place.id], bank),
            actions=chosen_actions[:4],
        )
        write_json(folder / "stories" / f"{place.id}.json", story.model_dump(mode="json"))
        for component in [temperature, rain]:
            write_json(folder / "series" / f"{component.series_id}.json", component.model_dump(mode="json"))
    write_json(folder / "places.json", [p.model_dump(mode="json") for p in all_places])
    for source in [
        power_source(next(iter(payloads.values())), inventory["imported_at"]),
        imerg_source(inventory["imported_at"]),
        global_data.source,
    ]:
        write_json(folder / "sources" / f"{source.id}.json", source.model_dump(mode="json"))
    manifest = {
        **release.model_dump(mode="json"),
        "release_format": FORMAT_VERSION,
        "identity": identity,
        "publication_state": "ready"
        if all(pair.status == "approved" for pair in imagery.values())
        else "draft",
        "source_requests": requests,
        "archive_inventory": inventory,
        "place_ids": [p.id for p in all_places],
        "approved_imagery_count": sum(x.status == "approved" for x in imagery.values()),
        "approved_temperature_count": approved_comparisons,
        "code_sha256": inputs.code_hash,
        "source_periods": {
            "temperature": "1981–2025",
            "global": "1880–2025",
            "rainfall": "pending" if release.rainfall_pending else "1998–latest complete year",
        },
        "content_questions": len(bank),
        "execution_amendment": "User accepted rainfall pending until Earthdata credentials are configured.",
    }
    manifest["output_sha256"] = {
        name: checksum
        for name, checksum in directory_hashes(folder).items()
        if not name.startswith("inputs/")
    }
    write_json(folder / "release.json", manifest)
    return manifest


def build_release(*, activate: bool = True) -> dict:
    """Build a complete candidate and validate it before changing any published pointer.

    activate=False permits an integrity-checked draft with pending imagery. Such a
    draft is never made active and cannot be remotely published as a ready release.
    """
    from .validation import validate_release

    inputs = capture_inputs()
    identity = inputs.identity(PROCESSING_VERSION)
    release_id = f"mcs-{digest(identity)[:16]}"
    releases_dir = settings.data_dir / "releases"
    releases_dir.mkdir(parents=True, exist_ok=True)
    candidate = Path(tempfile.mkdtemp(prefix=".candidate-", dir=releases_dir))
    destination = releases_dir / release_id
    try:
        inputs.write(candidate)
        manifest = _render_release(inputs, candidate, release_id, identity)
        with publication_lock():
            report = validate_release(
                folder=candidate, require_ready=activate, require_current_reviews=True, write_report=False
            )
            if destination.exists():
                if directory_hashes(destination) != directory_hashes(candidate):
                    raise ValueError(f"Immutable release {release_id} already exists with different content")
            else:
                os.rename(candidate, destination)
            if activate:
                # Reports may describe a validated candidate; only this final pointer makes it live.
                write_json(ROOT / "data" / "manifests" / "latest.json", manifest)
                write_json(ROOT / "data" / "manifests" / "validation.json", report)
                write_json(settings.data_dir / "active.json", {"id": release_id})
        return {
            "id": release_id,
            "places": len(manifest["place_ids"]),
            "imagery_approved": manifest["approved_imagery_count"],
            "rainfall_pending": manifest["rainfall_pending"],
            "activated": activate,
        }
    finally:
        if candidate.exists():
            shutil.rmtree(candidate)


def review_temperature(reviewer: str, evidence: str) -> dict:
    if len(evidence.strip()) < 30 or not reviewer.strip():
        raise ValueError("A named reviewer and substantive review evidence are required")
    result = {}
    for place in places():
        payload = read_json(settings.raw_dir / "power" / f"{place.id}.json")
        parsed = validate_power(payload)
        if decade_comparison(parsed["annual"]) is None:
            raise ValueError(f"Incomplete comparison windows for {place.id}")
        result[place.id] = {
            "id": f"temperature-{place.id}-{digest(parsed['data'])[:12]}",
            "data_hash": digest(parsed["data"]),
            "status": "comparison_approved",
            "windows": ["2001–2010", "2016–2025"],
            "reviewer": reviewer,
            "reviewed_at": utc_timestamp(),
            "evidence": evidence,
            "scope": "Descriptive arithmetic comparison only; no trend significance, causal attribution, or hot-day inference.",
        }
    with publication_lock():
        write_json(settings.content_dir / "temperature-reviews.json", result)
    return {"approved": len(result)}
