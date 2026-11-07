"""Create app icons and an actual Natural Earth overview, without AI imagery."""

import json
from pathlib import Path

import httpx
from PIL import Image, ImageDraw
from shapely.geometry import mapping, shape

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "apps/web/public"
SOURCE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"


def main():
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for size in [192, 512]:
        image = Image.new("RGB", (size, size), "#173f35")
        draw = ImageDraw.Draw(image)
        scale = size / 64
        draw.ellipse([18 * scale, 16 * scale, 48 * scale, 46 * scale], fill="#c2d79b")
        draw.polygon(
            [
                (18 * scale, 45 * scale),
                (18 * scale, 29 * scale),
                (30 * scale, 17 * scale),
                (47 * scale, 16 * scale),
                (47 * scale, 32 * scale),
                (34 * scale, 45 * scale),
            ],
            fill="#c2d79b",
        )
        draw.line([(20 * scale, 45 * scale), (39 * scale, 25 * scale)], fill="#173f35", width=int(3 * scale))
        draw.arc(
            [32 * scale, 40 * scale, 54 * scale, 59 * scale], 180, 300, fill="#8abdc5", width=int(3 * scale)
        )
        image.save(PUBLIC / f"icon-{size}.png")
    target = ROOT / "data/raw/maps/natural-earth-countries.geojson"
    if not target.exists():
        response = httpx.get(SOURCE, timeout=60)
        response.raise_for_status()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
    original = json.loads(target.read_text())
    features = []
    paths = []
    for feature in original["features"]:
        simplified = shape(feature["geometry"]).simplify(0.25, preserve_topology=True)
        geometry = mapping(simplified)
        features.append(
            {
                "type": "Feature",
                "properties": {"name": feature["properties"].get("ADMIN", "")},
                "geometry": geometry,
            }
        )
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        for polygon in polygons:
            for ring in polygon[:1]:
                points = [((lon + 180) * 2, (90 - lat) * 2) for lon, lat, *_ in ring]
                if points:
                    command = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in points) + "Z"
                    paths.append(f'<path d="{command}"/>')
    (PUBLIC / "offline-world.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":"))
    )
    (PUBLIC / "world-overview.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 360" role="img"><title>World overview, Natural Earth</title><rect width="720" height="360" rx="12" fill="#e9f0e7"/><g fill="#b0c59e" stroke="#e9f0e7" stroke-width=".6">'
        + "".join(paths)
        + '</g><circle cx="540.8" cy="132.4" r="4" fill="#315d42"/></svg>'
    )
    print("Created PWA icons and Natural Earth overview.")


if __name__ == "__main__":
    main()
