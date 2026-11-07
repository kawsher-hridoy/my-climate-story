"""Image identity, processing and review checks shared by preparation and publication."""

import hashlib
import math
import re
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image
from pyproj import Transformer

PROCESSING_VERSION = "landsat-rgb-v1"
DISPLAY = {
    "reflectance_scale": 0.0000275,
    "reflectance_offset": -0.2,
    "display_min": 0.0,
    "display_max": 0.30,
    "gamma": 1.5,
    "note": "Fixed shared transform for every image. Display colors do not classify land cover.",
}
QA_POLICY = (
    "fill,dilated cloud,cloud,shadow,snow; L8/9 cirrus; RGB saturation; TM dropped pixels; water retained"
)
USGS_ITEMS = "https://landsatlook.usgs.gov/stac-server/collections/landsat-c2l2-sr/items/"


def processing_policy() -> dict:
    return {
        "version": PROCESSING_VERSION,
        "display_transform": dict(DISPLAY),
        "qa_policy": QA_POLICY,
        "pixel_size_m": 30,
        "aoi_side_m": 20_000,
        "minimum_valid_fraction": 0.95,
    }


def candidate_for(place_id: str, candidates: dict) -> dict | None:
    matches = [candidate for candidate in candidates.values() if place_id in candidate.get("places", [])]
    return matches[0] if len(matches) == 1 else None


def asset_path(url: str, place_id: str, assets_dir: Path, asset_base: str) -> Path:
    """Resolve only the exact owned asset URL shape, never a basename of an arbitrary URL."""
    prefix = f"{asset_base.rstrip('/')}/imagery/{place_id}/"
    if not url.startswith(prefix):
        raise ValueError("Image URL does not use the declared owned asset origin/path")
    filename = url[len(prefix) :]
    if not re.fullmatch(r"[A-Za-z0-9_-]+\.webp", filename) or urlsplit(url).query or urlsplit(url).fragment:
        raise ValueError("Invalid image asset filename")
    return assets_dir / "imagery" / place_id / filename


def expected_layout(place, crs: str, policy: dict) -> tuple[list[float], list[int], list[float]]:
    pixel = policy["pixel_size_m"]
    side = policy["aoi_side_m"]
    x, y = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform(
        place.coordinates.longitude, place.coordinates.latitude
    )
    size = math.ceil(side / pixel)
    left = math.floor((x - side / 2) / pixel) * pixel
    top = math.ceil((y + side / 2) / pixel) * pixel
    bounds = [left, top - size * pixel, left + size * pixel, top]
    inverse = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    corners = [
        inverse.transform(px, py)
        for px, py in [
            (bounds[0], bounds[1]),
            (bounds[0], bounds[3]),
            (bounds[2], bounds[1]),
            (bounds[2], bounds[3]),
        ]
    ]
    geographic = [
        min(px for px, _ in corners),
        min(py for _, py in corners),
        max(px for px, _ in corners),
        max(py for _, py in corners),
    ]
    return bounds, [size, size], geographic


def _numbers_equal(actual, expected, tolerance=1e-7) -> bool:
    return (
        isinstance(actual, (list, tuple))
        and len(actual) == len(expected)
        and all(
            isinstance(a, (int, float))
            and math.isfinite(a)
            and math.isclose(a, b, abs_tol=tolerance, rel_tol=0)
            for a, b in zip(actual, expected, strict=True)
        )
    )


def preparation_issues(
    pair,
    place,
    candidate,
    processing,
    *,
    assets_dir: Path,
    asset_base: str,
    policy: dict | None = None,
    scenes: dict | None = None,
) -> list[str]:
    """Check the cached output against current/pinned preparation inputs, including real files."""
    policy = policy or processing_policy()
    errors = []
    if pair.id != place.id:
        errors.append("pair place identity differs")
    if candidate is None:
        errors.append("place must have exactly one scene candidate pair")
    if pair.processing_version != policy["version"] or pair.resolution_m != policy["pixel_size_m"]:
        errors.append("processing version/resolution differs")
    if pair.before is None or pair.after is None:
        return errors + ["image pair is incomplete"]
    if not isinstance(processing, dict):
        return errors + ["processing evidence is missing"]
    if processing.get("place_id") != place.id:
        errors.append("processing place identity differs")
    if processing.get("display_transform") != policy["display_transform"]:
        errors.append("display transform changed")
    if processing.get("qa_policy") != policy["qa_policy"]:
        errors.append("QA policy changed")
    if processing.get("pixel_size_m") != policy["pixel_size_m"] or processing.get("crs") != pair.crs:
        errors.append("processing grid differs")
    try:
        bounds, shape, geographic = expected_layout(place, pair.crs, policy)
        if not _numbers_equal(processing.get("bounds_projected"), bounds):
            errors.append("crop no longer matches the requested place")
        if processing.get("shape") != shape or not _numbers_equal(pair.bounds, geographic):
            errors.append("crop shape/geographic bounds differ")
    except (ValueError, TypeError, RuntimeError):
        errors.append("invalid projected crop")
        shape = [0, 0]
    for label, asset in [("before", pair.before), ("after", pair.after)]:
        if candidate is not None and asset.product_id != candidate.get(label):
            errors.append(f"{label} scene candidate changed")
        recorded = processing.get(label, {})
        if recorded != asset.model_dump(mode="json"):
            errors.append(f"{label} asset differs from its processing evidence")
        if asset.source_url != USGS_ITEMS + asset.product_id:
            errors.append(f"{label} source URL differs")
        expected_date = asset.product_id.split("_")[3] if len(asset.product_id.split("_")) >= 4 else ""
        if asset.date.replace("-", "") != expected_date:
            errors.append(f"{label} acquisition date differs from product ID")
        if (
            not math.isfinite(asset.valid_pixel_fraction)
            or not policy["minimum_valid_fraction"] <= asset.valid_pixel_fraction <= 1
        ):
            errors.append(f"{label} valid-pixel threshold failed")
        if not math.isfinite(asset.scene_cloud_percent) or not 0 <= asset.scene_cloud_percent <= 100:
            errors.append(f"{label} cloud metadata invalid")
        if [asset.height, asset.width] != shape:
            errors.append(f"{label} dimensions differ from the shared grid")
        if scenes is not None:
            source = scenes.get(asset.product_id)
            if source is None or source.get("id") != asset.product_id:
                errors.append(f"{label} official scene metadata missing")
            elif source.get("properties", {}).get("datetime", "")[:10] != asset.date:
                errors.append(f"{label} official acquisition date differs")
        try:
            path = asset_path(asset.url, place.id, assets_dir, asset_base)
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != asset.sha256 or len(raw) != asset.bytes:
                errors.append(f"{label} image checksum/size differs")
            with Image.open(path) as image:
                if image.format != "WEBP" or image.size != (asset.width, asset.height):
                    errors.append(f"{label} image format/dimensions differ")
                image.verify()
            thumb = asset_path(asset.thumbnail_url, place.id, assets_dir, asset_base)
            with Image.open(thumb) as image:
                if (
                    image.format != "WEBP"
                    or min(image.size) < 1
                    or max(image.size) > max(asset.width, asset.height)
                ):
                    errors.append(f"{label} thumbnail invalid")
                image.verify()
        except (OSError, ValueError):
            errors.append(f"{label} owned image/thumbnail is missing or invalid")
    return errors


def approval_issues(pair, review: dict | None) -> list[str]:
    if not isinstance(review, dict) or not review:
        return ["canonical imagery review is missing"]
    if review.get("status", "approved") != "approved":
        return ["canonical imagery review was withdrawn"]
    errors = []
    if not review.get("reviewer") or not review.get("evidence") or not review.get("reviewed_at"):
        errors.append("imagery review evidence is incomplete")
    if pair.before is None or review.get("before_sha256") != pair.before.sha256:
        errors.append("historical image review checksum differs")
    if pair.after is None or review.get("after_sha256") != pair.after.sha256:
        errors.append("recent image review checksum differs")
    if review.get("processing_version") != pair.processing_version:
        errors.append("review processing version differs")
    return errors


def reconcile_pair(
    pair,
    place,
    candidate,
    processing,
    review,
    *,
    assets_dir: Path,
    asset_base: str,
    policy: dict | None = None,
    scenes: dict | None = None,
):
    """Return a reconciled copy. Reading a cache never grants authority to its embedded review."""
    resolved = pair.model_copy(deep=True)
    preparation = preparation_issues(
        resolved,
        place,
        candidate,
        processing,
        assets_dir=assets_dir,
        asset_base=asset_base,
        policy=policy,
        scenes=scenes,
    )
    approvals = approval_issues(resolved, review)
    if preparation or approvals:
        resolved.status = "needs_review"
        resolved.review = None
        resolved.error = "; ".join(preparation + approvals)
    else:
        resolved.status = "approved"
        resolved.review = dict(review)
        resolved.error = None
    return resolved, preparation, approvals
