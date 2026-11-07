"""Pinned public inputs and immutable directory publication for scientific releases."""

import fcntl
import hashlib
import json
import re
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from climate.config import ROOT, settings
from climate.files import digest, read_json
from climate.schemas import ImageryPair, Place

from .imagery_policy import asset_path, candidate_for, processing_policy, reconcile_pair

FORMAT_VERSION = 2
CONTENT_FILES = (
    "places.json",
    "question-bank.json",
    "actions.json",
    "imagery-candidates.json",
    "temperature-reviews.json",
    "imagery-reviews.json",
)
GISTEMP_FILES = (
    "Global_Temperature_Data_GISTEMP.csv",
    "Global_Temperature_Annual_Clean.csv",
    "Global_Temperature_Monthly_Clean.csv",
)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def safe_relative(name: str) -> Path:
    value = PurePosixPath(name)
    if value.is_absolute() or not value.parts or any(part in (".", "..") for part in value.parts):
        raise ValueError("Invalid release member path")
    return Path(*value.parts)


def snapshot_time(files: dict[str, bytes]) -> str:
    """Stable effective timestamp from pinned inputs; rebuild wall-clock time is not release content."""
    times = []

    def collect(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"imported_at", "retrieved_at", "reviewed_at", "discovered_at"} and isinstance(
                    item, str
                ):
                    try:
                        instant = datetime.fromisoformat(item.replace("Z", "+00:00"))
                        if instant.tzinfo is not None:
                            times.append(instant.astimezone(timezone.utc))
                    except ValueError:
                        pass
                else:
                    collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    for name, raw in files.items():
        if name.endswith(".json"):
            collect(json.loads(raw))
    if not times:
        raise ValueError("A release requires a pinned acquisition timestamp")
    return max(times).isoformat()


@dataclass
class Inputs:
    files: dict[str, bytes]
    assets: dict[str, str]
    policy: dict
    asset_base: str
    code_hash: str

    def json(self, name: str):
        return json.loads(self.files[name])

    def identity(self, processing_version: str) -> dict:
        return {
            "release_format": FORMAT_VERSION,
            "processing_version": processing_version,
            "code_sha256": self.code_hash,
            "input_sha256": {name: sha256(raw) for name, raw in sorted(self.files.items())},
            "asset_sha256": dict(sorted(self.assets.items())),
            "asset_base": self.asset_base,
            "imagery_policy": self.policy,
        }

    def write(self, folder: Path) -> None:
        for name, raw in self.files.items():
            path = folder / "inputs" / safe_relative(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)


def capture_inputs() -> Inputs:
    files = {"archive-inventory.json": (settings.raw_dir / "archive-inventory.json").read_bytes()}
    for name in CONTENT_FILES:
        path = settings.content_dir / name
        if path.exists():
            files[f"content/{name}"] = path.read_bytes()
        elif name.endswith("reviews.json"):
            files[f"content/{name}"] = json_bytes({})
        else:
            raise FileNotFoundError(f"Required public content is missing: {name}")
    places = [Place.model_validate(item) for item in json.loads(files["content/places.json"])]
    candidates = json.loads(files["content/imagery-candidates.json"])
    reviews = json.loads(files["content/imagery-reviews.json"])
    assets = {}
    policy = processing_policy()
    for place in places:
        if not re.fullmatch(r"[a-z0-9_-]+", place.id):
            raise ValueError("Invalid curated place identifier")
        files[f"power/{place.id}.json"] = (settings.raw_dir / "power" / f"{place.id}.json").read_bytes()
        processing_path = settings.raw_dir / "imagery-metadata" / f"processing-{place.id}.json"
        processing = None
        if processing_path.exists():
            files[f"imagery-metadata/processing-{place.id}.json"] = processing_path.read_bytes()
            processing = json.loads(files[f"imagery-metadata/processing-{place.id}.json"])
        pair_path = settings.data_dir / "imagery" / f"{place.id}.json"
        if pair_path.exists():
            pair = ImageryPair.model_validate(read_json(pair_path))
            scenes = {}
            for asset in [pair.before, pair.after]:
                if asset is None:
                    continue
                source = settings.raw_dir / "imagery-metadata" / f"{asset.product_id}.json"
                if source.exists():
                    files[f"imagery-metadata/{asset.product_id}.json"] = source.read_bytes()
                    scenes[asset.product_id] = json.loads(files[f"imagery-metadata/{asset.product_id}.json"])
                for url in [asset.url, asset.thumbnail_url]:
                    path = asset_path(
                        url, place.id, settings.data_dir / "assets", settings.public_asset_base_url
                    )
                    # Missing declared dependencies fail before a candidate can be activated.
                    assets[path.relative_to(settings.data_dir / "assets").as_posix()] = sha256(
                        path.read_bytes()
                    )
            pair, _, _ = reconcile_pair(
                pair,
                place,
                candidate_for(place.id, candidates),
                processing,
                reviews.get(place.id),
                assets_dir=settings.data_dir / "assets",
                asset_base=settings.public_asset_base_url,
                policy=policy,
                scenes=scenes,
            )
            files[f"imagery/{place.id}.json"] = json_bytes(pair.model_dump(mode="json"))
        rain_path = settings.data_dir / "imerg" / f"{place.id}.json"
        if rain_path.exists():
            files[f"imerg/{place.id}.json"] = rain_path.read_bytes()
    for name in GISTEMP_FILES:
        files[f"gistemp/{name}"] = (settings.raw_dir / "gistemp" / name).read_bytes()
    if any(name.startswith("imerg/") for name in files):
        for name in ["catalog.json", "extraction-manifest.json"]:
            path = settings.raw_dir / "imerg" / name
            if path.exists():
                files[f"imerg-source/{name}"] = path.read_bytes()
        for path in sorted((settings.raw_dir / "imerg" / "point-samples").glob("*.json")):
            files[f"imerg-source/point-samples/{path.name}"] = path.read_bytes()
    code_paths = sorted(Path(__file__).parent.glob("*.py")) + [ROOT / "services/api/climate/schemas.py"]
    code_hash = digest({path.name: sha256(path.read_bytes()) for path in code_paths if path.exists()})
    return Inputs(files, assets, policy, settings.public_asset_base_url, code_hash)


def directory_hashes(folder: Path, *, exclude=()) -> dict[str, str]:
    result = {}
    for path in sorted(folder.rglob("*")):
        if path.is_symlink():
            raise ValueError("Release directories cannot contain symbolic links")
        if path.is_file() and path.relative_to(folder).as_posix() not in exclude:
            result[path.relative_to(folder).as_posix()] = sha256(path.read_bytes())
    return result


@contextmanager
def publication_lock():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    with (settings.data_dir / ".publication.lock").open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
