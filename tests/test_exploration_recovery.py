import asyncio
import json
import shutil
import subprocess
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from climate import exploration_artifacts as artifacts
from climate import exploration_lifecycle as lifecycle
from climate import jobs, main
from climate.config import settings
from climate.db import Base, ExplorationJobRecord
from climate.files import active_release, read_json, write_json
from climate.schemas import ExplorationRequest
from fastapi import HTTPException, Response
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    release_id, source = active_release()
    target = tmp_path / "data" / "releases" / release_id
    shutil.copytree(source, target)
    write_json(tmp_path / "data" / "active.json", {"id": release_id})
    raw = read_json(settings.raw_dir / "power" / "dhaka.json")
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    monkeypatch.setattr(settings, "raw_dir", tmp_path / "raw")
    engine = create_engine(f"sqlite:///{tmp_path / 'jobs.sqlite'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(jobs, "Session", sessions)
    monkeypatch.setattr(main, "Session", sessions)
    monkeypatch.setattr(lifecycle, "Session", sessions)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr("pipelines.providers.power_request", lambda *args, **kwargs: raw)
    main.traffic.clear()
    yield SimpleNamespace(root=tmp_path, engine=engine, sessions=sessions, release_id=release_id, raw=raw)
    main.traffic.clear()
    engine.dispose()


def make_job(sandbox, **overrides):
    coordinates = {"latitude": 23.8103, "longitude": 90.4125}
    fields = {
        "id": str(uuid4()),
        "request_key": str(uuid4()),
        "release_id": sandbox.release_id,
        "request_payload": {"coordinates": coordinates},
        "status": "pending",
        "generation": 1,
        "dispatch_attempts": 1,
        "queue_job_id": 1,
        "lease_until": lifecycle.utcnow() + lifecycle.PENDING_LEASE,
    }
    fields.update(overrides)
    with sandbox.sessions.begin() as session:
        session.add(ExplorationJobRecord(**fields))
    return fields["id"]


def test_submission_cancellation_rolls_back_application_row(sandbox, monkeypatch):
    def cancel(*args):
        raise asyncio.CancelledError()

    monkeypatch.setattr(main, "defer_exploration", cancel)
    request = SimpleNamespace(client=SimpleNamespace(host="test-client"))
    with sandbox.sessions() as session, pytest.raises(asyncio.CancelledError):
        main.explore(
            ExplorationRequest(coordinates={"latitude": 20, "longitude": 90}), request, Response(), session
        )
    with sandbox.sessions() as session:
        assert session.scalar(select(func.count()).select_from(ExplorationJobRecord)) == 0


def test_orphan_recovery_is_bounded_and_expired_work_releases_capacity(sandbox, monkeypatch):
    orphan = make_job(sandbox, queue_job_id=None, generation=0, dispatch_attempts=0)
    exhausted = make_job(sandbox, queue_job_id=None, dispatch_attempts=3)
    old = make_job(sandbox, created_at=lifecycle.utcnow() - timedelta(days=2), queue_job_id=None)
    submit = Mock(return_value=42)
    monkeypatch.setattr(lifecycle, "queue_state", lambda *_: None)
    with sandbox.sessions.begin() as session:
        report = lifecycle.reconcile_session(session, submit)
    assert report == {"requeued": 1, "failed": 2, "migrated": 0}
    submit.assert_called_once()
    with sandbox.sessions() as session:
        assert session.get(ExplorationJobRecord, orphan).queue_job_id == 42
        assert session.get(ExplorationJobRecord, orphan).generation == 1
        assert session.get(ExplorationJobRecord, exhausted).status == "failed"
        assert session.get(ExplorationJobRecord, old).status == "failed"


def test_completed_publication_contains_every_dependency(sandbox):
    identifier = make_job(sandbox)
    jobs.explore_point.func(identifier, generation=1)
    with sandbox.sessions() as session:
        job = session.get(ExplorationJobRecord, identifier)
        folder, story = artifacts.verified_bundle(job)
        assert job.status == "completed"
        assert (folder / "source.json").exists()
        assert (folder / "series" / f"{story.temperature.series_id}.json").exists()
        assert main.load_story(story.place.id, sandbox.release_id, session=session) == story
        assert main.component(story.temperature.series_id, sandbox.release_id) == story.temperature


def test_malformed_temperature_cannot_be_sealed_with_valid_source(sandbox):
    identifier = make_job(sandbox)
    jobs.explore_point.func(identifier, generation=1)
    with sandbox.sessions() as session:
        _, story = artifacts.verified_bundle(session.get(ExplorationJobRecord, identifier))
    story.temperature.annual[0].value = 12345
    with pytest.raises(artifacts.IncompleteExploration, match="Annual temperature"):
        artifacts.publish_bundle(str(uuid4()), 1, story, sandbox.raw)


def test_failed_dependency_write_never_exposes_story(sandbox, monkeypatch):
    identifier = make_job(sandbox)
    original = artifacts.write_json
    calls = []

    def fail_second(path, payload):
        calls.append(path)
        if len(calls) == 2:
            raise OSError("simulated full disk")
        original(path, payload)

    monkeypatch.setattr(artifacts, "write_json", fail_second)
    jobs.explore_point.func(identifier, generation=1)
    with sandbox.sessions() as session:
        job = session.get(ExplorationJobRecord, identifier)
        assert job.status == "failed"
        assert job.result_hash is None
    assert not list((settings.data_dir / "explorations").rglob("complete.json"))
    assert not list((settings.data_dir / "explorations").rglob(".staging-*"))
    coordinates = "23.8103,90.4125"
    import hashlib

    story_id = "point-" + hashlib.sha256(coordinates.encode()).hexdigest()[:20]
    with sandbox.sessions() as session, pytest.raises(HTTPException) as error:
        main.load_story(story_id, sandbox.release_id, session=session)
    assert error.value.status_code == 404


def test_stale_worker_generation_cannot_publish(sandbox):
    identifier = make_job(sandbox, generation=2)
    jobs.explore_point.func(identifier, generation=1)
    with sandbox.sessions() as session:
        job = session.get(ExplorationJobRecord, identifier)
        assert job.status == "pending"
        assert job.result_hash is None


def test_publication_requires_committed_database_state(sandbox):
    identifier = make_job(sandbox)
    jobs.explore_point.func(identifier, generation=1)
    with sandbox.sessions.begin() as session:
        job = session.get(ExplorationJobRecord, identifier)
        story_id = job.story_id
        job.status = "running"  # Simulate a crash after directory publication, before DB completion.
    with sandbox.sessions() as session, pytest.raises(HTTPException):
        main.load_story(story_id, sandbox.release_id, session=session)


def test_abrupt_worker_exit_recovers_with_new_generation(sandbox, monkeypatch):
    identifier = make_job(sandbox)
    config = {
        "database": str(sandbox.engine.url),
        "data": str(settings.data_dir),
        "raw": str(settings.raw_dir),
        "job": identifier,
        "payload": sandbox.raw,
    }
    config_path = sandbox.root / "crash-input.json"
    config_path.write_text(json.dumps(config))
    script = """import json,os,sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from climate import jobs
from climate.config import settings
import pipelines.providers
c=json.loads(Path(sys.argv[1]).read_text())
settings.data_dir=Path(c['data']);settings.raw_dir=Path(c['raw'])
jobs.Session=sessionmaker(create_engine(c['database']),expire_on_commit=False)
pipelines.providers.power_request=lambda *a,**kw:os._exit(73)
jobs.explore_point.func(c['job'],generation=1)
"""
    import sys

    result = subprocess.run([sys.executable, "-c", script, str(config_path)], capture_output=True, timeout=20)
    assert result.returncode == 73
    with sandbox.sessions() as session:
        assert session.get(ExplorationJobRecord, identifier).status == "running"
    monkeypatch.setattr(
        lifecycle, "queue_state", lambda *_: {"id": 1, "status": "doing", "last_heartbeat": None}
    )
    with sandbox.sessions.begin() as session:
        lifecycle.reconcile_session(session, Mock(return_value=2))
    with sandbox.sessions() as session:
        job = session.get(ExplorationJobRecord, identifier)
        assert job.status == "pending" and job.generation == 2
    jobs.explore_point.func(identifier, generation=2)
    with sandbox.sessions() as session:
        assert session.get(ExplorationJobRecord, identifier).status == "completed"


def test_legacy_partial_files_are_never_treated_as_complete(sandbox):
    identifier = make_job(sandbox, status="completed", story_id="point-legacy", result_hash=None)
    legacy = settings.data_dir / "explorations" / sandbox.release_id
    write_json(legacy / "point-legacy.json", {"partial": "story"})
    with sandbox.sessions.begin() as session:
        lifecycle.reconcile_session(session, Mock(return_value=2))
    with sandbox.sessions() as session:
        assert session.get(ExplorationJobRecord, identifier).status == "failed"


def test_valid_legacy_result_is_verified_and_migrated(sandbox):
    identifier = make_job(sandbox)
    jobs.explore_point.func(identifier, generation=1)
    with sandbox.sessions.begin() as session:
        job = session.get(ExplorationJobRecord, identifier)
        folder, story = artifacts.verified_bundle(job)
        legacy = settings.data_dir / "explorations" / sandbox.release_id
        write_json(legacy / f"{job.story_id}.json", story.model_dump(mode="json"))
        write_json(
            legacy / "series" / f"{story.temperature.series_id}.json",
            story.temperature.model_dump(mode="json"),
        )
        write_json(settings.raw_dir / "explorations" / f"{job.story_id}.json", sandbox.raw)
        job.result_dir = None
        job.result_hash = None
    with sandbox.sessions.begin() as session:
        report = lifecycle.reconcile_session(session, Mock(return_value=42))
        assert report["migrated"] == 1
    with sandbox.sessions() as session:
        _, restored = artifacts.verified_bundle(session.get(ExplorationJobRecord, identifier))
        assert restored == story
