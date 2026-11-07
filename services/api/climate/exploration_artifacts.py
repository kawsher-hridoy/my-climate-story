"""Complete, immutable exploration directories. Database completion controls visibility."""

import hashlib
import os
import shutil
import tempfile
from pathlib import Path

from .config import settings
from .files import digest, read_json, write_json
from .schemas import ClimateComponent, StoryManifest


class IncompleteExploration(ValueError):
    pass


def bundle_name(job_id: str, generation: int) -> str:
    if len(job_id) != 36 or any(char not in "0123456789abcdef-" for char in job_id) or generation < 0:
        raise IncompleteExploration("Invalid result identity")
    return f"{job_id}-g{generation}"


def bundle_parent(release_id: str) -> Path:
    if not release_id.startswith("mcs-") or any(
        char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in release_id
    ):
        raise IncompleteExploration("Invalid release identity")
    return settings.data_dir / "explorations" / release_id / "bundles"


def publish_bundle(job_id: str, generation: int, story: StoryManifest, raw: dict) -> tuple[str, str]:
    """Stage every dependency and rename once. Caller commits the DB result afterward."""
    verify_source_agreement(story, raw)
    for identifier in [story.place.id, story.temperature.series_id, story.rainfall.series_id]:
        if (
            not identifier
            or len(identifier) > 120
            or any(
                char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
                for char in identifier
            )
        ):
            raise IncompleteExploration("Invalid story or series identifier")
    if story.temperature.publication_state != "provisional" or story.temperature.comparison is not None:
        raise IncompleteExploration("Exploration cannot publish an approved comparison")
    name = bundle_name(job_id, generation)
    parent = bundle_parent(story.release.id)
    parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".staging-", dir=parent))
    try:
        write_json(stage / "source.json", raw)
        for component in [story.temperature, story.rainfall]:
            write_json(stage / "series" / f"{component.series_id}.json", component.model_dump(mode="json"))
        write_json(stage / "story.json", story.model_dump(mode="json"))
        files = {
            str(path.relative_to(stage)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(stage.rglob("*.json"))
        }
        manifest = {
            "version": 1,
            "job_id": job_id,
            "generation": generation,
            "story_id": story.place.id,
            "release_id": story.release.id,
            "files": files,
        }
        write_json(stage / "complete.json", manifest)
        for path in stage.rglob("*.json"):
            with path.open("rb") as handle:
                os.fsync(handle.fileno())
        target = parent / name
        if target.exists():
            existing = read_json(target / "complete.json")
            if existing != manifest:
                raise IncompleteExploration("Cannot overwrite a different completed artifact")
            for relative, checksum in manifest["files"].items():
                if hashlib.sha256((target / relative).read_bytes()).hexdigest() != checksum:
                    raise IncompleteExploration("Existing artifact content differs from its manifest")
        else:
            os.replace(stage, target)
            descriptor = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        return name, digest(manifest)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def verified_bundle(job) -> tuple[Path, StoryManifest]:
    """Never serve legacy loose files or a result merely because its story exists."""
    if job.status != "completed" or not job.result_dir or not job.result_hash:
        raise IncompleteExploration("Exploration has no completed publication")
    expected_name = bundle_name(job.id, job.generation)
    if job.result_dir != expected_name:
        raise IncompleteExploration("Unexpected exploration directory")
    folder = bundle_parent(job.release_id) / expected_name
    try:
        manifest = read_json(folder / "complete.json")
        if digest(manifest) != job.result_hash:
            raise IncompleteExploration("Completion manifest changed")
        if (
            manifest.get("job_id"),
            manifest.get("generation"),
            manifest.get("release_id"),
            manifest.get("story_id"),
        ) != (job.id, job.generation, job.release_id, job.story_id):
            raise IncompleteExploration("Completion identity mismatch")
        required = {"story.json", "source.json"}
        if not required.issubset(manifest.get("files", {})):
            raise IncompleteExploration("Missing source or story dependency")
        for relative, checksum in manifest["files"].items():
            path = folder / relative
            if Path(relative).is_absolute() or ".." in Path(relative).parts or path.is_symlink():
                raise IncompleteExploration("Invalid artifact path")
            if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
                raise IncompleteExploration("Artifact checksum changed")
        story = StoryManifest.model_validate(read_json(folder / "story.json"))
        if story.place.id != job.story_id or story.release.id != job.release_id:
            raise IncompleteExploration("Story identity changed")
        for component in [story.temperature, story.rainfall]:
            name = f"series/{component.series_id}.json"
            if (
                name not in manifest["files"]
                or ClimateComponent.model_validate(read_json(folder / name)) != component
            ):
                raise IncompleteExploration("Story/series dependency mismatch")
        verify_source_agreement(story, read_json(folder / "source.json"))
        return folder, story
    except (OSError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, IncompleteExploration):
            raise
        raise IncompleteExploration("Exploration artifacts are incomplete") from error


def verify_source_agreement(story: StoryManifest, raw: dict):
    from pipelines.science import validate_power

    parsed = validate_power(raw, strict=False)
    if [item.model_dump() for item in story.temperature.annual] != parsed["annual"]:
        raise IncompleteExploration("Annual temperature differs from its source")
    expected = [
        {"date": f"{key[:4]}-{key[4:]}-01", "value": parsed["data"]["T2M"][key]}
        for key in parsed["monthly_keys"]
    ]
    if [item.model_dump() for item in story.temperature.monthly] != expected:
        raise IncompleteExploration("Monthly temperature differs from its source")
    source = story.temperature.source
    if (source.id, source.unit, source.start, source.end, source.version) != (
        "nasa-power",
        "°C",
        raw["header"]["start"][:4],
        raw["header"]["end"][:4],
        raw["header"]["api"]["version"],
    ):
        raise IncompleteExploration("Temperature source metadata differs")
    if story.temperature.requested_coordinates != story.place.coordinates:
        raise IncompleteExploration("Requested coordinates differ")
    longitude, latitude = raw["geometry"]["coordinates"][:2]
    requested = story.place.coordinates
    longitude_distance = abs((longitude - requested.longitude + 180) % 360 - 180)
    if abs(latitude - requested.latitude) > 0.001001 or longitude_distance > 0.001001:
        raise IncompleteExploration("Source response belongs to a different requested location")


def migrate_legacy_bundle(job) -> bool:
    """Preserve old complete results only after checking actual source/series agreement."""
    if job.status != "completed" or not job.story_id or job.result_hash:
        return False
    root = settings.data_dir / "explorations" / job.release_id
    try:
        story = StoryManifest.model_validate(read_json(root / f"{job.story_id}.json"))
        series = ClimateComponent.model_validate(
            read_json(root / "series" / f"{story.temperature.series_id}.json")
        )
        raw = read_json(settings.raw_dir / "explorations" / f"{job.story_id}.json")
        if (
            story.release.id != job.release_id
            or story.place.id != job.story_id
            or series != story.temperature
        ):
            return False
        verify_source_agreement(story, raw)
        job.result_dir, job.result_hash = publish_bundle(job.id, job.generation, story, raw)
        return True
    except (OSError, ValueError, TypeError, KeyError):
        return False
