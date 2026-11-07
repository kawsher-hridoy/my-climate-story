import csv
import io
import json
import shutil
import zipfile

import pytest
from climate.config import ROOT, settings
from climate.files import read_json
from climate.schemas import StoryManifest

from pipelines import build
from pipelines.imerg import extract_grid


@pytest.fixture
def isolated_release(tmp_path, monkeypatch):
    shutil.copy(ROOT / "climate_data.zip", tmp_path / "climate_data.zip")
    content = tmp_path / "content"
    content.mkdir()
    for filename in ["places.json", "question-bank.json", "actions.json", "imagery-candidates.json"]:
        shutil.copy(settings.content_dir / filename, content / filename)
    monkeypatch.setattr(build, "ROOT", tmp_path)
    monkeypatch.setattr(settings, "content_dir", content)
    monkeypatch.setattr(settings, "raw_dir", tmp_path / "raw")
    monkeypatch.setattr(settings, "data_dir", tmp_path / "processed")
    build.import_archive()
    result = build.build_release(activate=False)
    return tmp_path, settings.data_dir / "releases" / result["id"]


def test_bundles_have_real_records_and_pending_rain_without_invented_values(isolated_release):
    _, folder = isolated_release
    for raw_place in read_json(folder / "places.json"):
        story = StoryManifest.model_validate(read_json(folder / "stories" / f"{raw_place['id']}.json"))
        assert len(story.temperature.monthly) == 540
        assert len(story.temperature.annual) == 45
        assert story.temperature.comparison is None
        assert story.temperature.publication_state == "descriptive_only"
        assert story.rainfall.publication_state == "unavailable"
        assert not story.rainfall.annual and not story.rainfall.monthly
        assert story.global_context.baseline == "1951–1980"
        assert len(story.global_context.annual) == 146
        assert len(story.quiz) == 5 and len(story.actions) >= 3


def test_release_identity_is_reproducible(isolated_release):
    _, folder = isolated_release
    before = (folder / "stories/dhaka.json").read_bytes()
    result = build.build_release(activate=False)
    assert result["id"] == folder.name
    assert before == (folder / "stories/dhaka.json").read_bytes()


def test_comparison_needs_matching_data_review(isolated_release):
    build.review_temperature(
        "Test reviewer",
        "Calendar aggregation and complete comparison windows independently checked; descriptive arithmetic only.",
    )
    release = build.build_release(activate=False)
    story = read_json(settings.data_dir / "releases" / release["id"] / "stories/dhaka.json")
    assert story["temperature"]["comparison"]["publication_state"] == "comparison_approved"
    reviews = read_json(settings.content_dir / "temperature-reviews.json")
    reviews["dhaka"]["data_hash"] = "stale-source"
    (settings.content_dir / "temperature-reviews.json").write_text(json.dumps(reviews))
    release = build.build_release(activate=False)
    story = read_json(settings.data_dir / "releases" / release["id"] / "stories/dhaka.json")
    assert story["temperature"]["comparison"] is None


def test_gistemp_clean_values_match_supplied_original():
    with zipfile.ZipFile(ROOT / "climate_data.zip") as archive:
        raw = archive.read("climate_data/global_gistemp/Global_Temperature_Data_GISTEMP.csv").decode(
            "utf-8-sig"
        )
        lines = raw.splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith("Year,"))
        original = {int(row["Year"]): row for row in csv.DictReader(io.StringIO("\n".join(lines[start:])))}
        clean = csv.DictReader(
            io.StringIO(
                archive.read("climate_data/global_gistemp/Global_Temperature_Annual_Clean.csv").decode(
                    "utf-8-sig"
                )
            )
        )
        for row in clean:
            assert float(row["temperature_anomaly_c"]) == float(original[int(row["year"])]["J-D"])


def test_imerg_hdf5_dimension_order_units_and_missing(tmp_path):
    import numpy as np
    import xarray as xr
    from climate.schemas import Place

    location = Place.model_validate(read_json(settings.content_dir / "places.json")[0])
    location.coordinates.latitude = 24.05
    location.coordinates.longitude = 90.45
    ds = xr.Dataset(
        {"precipitation": (("time", "lon", "lat"), np.array([[[1.0, -9999.9], [2.0, 3.0]]]))},
        coords={
            "time": np.array(["2024-02-01"], dtype="datetime64[ns]"),
            "lon": [90.45, 90.55],
            "lat": [24.05, 24.15],
        },
    )
    ds.precipitation.attrs["units"] = "mm/hr"
    target = tmp_path / "sample.h5"
    ds.to_netcdf(target, group="Grid", engine="h5netcdf")
    records = extract_grid(target, [location])
    assert records[0]["value"] == 696
    location.coordinates.latitude = 24.15
    assert extract_grid(target, [location])[0]["value"] is None
