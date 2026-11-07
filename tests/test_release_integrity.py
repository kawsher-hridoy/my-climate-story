"""Regression tests use isolated copies of the shipped public snapshot, never live outputs."""

import json
import shutil
import tarfile
from pathlib import Path

import pytest
from climate.config import ROOT, settings
from climate.files import read_json, write_json

from pipelines import build, imagery, storage, validation
from pipelines.imagery_policy import DISPLAY
from pipelines.release_io import directory_hashes


@pytest.fixture
def ready_workspace(tmp_path, monkeypatch):
    source_content = settings.content_dir
    monkeypatch.setattr(build, "ROOT", tmp_path)
    monkeypatch.setattr(validation, "ROOT", tmp_path)
    monkeypatch.setattr(settings, "content_dir", tmp_path / "content")
    monkeypatch.setattr(settings, "data_dir", tmp_path / "processed")
    monkeypatch.setattr(settings, "raw_dir", tmp_path / "raw")
    monkeypatch.setattr(settings, "public_asset_base_url", "/media")
    shutil.copytree(source_content, settings.content_dir)
    prefixes = (
        "raw/archive-inventory.json",
        "raw/power/",
        "raw/gistemp/",
        "raw/imagery-metadata/",
        "processed/assets/",
        "processed/imagery/",
    )
    with tarfile.open(ROOT / "data/bootstrap-release.tar.gz", "r|gz") as archive:
        for member in archive:
            if member.isfile() and any(
                member.name == prefix or member.name.startswith(prefix) for prefix in prefixes
            ):
                target = tmp_path / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as handle:
                    target.write_bytes(handle.read())
    result = build.build_release()
    folder = settings.data_dir / "releases" / result["id"]
    return folder


def _refresh_output_hashes(folder: Path):
    """Adversarially update the hash catalog too, exercising independent numeric validation."""
    manifest = read_json(folder / "release.json")
    manifest["output_sha256"] = {
        name: checksum
        for name, checksum in directory_hashes(folder, exclude=("release.json",)).items()
        if not name.startswith("inputs/")
    }
    write_json(folder / "release.json", manifest)


def test_new_release_is_valid_and_has_unique_place_components(ready_workspace):
    folder = ready_workspace
    result = validation.validate_release(folder=folder, write_report=False)
    assert result["passed"] and result["ready"]
    assert result["reviewed_images"] == 24
    barishal = read_json(folder / "stories/barishal.json")["temperature"]
    bhola = read_json(folder / "stories/bhola.json")["temperature"]
    assert barishal["monthly"] == bhola["monthly"]
    assert barishal["series_id"] != bhola["series_id"]
    for component in [barishal, bhola]:
        assert read_json(folder / "series" / f"{component['series_id']}.json") == component


def test_missing_asset_never_replaces_active_release(ready_workspace):
    pointer = (settings.data_dir / "active.json").read_bytes()
    path = settings.data_dir / "imagery/dhaka.json"
    pair = read_json(path)
    pair["before"]["url"] = "/media/imagery/dhaka/missing.webp"
    write_json(path, pair)
    with pytest.raises((OSError, ValueError)):
        build.build_release()
    assert (settings.data_dir / "active.json").read_bytes() == pointer
    assert not list((settings.data_dir / "releases").glob(".candidate-*"))


def test_failed_candidate_validation_never_activates(ready_workspace, monkeypatch):
    pointer = (settings.data_dir / "active.json").read_bytes()
    original = build._render_release

    def broken_output(inputs, folder, release_id, identity):
        manifest = original(inputs, folder, release_id, identity)
        path = folder / "stories/dhaka.json"
        story = read_json(path)
        story["temperature"]["annual"][0]["value"] = 12345
        write_json(path, story)
        return manifest

    monkeypatch.setattr(build, "_render_release", broken_output)
    with pytest.raises(ValueError, match="published annual temperatures differ"):
        build.build_release()
    assert (settings.data_dir / "active.json").read_bytes() == pointer


def test_numeric_tampering_fails_even_with_updated_output_catalog(ready_workspace):
    folder = ready_workspace
    path = folder / "stories/dhaka.json"
    story = read_json(path)
    story["temperature"]["annual"][0]["value"] = 12345
    story["temperature"]["comparison"]["difference"] = 999
    write_json(path, story)
    write_json(folder / "series" / f"{story['temperature']['series_id']}.json", story["temperature"])
    _refresh_output_hashes(folder)
    with pytest.raises(ValueError, match="comparison values differ"):
        validation.validate_release(folder=folder, write_report=False)


def test_review_tampering_fails_even_with_updated_output_catalog(ready_workspace):
    folder = ready_workspace
    path = folder / "stories/dhaka.json"
    story = read_json(path)
    story["imagery"]["review"]["before_sha256"] = "stale-checksum"
    write_json(path, story)
    _refresh_output_hashes(folder)
    with pytest.raises(ValueError, match="embedded imagery approval differs"):
        validation.validate_release(folder=folder, write_report=False)


def test_changed_pinned_input_hash_cannot_keep_the_old_release_identity(ready_workspace):
    folder = ready_workspace
    manifest = read_json(folder / "release.json")
    manifest["identity"]["input_sha256"]["power/dhaka.json"] = "0" * 64
    write_json(folder / "release.json", manifest)
    with pytest.raises(ValueError, match="Release identity differs"):
        validation.validate_release(folder=folder, write_report=False)


@pytest.mark.parametrize("change", ["checksum", "withdraw", "remove"])
def test_current_review_changes_invalidate_cache_and_stop_publication(ready_workspace, change):
    pointer = (settings.data_dir / "active.json").read_bytes()
    path = settings.content_dir / "imagery-reviews.json"
    reviews = read_json(path)
    if change == "checksum":
        reviews["dhaka"]["before_sha256"] = "changed"
    elif change == "withdraw":
        reviews["dhaka"]["status"] = "withdrawn"
    else:
        del reviews["dhaka"]
    write_json(path, reviews)
    result = imagery.prepare_all(["dhaka"])
    assert result[0]["status"] == "needs_review"
    assert read_json(settings.data_dir / "imagery/dhaka.json")["review"] is None
    with pytest.raises(ValueError, match="imagery review is incomplete"):
        build.build_release()
    assert (settings.data_dir / "active.json").read_bytes() == pointer
    with pytest.raises(ValueError, match="Current publication authority changed"):
        validation.validate_release(folder=ready_workspace, write_report=False)
    # Historical verification is still possible against the pinned original authority.
    assert validation.validate_release(
        folder=ready_workspace, require_current_reviews=False, write_report=False
    )["passed"]


def test_changed_candidates_do_not_take_the_approved_fast_path(ready_workspace, monkeypatch):
    path = settings.content_dir / "imagery-candidates.json"
    candidates = read_json(path)
    candidates["A"]["before"] = candidates["A"]["before"].replace("19900107", "19890107")
    write_json(path, candidates)
    called = []

    def no_network(place_id):
        called.append(place_id)
        raise ValueError("Replacement imagery needs acquisition")

    monkeypatch.setattr(imagery, "prepare_place", no_network)
    result = imagery.prepare_all(["dhaka"])
    assert called == ["dhaka"] and result[0]["status"] == "failed"
    assert read_json(settings.data_dir / "imagery/dhaka.json")["status"] == "needs_review"


def test_changed_processing_configuration_invalidates_cache(ready_workspace, monkeypatch):
    monkeypatch.setitem(DISPLAY, "gamma", 1.7)
    called = []

    def no_network(place_id):
        called.append(place_id)
        raise ValueError("Replacement processing is required")

    monkeypatch.setattr(imagery, "prepare_place", no_network)
    imagery.prepare_all(["dhaka"])
    assert called == ["dhaka"]
    assert read_json(settings.data_dir / "imagery/dhaka.json")["review"] is None


def test_provenance_change_gets_a_new_id_and_preserves_old_bytes(ready_workspace):
    before = directory_hashes(ready_workspace)
    path = settings.raw_dir / "archive-inventory.json"
    inventory = read_json(path)
    inventory["imported_at"] = "2026-11-08T12:00:00+00:00"
    write_json(path, inventory)
    result = build.build_release()
    assert result["id"] != ready_workspace.name
    assert directory_hashes(ready_workspace) == before


def test_pinned_validation_does_not_depend_on_mutable_raw_directory(ready_workspace):
    path = settings.raw_dir / "power/dhaka.json"
    payload = read_json(path)
    payload["properties"]["parameter"]["T2M"]["202501"] = -999
    write_json(path, payload)
    assert validation.validate_release(folder=ready_workspace, write_report=False)["passed"]


def test_existing_release_cannot_be_overwritten_with_different_content(ready_workspace):
    path = ready_workspace / "sources/nasa-power.json"
    source = read_json(path)
    source["notes"]["en"] = "An unexpected changed output"
    write_json(path, source)
    before = path.read_bytes()
    pointer = (settings.data_dir / "active.json").read_bytes()
    with pytest.raises(ValueError, match="Immutable release"):
        build.build_release()
    assert path.read_bytes() == before
    assert (settings.data_dir / "active.json").read_bytes() == pointer


def _storage_settings(monkeypatch):
    for name in ["s3_endpoint_url", "s3_access_key_id", "s3_secret_access_key", "s3_bucket"]:
        monkeypatch.setattr(settings, name, "test-value")


def test_invalid_release_never_reaches_storage_client(ready_workspace, monkeypatch):
    _storage_settings(monkeypatch)
    path = ready_workspace / "stories/dhaka.json"
    story = read_json(path)
    story["temperature"]["annual"][0]["value"] = 12345
    write_json(path, story)
    called = []
    monkeypatch.setattr(storage.boto3, "client", lambda *args, **kwargs: called.append(True))
    with pytest.raises(ValueError, match="Release validation failed"):
        storage.publish()
    assert not called


def test_storage_pointer_is_bound_to_validated_release(ready_workspace, monkeypatch):
    _storage_settings(monkeypatch)
    uploaded = []

    class Client:
        def put_object(self, **kwargs):
            uploaded.append(kwargs)
            if len(uploaded) == 1:
                write_json(settings.data_dir / "active.json", {"id": "mcs-another-release"})

    monkeypatch.setattr(storage.boto3, "client", lambda *args, **kwargs: Client())
    result = storage.publish()
    assert result["release_id"] == ready_workspace.name
    assert uploaded[-1]["Key"] == "active.json"
    assert json.loads(uploaded[-1]["Body"]) == {"id": ready_workspace.name}
    assert all("/inputs/" not in item["Key"] for item in uploaded)
    assert all(item["ContentType"] == "image/webp" for item in uploaded if item["Key"].endswith(".webp"))
