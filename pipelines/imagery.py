"""Retrieve real Landsat windows; preserve geometry, QA, and review evidence."""

import hashlib
import math
import time
from functools import lru_cache
from pathlib import Path

import httpx
import numpy as np
import rasterio
from climate.config import settings
from climate.files import read_json, write_json
from climate.schemas import ImageryAsset, ImageryPair, Localized
from PIL import Image
from pyproj import Transformer
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from rasterio.windows import from_bounds
from shapely.geometry import box, shape
from shapely.ops import transform as transform_geometry

from .build import places, utc_timestamp
from .imagery_policy import (
    DISPLAY,
    QA_POLICY,
    candidate_for,
    preparation_issues,
    reconcile_pair,
)
from .release_io import publication_lock

USGS = "https://landsatlook.usgs.gov/stac-server/collections/landsat-c2l2-sr/items/"
PC = "https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2/items/"
SIGN = "https://planetarycomputer.microsoft.com/api/sas/v1/sign"


def fetch_json(client: httpx.Client, url: str, params=None) -> dict:
    for attempt in range(4):
        try:
            response = client.get(url, params=params)
            if (response.status_code == 429 or response.status_code >= 500) and attempt < 3:
                wait = response.headers.get("Retry-After", "")
                time.sleep(min(int(wait), 30) if wait.isdigit() else 2 ** (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError("Imagery metadata request did not complete")


def pc_id(usgs_id: str) -> str:
    parts = usgs_id.split("_")
    return "_".join(parts[:4] + parts[5:7])


@lru_cache(maxsize=40)
def scene(usgs_id: str) -> tuple[dict, dict]:
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        usgs_path = settings.raw_dir / "imagery-metadata" / f"{usgs_id}.json"
        if usgs_path.exists():
            official = read_json(usgs_path)
        else:
            official = fetch_json(client, USGS + usgs_id)
            write_json(usgs_path, official)
        mirror = fetch_json(client, PC + pc_id(usgs_id))
        if official["properties"]["datetime"][:10] != mirror["properties"]["datetime"][:10]:
            raise ValueError("Official and mirror acquisition dates differ")
        return official, mirror


@lru_cache(maxsize=100)
def signed_href(href: str) -> str:
    if not href.startswith("https://") or ".blob.core.windows.net/" not in href:
        raise ValueError("Unexpected Landsat asset host")
    with httpx.Client(timeout=60) as client:
        signed = fetch_json(client, SIGN, {"href": href})["href"]
        if not signed.startswith(href + "?"):
            raise ValueError("Invalid signed asset response")
        return signed


def sensor_mask(qa: np.ndarray, saturation: np.ndarray, landsat8: bool) -> np.ndarray:
    bad_bits = [0, 1, 3, 4, 5] + ([2] if landsat8 else [])
    bad = np.zeros(qa.shape, dtype=bool)
    for bit in bad_bits:
        bad |= (qa & (1 << bit)) != 0
    for bit in [1, 2, 3] if landsat8 else [0, 1, 2]:
        bad |= (saturation & (1 << bit)) != 0
    if not landsat8:
        bad |= (saturation & (1 << 9)) != 0
    return ~bad


def read_window(
    item: dict,
    asset_name: str,
    bounds: tuple,
    target_crs: str,
    target_transform,
    size: int,
    categorical=False,
) -> np.ndarray:
    asset = item["assets"].get(asset_name)
    if asset is None:
        raise ValueError(f"Missing Landsat asset {asset_name}")
    url = signed_href(asset["href"])
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        GDAL_HTTP_TIMEOUT="60",
        GDAL_HTTP_MAX_RETRY="3",
        GDAL_HTTP_RETRY_DELAY="2",
        VSI_CACHE="TRUE",
        VSI_CACHE_SIZE=32_000_000,
        GDAL_CACHEMAX=128,
    ):
        with rasterio.open(url) as dataset:
            inverse = Transformer.from_crs(target_crs, dataset.crs, always_xy=True)
            corners = [inverse.transform(bounds[0], bounds[1]), inverse.transform(bounds[2], bounds[3])]
            window = (
                from_bounds(corners[0][0], corners[0][1], corners[1][0], corners[1][1], dataset.transform)
                .round_offsets()
                .round_lengths()
            )
            source = dataset.read(1, window=window, boundless=True, fill_value=0)
            destination = np.zeros((size, size), dtype=np.uint16 if categorical else np.float32)
            reproject(
                source=source,
                destination=destination,
                src_transform=dataset.window_transform(window),
                src_crs=dataset.crs,
                dst_transform=target_transform,
                dst_crs=target_crs,
                src_nodata=0,
                dst_nodata=0,
                resampling=Resampling.nearest if categorical else Resampling.bilinear,
            )
            return destination


def render_asset(
    place, usgs_id: str, target_crs: str, bounds: tuple, grid, size: int, label: str
) -> ImageryAsset:
    official, item = scene(usgs_id)
    footprint = transform_geometry(
        Transformer.from_crs("EPSG:4326", target_crs, always_xy=True).transform, shape(item["geometry"])
    )
    if not footprint.covers(box(*bounds)):
        raise ValueError(f"Scene does not contain complete {place.id} AOI")
    qa = read_window(item, "qa_pixel", bounds, target_crs, grid, size, categorical=True)
    saturation = read_window(item, "qa_radsat", bounds, target_crs, grid, size, categorical=True)
    bands = [read_window(item, name, bounds, target_crs, grid, size) for name in ["red", "green", "blue"]]
    landsat8 = usgs_id.startswith(("LC08", "LC09"))
    valid = sensor_mask(qa, saturation, landsat8) & np.all(np.stack(bands) != 0, axis=0)
    fraction = float(np.mean(valid))
    if fraction < 0.95:
        raise ValueError(f"Insufficient valid pixels for {place.id}: {fraction:.1%}")
    reflectance = np.stack(bands, axis=-1) * DISPLAY["reflectance_scale"] + DISPLAY["reflectance_offset"]
    display = np.clip(
        (reflectance - DISPLAY["display_min"]) / (DISPLAY["display_max"] - DISPLAY["display_min"]), 0, 1
    )
    display = np.power(display, 1 / DISPLAY["gamma"])
    rgb = (display * 255).astype(np.uint8)
    rgb[~valid] = (238, 235, 224)
    image = Image.fromarray(rgb)
    directory = settings.data_dir / "assets" / "imagery" / place.id
    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / f"{label}.webp"
    image.save(temporary, "WEBP", quality=86, method=6)
    checksum = hashlib.sha256(temporary.read_bytes()).hexdigest()
    filename = f"{label}-{checksum[:12]}.webp"
    destination = directory / filename
    temporary.replace(destination)
    thumbnail = image.copy()
    thumbnail.thumbnail((384, 384))
    thumbnail_name = f"{label}-{checksum[:12]}-thumb.webp"
    thumbnail.save(directory / thumbnail_name, "WEBP", quality=80, method=6)
    date = item["properties"]["datetime"][:10]
    return ImageryAsset(
        url=f"{settings.public_asset_base_url}/imagery/{place.id}/{filename}",
        thumbnail_url=f"{settings.public_asset_base_url}/imagery/{place.id}/{thumbnail_name}",
        date=date,
        sensor="Landsat 8 OLI" if landsat8 else "Landsat 5 TM",
        product_id=usgs_id,
        source_url=USGS + usgs_id,
        sha256=checksum,
        width=size,
        height=size,
        bytes=destination.stat().st_size,
        valid_pixel_fraction=fraction,
        scene_cloud_percent=float(
            official["properties"].get("eo:cloud_cover", item["properties"].get("eo:cloud_cover", 0))
        ),
        alt=Localized(
            en=f"True-color Landsat view of the approximately 20 km area around {place.name.en}, acquired {date}.",
            bn=f"{place.name.bn}-এর আশপাশের প্রায় ২০ কিমি এলাকার সত্য রঙের ল্যান্ডস্যাট ছবি, তারিখ {date}।",
        ),
    )


def prepare_place(place_id: str) -> dict:
    place = next(p for p in places() if p.id == place_id)
    candidates = read_json(settings.content_dir / "imagery-candidates.json")
    candidate = next(v for v in candidates.values() if place_id in v["places"])
    _, old = scene(candidate["before"])
    epsg = old["properties"].get("proj:epsg") or old["assets"]["red"].get("proj:epsg")
    if epsg is None:
        zone = int((place.coordinates.longitude + 180) / 6) + 1
        epsg = 32600 + zone
    target_crs = f"EPSG:{epsg}"
    x, y = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True).transform(
        place.coordinates.longitude, place.coordinates.latitude
    )
    size = math.ceil(20_000 / 30)
    left = math.floor((x - 10_000) / 30) * 30
    top = math.ceil((y + 10_000) / 30) * 30
    bounds = (left, top - size * 30, left + size * 30, top)
    grid = from_origin(left, top, 30, 30)
    before = render_asset(place, candidate["before"], target_crs, bounds, grid, size, "before")
    after = render_asset(place, candidate["after"], target_crs, bounds, grid, size, "after")
    inverse = Transformer.from_crs(target_crs, "EPSG:4326", always_xy=True)
    corners = [
        inverse.transform(x, y)
        for x, y in [
            (bounds[0], bounds[1]),
            (bounds[0], bounds[3]),
            (bounds[2], bounds[1]),
            (bounds[2], bounds[3]),
        ]
    ]
    geographic = [
        min(x for x, y in corners),
        min(y for x, y in corners),
        max(x for x, y in corners),
        max(y for x, y in corners),
    ]
    pair = ImageryPair(
        id=place.id,
        status="needs_review",
        before=before,
        after=after,
        crs=target_crs,
        bounds=geographic,
        caption=Localized(
            en="Compare land, water, and built shapes in the same area. Colors also vary with sensors, season, and atmospheric haze; pale patches are masked pixels. These views do not establish a single cause.",
            bn="একই এলাকার জমি, পানি আর নির্মিত অংশের আকৃতি তুলনা করো। সেন্সর, ঋতু আর বায়ুমণ্ডলের কুয়াশায় রং বদলাতে পারে; ফ্যাকাশে অংশে পিক্সেল বাদ দেওয়া হয়েছে। এই দৃশ্য একটিমাত্র কারণ প্রমাণ করে না।",
        ),
    )
    processing = {
        "place_id": place.id,
        "retrieved_at": utc_timestamp(),
        "display_transform": DISPLAY,
        "bounds_projected": bounds,
        "crs": target_crs,
        "pixel_size_m": 30,
        "shape": [size, size],
        "qa_policy": QA_POLICY,
        "before": before.model_dump(mode="json"),
        "after": after.model_dump(mode="json"),
    }
    review_path = settings.content_dir / "imagery-reviews.json"
    review = read_json(review_path).get(place_id) if review_path.exists() else None
    scene_records = {asset.product_id: scene(asset.product_id)[0] for asset in [before, after]}
    pair, errors, _ = reconcile_pair(
        pair,
        place,
        candidate,
        processing,
        review,
        assets_dir=settings.data_dir / "assets",
        asset_base=settings.public_asset_base_url,
        scenes=scene_records,
    )
    if errors:
        raise ValueError("Prepared imagery failed integrity checks: " + "; ".join(errors))
    write_json(settings.raw_dir / "imagery-metadata" / f"processing-{place.id}.json", processing)
    write_json(settings.data_dir / "imagery" / f"{place.id}.json", pair.model_dump(mode="json"))
    return {
        "place": place.id,
        "status": pair.status,
        "before_valid": before.valid_pixel_fraction,
        "after_valid": after.valid_pixel_fraction,
    }


def prepare_all(selected: list[str] | None = None) -> list[dict]:
    results = []
    candidates = read_json(settings.content_dir / "imagery-candidates.json")
    review_path = settings.content_dir / "imagery-reviews.json"
    reviews = read_json(review_path) if review_path.exists() else {}
    for place in places():
        if selected and place.id not in selected:
            continue
        path = settings.data_dir / "imagery" / f"{place.id}.json"
        try:
            preparation = ["no cached pair"]
            if path.exists():
                pair = ImageryPair.model_validate(read_json(path))
                processing_path = settings.raw_dir / "imagery-metadata" / f"processing-{place.id}.json"
                processing = read_json(processing_path) if processing_path.exists() else None
                scenes = {}
                for asset in [pair.before, pair.after]:
                    if asset:
                        source = settings.raw_dir / "imagery-metadata" / f"{asset.product_id}.json"
                        if source.exists():
                            scenes[asset.product_id] = read_json(source)
                pair, preparation, _ = reconcile_pair(
                    pair,
                    place,
                    candidate_for(place.id, candidates),
                    processing,
                    reviews.get(place.id),
                    assets_dir=settings.data_dir / "assets",
                    asset_base=settings.public_asset_base_url,
                    scenes=scenes,
                )
                write_json(path, pair.model_dump(mode="json"))
            if preparation:
                result = prepare_place(place.id)
            else:
                result = {"place": place.id, "status": pair.status, "cached": True}
        except Exception as error:
            # Never log a raster exception's signed URL or SAS query.
            result = {"place": place.id, "status": "failed", "error_type": type(error).__name__}
            if isinstance(error, httpx.HTTPStatusError):
                result["http_status"] = error.response.status_code
                result["stage_host"] = error.request.url.host
            elif isinstance(error, ValueError):
                result["reason"] = str(error)
        print(result, flush=True)
        results.append(result)
    return results


def review_pair(place_id: str, reviewer: str, note: str) -> dict:
    if len(note.strip()) < 30 or not reviewer.strip():
        raise ValueError("Substantive visual-review evidence is required")
    path = settings.data_dir / "imagery" / f"{place_id}.json"
    pair = ImageryPair.model_validate(read_json(path))
    place = next(place for place in places() if place.id == place_id)
    processing_path = settings.raw_dir / "imagery-metadata" / f"processing-{place_id}.json"
    processing = read_json(processing_path) if processing_path.exists() else None
    scenes = {}
    for asset in [pair.before, pair.after]:
        if asset:
            source = settings.raw_dir / "imagery-metadata" / f"{asset.product_id}.json"
            if source.exists():
                scenes[asset.product_id] = read_json(source)
    errors = preparation_issues(
        pair,
        place,
        candidate_for(place_id, read_json(settings.content_dir / "imagery-candidates.json")),
        processing,
        assets_dir=settings.data_dir / "assets",
        asset_base=settings.public_asset_base_url,
        scenes=scenes,
    )
    if errors:
        raise ValueError("Cannot approve stale or invalid imagery: " + "; ".join(errors))
    if pair.before is None or pair.after is None:
        raise ValueError("Cannot approve missing imagery")
    if min(pair.before.valid_pixel_fraction, pair.after.valid_pixel_fraction) < 0.95:
        raise ValueError("Cannot approve insufficient coverage")
    for asset in [pair.before, pair.after]:
        source = settings.data_dir / "assets" / "imagery" / place_id / Path(asset.url).name
        if hashlib.sha256(source.read_bytes()).hexdigest() != asset.sha256:
            raise ValueError("Image checksum changed")
    pair.status = "approved"
    pair.review = {
        "reviewer": reviewer,
        "reviewed_at": utc_timestamp(),
        "evidence": note,
        "before_sha256": pair.before.sha256,
        "after_sha256": pair.after.sha256,
        "processing_version": pair.processing_version,
    }
    pair.caption = Localized(
        en="Compare land, water, and built shapes in the same area. Colors also vary with sensors, season, and atmospheric haze; pale patches are masked pixels. These views do not establish a single cause.",
        bn="একই এলাকার জমি, পানি আর নির্মিত অংশের আকৃতি তুলনা করো। সেন্সর, ঋতু আর বায়ুমণ্ডলের কুয়াশায় রং বদলাতে পারে; ফ্যাকাশে অংশে পিক্সেল বাদ দেওয়া হয়েছে। এই দৃশ্য একটিমাত্র কারণ প্রমাণ করে না।",
    )
    review_path = settings.content_dir / "imagery-reviews.json"
    with publication_lock():
        records = read_json(review_path) if review_path.exists() else {}
        records[place_id] = pair.review
        write_json(review_path, records)
        write_json(path, pair.model_dump(mode="json"))
    return {"place": place_id, "status": "approved"}
