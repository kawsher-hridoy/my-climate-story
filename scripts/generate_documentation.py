"""Refresh public documentation from the active release and actual model definitions."""

import hashlib
import json

from climate.config import ROOT
from climate.db import Base
from climate.files import active_release, read_json
from climate.jobs import app as queue_app
from climate.schemas import ExplorationRequest, StoryManifest
from sqlalchemy.dialects import postgresql


def markdown(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def column_default(column):
    values = []
    if column.default is not None:
        value = column.default.arg
        default = value.__name__ + "()" if callable(value) else json.dumps(value, ensure_ascii=False)
        values.append("Python: " + default)
    if column.server_default is not None:
        values.append("SQL: " + str(column.server_default.arg))
    return "; ".join(values) or "—"


def main():
    release_id, folder = active_release()
    manifest = read_json(folder / "release.json")
    output = ROOT / "docs" / "generated"
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for place_id in manifest["place_ids"]:
        story = read_json(folder / "stories" / f"{place_id}.json")
        StoryManifest.model_validate(story)
        source = next(row for row in manifest["source_requests"] if row["place_id"] == place_id)
        pinned = folder / "inputs" / "power" / f"{place_id}.json"
        if not pinned.exists():
            raise ValueError("Rebuild as release format 2 before generating the data register")
        raw = read_json(pinned)
        assert hashlib.sha256(pinned.read_bytes()).hexdigest() == source["sha256"]
        for key in ["temperature", "rainfall"]:
            component = story[key]
            assert read_json(folder / "series" / f"{component['series_id']}.json") == component
        images = {}
        for key in ["before", "after"]:
            asset = story["imagery"].get(key)
            images[key] = asset
        entries.append(
            {
                "place": story["place"],
                "story_file": str((folder / "stories" / f"{place_id}.json").relative_to(ROOT)),
                "source_file": f"data/raw/power/{place_id}.json",
                "pinned_source_file": str(pinned.relative_to(ROOT)),
                "source_request": source,
                "power_variables": {
                    name: {
                        "unit": raw["parameters"][name]["units"],
                        "numeric_values": len(values),
                    }
                    for name, values in raw["properties"]["parameter"].items()
                },
                "temperature": {
                    key: story["temperature"][key]
                    for key in ["series_id", "publication_state", "comparison", "shared_series_with"]
                },
                "temperature_annual_count": len(story["temperature"]["annual"]),
                "temperature_monthly_count": len(story["temperature"]["monthly"]),
                "rainfall_series_id": story["rainfall"]["series_id"],
                "rainfall_state": story["rainfall"]["publication_state"],
                "rainfall_annual_count": len(story["rainfall"]["annual"]),
                "rainfall_monthly_count": len(story["rainfall"]["monthly"]),
                "global_annual_count": len(story["global_context"]["annual"]),
                "global_period": [
                    story["global_context"]["annual"][0]["year"],
                    story["global_context"]["annual"][-1]["year"],
                ],
                "imagery_status": story["imagery"]["status"],
                "imagery_review": story["imagery"]["review"],
                "images": images,
                "quiz_ids": [row["id"] for row in story["quiz"]],
                "action_ids": [row["id"] for row in story["actions"]],
            }
        )
    write_json(
        output / "data-register.json",
        {
            "release_id": release_id,
            "release_format": manifest["release_format"],
            "release_created_at": manifest["created_at"],
            "rainfall_pending": manifest["rainfall_pending"],
            "places": entries,
        },
    )
    lines = [
        "# Active release: per-location data register",
        "",
        "Generated with `uv run python scripts/generate_documentation.py`.",
        "",
        f"Release: `{release_id}`; format {manifest['release_format']}. This is a versioned snapshot.",
        "",
        "The [JSON register](data-register.json) includes full source URLs/hashes, image IDs/hashes, "
        "review records, quiz IDs, action IDs and the exact file paths for every place.",
        "",
        "## Coverage",
        "",
        "| Place | Selected coordinate | Temperature months / years | Rainfall months / years | "
        "Historical / recent image |",
        "|---|---|---|---|---|",
    ]
    for row in entries:
        place = row["place"]
        coords = place["coordinates"]
        images = row["images"]
        dates = " / ".join(asset["date"] if asset else "pending" for asset in images.values())
        lines.append(
            f"| {place['name']['en']} / {place['name']['bn']} | "
            f"{coords['latitude']}, {coords['longitude']} | "
            f"{row['temperature_monthly_count']} / {row['temperature_annual_count']} | "
            f"{row['rainfall_monthly_count']} / {row['rainfall_annual_count']} | {dates} |"
        )
    lines += ["", "## Exact resources", ""]
    for row in entries:
        place_id = row["place"]["id"]
        temp = row["temperature"]
        comparison = temp["comparison"]
        lines += [
            f"### {row['place']['name']['en']} (`{place_id}`)",
            "",
            f"- Story: `GET /api/v1/stories/{place_id}?release={release_id}`.",
            f"- POWER input: `{row['source_file']}`; pinned evidence: `{row['pinned_source_file']}`.",
            f"- Source SHA-256: `{row['source_request']['sha256']}`.",
            f"- Temperature series: `{temp['series_id']}`; state: `{temp['publication_state']}`.",
            f"- Rainfall series: `{row['rainfall_series_id']}`; state: `{row['rainfall_state']}`.",
            f"- Shared-value annotations: {', '.join(temp['shared_series_with']) or 'none'}.",
        ]
        if comparison:
            lines.append(
                f"- Temperature review: `{comparison['review_id']}`; windows "
                f"{comparison['baseline_period']} and {comparison['recent_period']}.")
        for key, asset in row["images"].items():
            if asset:
                lines += [
                    f"- {key.capitalize()} image: `{asset['product_id']}`; "
                    f"{asset['date']}; {asset['width']} × {asset['height']}; "
                    f"valid coverage {asset['valid_pixel_fraction']:.4%}.",
                    f"  Asset `{asset['url']}`; SHA-256 `{asset['sha256']}`.",
                ]
        lines += [
            f"- Quiz: {', '.join('`' + key + '`' for key in row['quiz_ids'])}.",
            f"- Actions: {', '.join('`' + key + '`' for key in row['action_ids'])}.",
            "",
        ]
    (output / "place-data-register.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    schema_lines = [
        "# Application database schema",
        "",
        "Generated from `services/api/climate/db.py`. Procrastinate manages its separate queue tables.",
        "",
        "Relationships between IDs are application-managed; these models do not declare SQL foreign keys. "
        "JSON stores manifests/evidence. Migration-added PostGIS/trigram indexes are documented separately.",
        "",
    ]
    for table in Base.metadata.sorted_tables:
        schema_lines += [
            f"## `{table.name}`", "",
            "| Column | PostgreSQL type | Nullable | Primary key | Default |",
            "|---|---|---|---|---|",
        ]
        for column in table.columns:
            schema_lines.append(
                f"| `{column.name}` | `{markdown(column.type.compile(dialect=postgresql.dialect()))}` | "
                f"{'yes' if column.nullable else 'no'} | {'yes' if column.primary_key else 'no'} | "
                f"{markdown(column_default(column))} |"
            )
        schema_lines += ["", "Declared indexes/constraints:", ""]
        for index in sorted(table.indexes, key=lambda item: item.name):
            fields = ", ".join(str(column.name) for column in index.columns)
            predicate = index.dialect_options["postgresql"].get("where")
            schema_lines.append(
                f"- `{index.name}` ({fields})"
                + ("; unique" if index.unique else "")
                + (f"; partial predicate `{predicate}`" if predicate is not None else "")
                + "."
            )
        if not table.indexes and not any(
            item.__class__.__name__ == "UniqueConstraint" for item in table.constraints
        ):
            schema_lines.append("- No additional declared indexes/unique constraints beyond the primary key.")
        for constraint in table.constraints:
            if constraint.__class__.__name__ == "UniqueConstraint":
                schema_lines.append("- Unique: " + ", ".join(column.name for column in constraint.columns) + ".")
        schema_lines.append("")
    (output / "database-schema.md").write_text("\n".join(schema_lines), encoding="utf-8")
    write_json(output / "story-json-schema.json", StoryManifest.model_json_schema())
    write_json(output / "exploration-json-schema.json", ExplorationRequest.model_json_schema())
    (output / "queue-schema.sql").write_text(queue_app.schema_manager.get_schema(), encoding="utf-8")
    print(json.dumps({"release_id": release_id, "places": len(entries), "outputs": str(output.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
