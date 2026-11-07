"""Validate complete candidates against pinned scientific inputs before publication."""

import csv
import io
import json
import math
from pathlib import Path

from climate.config import ROOT, settings
from climate.files import active_release, digest, read_json, write_json
from climate.schemas import ClimateComponent, ImageryPair, Place, ReleaseRef, StoryManifest

from .imagery_policy import approval_issues, asset_path, candidate_for, preparation_issues, processing_policy
from .release_io import FORMAT_VERSION, directory_hashes, safe_relative, sha256, snapshot_time
from .science import annual_rainfall, decade_comparison, monthly_rain_total, validate_power


def _equal_numbers(actual, expected) -> bool:
    if actual is None or expected is None:
        return actual is expected
    return (
        isinstance(actual, (int, float))
        and math.isfinite(actual)
        and math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9)
    )


def _same_observations(actual: list, expected: list, key: str) -> bool:
    if len(actual) != len(expected):
        return False
    rows = [row.model_dump(mode="json") if hasattr(row, "model_dump") else row for row in actual]
    if len({row.get(key) for row in rows}) != len(rows):
        return False
    return all(
        a.get(key) == b.get(key)
        and _equal_numbers(a.get("value"), b.get("value"))
        and a.get("complete", True) == b.get("complete", True)
        for a, b in zip(rows, expected, strict=True)
    )


def _gistemp_annual(raw: bytes) -> list[dict]:
    lines = raw.decode("utf-8-sig").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("Year,"))
    rows = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    result = [
        {"year": int(row["Year"]), "value": float(row["J-D"]), "complete": True}
        for row in rows
        if row.get("J-D") not in [None, "", "***"]
        and all(row.get(m) not in [None, "", "***"] for m in months)
    ]
    if not result or len({row["year"] for row in result}) != len(result):
        raise ValueError("Invalid GISTEMP annual source")
    return result


def _read_inputs(folder: Path, identity: dict, failures: list[str]) -> dict[str, bytes]:
    expected = identity.get("input_sha256", {})
    if not isinstance(expected, dict) or not expected:
        raise ValueError("Release has no pinned input manifest")
    if set(directory_hashes(folder / "inputs")) != set(expected):
        failures.append("Pinned input inventory differs")
    result = {}
    for name, checksum in expected.items():
        path = folder / "inputs" / safe_relative(name)
        try:
            raw = path.read_bytes()
            result[name] = raw
            if sha256(raw) != checksum:
                failures.append(f"Pinned input checksum differs: {name}")
        except OSError:
            failures.append(f"Pinned input is missing: {name}")
    return result


def _check_current_authority(files: dict[str, bytes], identity: dict, failures: list[str]) -> None:
    for name in [
        "places.json",
        "imagery-candidates.json",
        "imagery-reviews.json",
        "temperature-reviews.json",
    ]:
        path = settings.content_dir / name
        current = read_json(path) if path.exists() else {}
        if current != json.loads(files[f"content/{name}"]):
            failures.append(f"Current publication authority changed: {name}")
    if identity.get("imagery_policy") != processing_policy():
        failures.append("Current image processing policy changed")


def _validate_rainfall(component, place, files, failures) -> None:
    source_name = f"imerg/{place.id}.json"
    if source_name not in files:
        if (
            component.publication_state != "unavailable"
            or component.annual
            or component.monthly
            or component.comparison
        ):
            failures.append(f"{place.id}: missing precipitation source contains published values")
        return
    if (component.source.id, component.source.version, component.source.unit) != ("nasa-imerg", "V07B", "mm"):
        failures.append(f"{place.id}: precipitation source or units differ")
    if component.comparison is not None or component.publication_state == "comparison_approved":
        failures.append(f"{place.id}: precipitation comparison has no implemented approval policy")
    expected = ClimateComponent.model_validate(json.loads(files[source_name]))
    expected.series_id = component.series_id
    if component.model_dump(mode="json") != expected.model_dump(mode="json"):
        failures.append(f"{place.id}: precipitation component differs from pinned extraction")
    manifest_name = "imerg-source/extraction-manifest.json"
    if manifest_name not in files:
        failures.append(f"{place.id}: precipitation extraction provenance is missing")
        return
    extraction = json.loads(files[manifest_name])
    month_sources = {row["month"]: row for row in extraction.get("granules", [])}
    monthly = []
    for name, raw in sorted(files.items()):
        if not name.startswith("imerg-source/point-samples/"):
            continue
        sample = json.loads(raw)
        rows = [row for row in sample["records"] if row["place_id"] == place.id]
        if len(rows) != 1:
            failures.append(f"{place.id}: precipitation point source is missing or duplicated")
            continue
        row = rows[0]
        month = row["date"][:7]
        provenance = month_sources.get(month, {})
        if (
            provenance.get("granule_id") != sample["granule_id"]
            or provenance.get("sha256") != sample["sha256"]
        ):
            failures.append(f"{place.id}: precipitation granule identity differs for {month}")
        total = monthly_rain_total(row["native_rate_mm_hr"], int(month[:4]), int(month[5:]), "mm/hr")
        if not _equal_numbers(row["value"], total):
            failures.append(f"{place.id}: precipitation conversion differs for {month}")
        monthly.append({"date": row["date"], "value": total})
        if component.native_cell_center is None or not (
            _equal_numbers(component.native_cell_center.latitude, row["cell_latitude"])
            and _equal_numbers(component.native_cell_center.longitude, row["cell_longitude"])
        ):
            failures.append(f"{place.id}: precipitation cell identity differs")
    if not monthly or not _same_observations(component.monthly, monthly, "date"):
        failures.append(f"{place.id}: precipitation months differ from source rates")
    if not _same_observations(component.annual, annual_rainfall(monthly), "year"):
        failures.append(f"{place.id}: precipitation annual totals differ")


def validate_release(
    release_id: str | None = None,
    *,
    folder: Path | None = None,
    require_ready: bool = True,
    require_current_reviews: bool = True,
    write_report: bool = True,
) -> dict:
    """Validate a candidate/active release without activation; publication rechecks current authority."""
    if folder is None:
        if release_id is None:
            release_id, folder = active_release()
        else:
            if not release_id.startswith("mcs-") or safe_relative(release_id).name != release_id:
                raise ValueError("Invalid release identifier")
            folder = settings.data_dir / "releases" / release_id
    folder = Path(folder)
    manifest = read_json(folder / "release.json")
    if manifest.get("release_format") != FORMAT_VERSION:
        raise ValueError("Legacy release lacks pinned validation inputs; rebuild before publication")
    identity = manifest.get("identity", {})
    expected_id = f"mcs-{digest(identity)[:16]}"
    failures = []
    if manifest.get("id") != expected_id or (release_id is not None and release_id != expected_id):
        failures.append("Release identity differs from pinned dependencies")
    if folder.name.startswith("mcs-") and folder.name != expected_id:
        failures.append("Published directory name differs from release identity")
    release_id = expected_id
    files = _read_inputs(folder, identity, failures)
    if failures:
        raise ValueError("Release validation failed: " + "; ".join(failures))
    if identity.get("release_format") != FORMAT_VERSION or manifest.get("processing_version") != identity.get(
        "processing_version"
    ):
        failures.append("Release processing version differs")
    if manifest.get("code_sha256") != identity.get("code_sha256"):
        failures.append("Release processing-code identity differs")
    output_hashes = {
        name: value
        for name, value in directory_hashes(folder, exclude=("release.json",)).items()
        if not name.startswith("inputs/")
    }
    if output_hashes != manifest.get("output_sha256"):
        failures.append("Published output checksums/inventory differ")
    if require_current_reviews:
        _check_current_authority(files, identity, failures)
    if manifest.get("created_at") != snapshot_time(files):
        failures.append("Release timestamp differs from pinned provenance")
    content = {Path(name).name: json.loads(raw) for name, raw in files.items() if name.startswith("content/")}
    if manifest.get("content_version") != digest(content)[:12]:
        failures.append("Content release identity differs")
    place_list = [Place.model_validate(row) for row in content["places.json"]]
    ids = [place.id for place in place_list]
    if len(ids) != 12 or len(set(ids)) != len(ids) or manifest.get("place_ids") != ids:
        failures.append("Curated place inventory differs")
    inventory = json.loads(files["archive-inventory.json"])
    if manifest.get("archive_inventory") != inventory:
        failures.append("Archive provenance differs")
    source_records = {row["place_id"]: row for row in manifest.get("source_requests", [])}
    if len(source_records) != len(ids) or len(manifest.get("source_requests", [])) != len(ids):
        failures.append("Source request inventory differs")
    parsed = {place.id: validate_power(json.loads(files[f"power/{place.id}.json"])) for place in place_list}
    hashes = {key: digest(value["data"]) for key, value in parsed.items()}
    global_annual = _gistemp_annual(files["gistemp/Global_Temperature_Data_GISTEMP.csv"])
    clean_global = [
        {"year": int(row["year"]), "value": float(row["temperature_anomaly_c"]), "complete": True}
        for row in csv.DictReader(
            io.StringIO(files["gistemp/Global_Temperature_Annual_Clean.csv"].decode("utf-8-sig"))
        )
    ]
    if not _same_observations(clean_global, global_annual, "year"):
        failures.append("Prepared GISTEMP values differ from original annual source")
    release_ref = ReleaseRef.model_validate(manifest)
    measurements, images, activities, approvals = 0, 0, 0, 0
    referenced_series = set()
    referenced_assets = set()
    for place in place_list:
        place_id = place.id
        try:
            story = StoryManifest.model_validate(read_json(folder / "stories" / f"{place_id}.json"))
            checks = parsed[place_id]
            raw = json.loads(files[f"power/{place_id}.json"])
            measurements += checks["numeric_values"]
            if story.place != place or story.release != release_ref:
                failures.append(f"{place_id}: story place/release identity differs")
            monthly = [
                {"date": f"{key[:4]}-{key[4:]}-01", "value": checks["data"]["T2M"][key]}
                for key in checks["monthly_keys"]
            ]
            if not _same_observations(story.temperature.monthly, monthly, "date"):
                failures.append(f"{place_id}: published temperature months differ from raw source")
            if not _same_observations(story.temperature.annual, checks["annual"], "year"):
                failures.append(f"{place_id}: published annual temperatures differ from source aggregation")
            if (
                story.temperature.series_id
                != f"power-t2m-{place_id}-{digest(monthly)[:16]}-{release_id[4:12]}"
            ):
                failures.append(f"{place_id}: temperature component identity differs")
            if story.temperature.requested_coordinates != place.coordinates:
                failures.append(f"{place_id}: requested temperature coordinates differ")
            shared = [key for key in ids if key != place_id and hashes[key] == hashes[place_id]]
            if story.temperature.shared_series_with != shared:
                failures.append(f"{place_id}: shared-series provenance differs")
            source = story.temperature.source
            if (source.id, source.version, source.unit, source.start, source.end, source.retrieved_at) != (
                "nasa-power",
                raw["header"]["api"]["version"],
                "°C",
                raw["header"]["start"][:4],
                raw["header"]["end"][:4],
                inventory["imported_at"],
            ):
                failures.append(f"{place_id}: temperature source metadata differs")
            request = source_records.get(place_id, {})
            request_hash = sha256(files[f"power/{place_id}.json"])
            if request.get("sha256") != request_hash or request.get("id") != request_hash:
                failures.append(f"{place_id}: source request checksum differs")
            if (
                request.get("requested_coordinates") != place.coordinates.model_dump()
                or request.get("retrieved_at") != inventory["imported_at"]
            ):
                failures.append(f"{place_id}: source request provenance differs")
            expected_url = (
                "https://power.larc.nasa.gov/api/temporal/monthly/point"
                "?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M&community=AG"
                f"&longitude={place.coordinates.longitude}&latitude={place.coordinates.latitude}"
                "&start=1981&end=2025&format=JSON"
            )
            if (
                request.get("dataset"),
                request.get("place_id"),
                request.get("version"),
                request.get("source_url"),
            ) != ("nasa-power", place_id, raw["header"]["api"]["version"], expected_url):
                failures.append(f"{place_id}: source request identity/URL differs")
            review = content["temperature-reviews.json"].get(place_id, {})
            approved = (
                review.get("data_hash") == hashes[place_id]
                and review.get("status") == "comparison_approved"
                and review.get("windows") == ["2001–2010", "2016–2025"]
            )
            comparison = story.temperature.comparison
            metrics = decade_comparison(checks["annual"])
            if approved and metrics:
                if comparison is None or story.temperature.publication_state != "comparison_approved":
                    failures.append(f"{place_id}: approved comparison is missing")
                else:
                    if any(
                        not _equal_numbers(getattr(comparison, key), metrics[key])
                        for key in ["baseline_value", "recent_value", "difference"]
                    ):
                        failures.append(f"{place_id}: comparison values differ from recomputed means")
                    if (
                        comparison.baseline_period,
                        comparison.recent_period,
                        comparison.review_id,
                        comparison.unit,
                        comparison.method,
                        comparison.publication_state,
                    ) != (
                        metrics["baseline_period"],
                        metrics["recent_period"],
                        review.get("id"),
                        "°C",
                        "complete-decade-means",
                        "comparison_approved",
                    ):
                        failures.append(f"{place_id}: comparison review/window identity differs")
                    approvals += 1
            elif comparison is not None or story.temperature.publication_state != "descriptive_only":
                failures.append(f"{place_id}: unauthorized temperature comparison")
            if (
                story.global_context.baseline != "1951–1980"
                or story.global_context.source.id != "nasa-gistemp"
                or story.global_context.source.unit != "°C anomaly"
            ):
                failures.append(f"{place_id}: global source/baseline differs")
            if not _same_observations(story.global_context.annual, global_annual, "year"):
                failures.append(f"{place_id}: global observations differ from source")
            if story.global_context.source.retrieved_at != inventory["imported_at"]:
                failures.append(f"{place_id}: global provenance differs")
            _validate_rainfall(story.rainfall, place, files, failures)
            for component in [story.temperature, story.rainfall]:
                if component.series_id in referenced_series:
                    failures.append(f"{place_id}: component ID is shared across places")
                referenced_series.add(component.series_id)
                if read_json(folder / "series" / f"{component.series_id}.json") != component.model_dump(
                    mode="json"
                ):
                    failures.append(f"{place_id}: series endpoint payload differs from story")
            pair = story.imagery
            pair_name = f"imagery/{place_id}.json"
            if pair_name in files:
                if pair != ImageryPair.model_validate(json.loads(files[pair_name])):
                    failures.append(f"{place_id}: imagery differs from pinned preparation")
                proc_name = f"imagery-metadata/processing-{place_id}.json"
                processing = json.loads(files[proc_name]) if proc_name in files else None
                scenes = {
                    asset.product_id: json.loads(files[f"imagery-metadata/{asset.product_id}.json"])
                    for asset in [pair.before, pair.after]
                    if asset is not None and f"imagery-metadata/{asset.product_id}.json" in files
                }
                errors = preparation_issues(
                    pair,
                    place,
                    candidate_for(place_id, content["imagery-candidates.json"]),
                    processing,
                    assets_dir=settings.data_dir / "assets",
                    asset_base=identity["asset_base"],
                    policy=identity["imagery_policy"],
                    scenes=scenes,
                )
                failures.extend(f"{place_id}: {error}" for error in errors)
                canonical = content["imagery-reviews.json"].get(place_id)
                if pair.status == "approved":
                    failures.extend(f"{place_id}: {error}" for error in approval_issues(pair, canonical))
                    if pair.review != canonical:
                        failures.append(
                            f"{place_id}: embedded imagery approval differs from canonical review"
                        )
                    images += 2
                elif pair.review is not None:
                    failures.append(f"{place_id}: unapproved imagery retains a review label")
                for asset in [pair.before, pair.after]:
                    if asset is not None:
                        for url in [asset.url, asset.thumbnail_url]:
                            path = asset_path(
                                url, place_id, settings.data_dir / "assets", identity["asset_base"]
                            )
                            referenced_assets.add(path.relative_to(settings.data_dir / "assets").as_posix())
            elif pair.status not in ["pending", "unavailable"] or pair.before or pair.after:
                failures.append(f"{place_id}: imagery has no pinned input")
            if require_ready and pair.status != "approved":
                failures.append(f"{place_id}: imagery review is incomplete")
            if len(story.quiz) != 5 or len(story.actions) < 3:
                failures.append(f"{place_id}: learning activity is incomplete")
            if any(not 0 <= question.correct_index < len(question.options) for question in story.quiz):
                failures.append(f"{place_id}: quiz answer index is invalid")
            activities += 1
        except (OSError, ValueError, KeyError, TypeError) as error:
            failures.append(
                f"{place_id}: invalid or missing release dependency ({type(error).__name__}: {error})"
            )
    expected_assets = identity.get("asset_sha256", {})
    if referenced_assets != set(expected_assets):
        failures.append("Referenced image inventory differs from pinned asset hashes")
    for name, checksum in expected_assets.items():
        path = settings.data_dir / "assets" / safe_relative(name)
        if not path.is_file() or sha256(path.read_bytes()) != checksum:
            failures.append(f"Image dependency checksum differs: {name}")
    ready = images == 2 * len(ids)
    if manifest.get("publication_state") != ("ready" if ready else "draft"):
        failures.append("Release readiness label differs")
    if require_ready and not ready:
        failures.append("Release is not ready for publication")
    if (
        manifest.get("approved_imagery_count") != images // 2
        or manifest.get("approved_temperature_count") != approvals
    ):
        failures.append("Release approval counts differ")
    if manifest.get("content_questions") != len(content["question-bank.json"]):
        failures.append("Question-bank inventory differs")
    pending = any(f"imerg/{place_id}.json" not in files for place_id in ids)
    if manifest.get("rainfall_pending") != pending:
        failures.append("Precipitation availability differs")
    report = {
        "release_id": release_id,
        "passed": not failures,
        "ready": ready,
        "places": len(ids),
        "power_numeric_values": measurements,
        "reviewed_images": images,
        "temperature_comparisons": approvals,
        "activities": activities,
        "question_bank": len(content["question-bank.json"]),
        "rainfall_pending": pending,
        "accepted_amendment": "User authorized rainfall pending.",
        "failures": failures,
    }
    if write_report:
        write_json(ROOT / "data" / "manifests" / "validation.json", report)
    if failures:
        raise ValueError("Release validation failed: " + "; ".join(failures))
    return report
