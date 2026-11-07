"""Opt-in integration tests; TEST_DATABASE_URL must point at a disposable database."""

import os
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from climate import db, jobs, main
from climate.config import ROOT
from climate.db import Base, ExplorationJobRecord
from climate.exploration_lifecycle import dispatch_job, reconcile_session
from climate.files import active_release
from climate.schemas import ExplorationRequest
from fastapi import HTTPException, Response
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="Disposable PostgreSQL required"
)


@pytest.fixture
def postgres(monkeypatch):
    uri = os.environ["TEST_DATABASE_URL"]
    if make_url(uri).database != "climate_jobs_test":
        pytest.fail("Refusing integration cleanup outside the explicitly named disposable test database")
    engine = create_engine(uri, pool_size=5)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP SCHEMA public CASCADE")
        connection.exec_driver_sql("CREATE SCHEMA public")
    Base.metadata.create_all(engine)
    schema = jobs.app.schema_manager.get_schema()
    with engine.begin() as connection:
        connection.connection.driver_connection.execute(schema)
    sessions = sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(main, "Session", sessions)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(jobs, "Session", sessions)
    main.traffic.clear()
    yield engine, sessions
    main.traffic.clear()
    engine.dispose()


def new_job():
    return ExplorationJobRecord(
        id=str(uuid4()),
        request_key=str(uuid4()),
        release_id=active_release()[0],
        request_payload={"coordinates": {"latitude": 20, "longitude": 90}},
    )


def test_procrastinate_enqueue_and_application_row_commit_together(postgres):
    engine, sessions = postgres
    with sessions.begin() as session:
        job = new_job()
        session.add(job)
        dispatch_job(session, job, jobs.defer_exploration)
        queue_id = job.queue_job_id
        with engine.connect() as observer:
            assert observer.scalar(text("SELECT count(*) FROM exploration_jobs")) == 0
            assert observer.scalar(text("SELECT count(*) FROM procrastinate_jobs")) == 0
    with engine.connect() as observer:
        assert observer.scalar(text("SELECT count(*) FROM exploration_jobs")) == 1
        queued = observer.execute(
            text("SELECT args FROM procrastinate_jobs WHERE id=:id"), {"id": queue_id}
        ).scalar_one()
        assert queued == {"exploration_id": job.id, "generation": 1}


def test_failure_after_real_queue_insert_rolls_back_both_rows(postgres):
    engine, sessions = postgres
    with pytest.raises(RuntimeError), sessions.begin() as session:
        job = new_job()
        session.add(job)
        dispatch_job(session, job, jobs.defer_exploration)
        raise RuntimeError("simulated failure before transaction commit")
    with engine.connect() as observer:
        assert observer.scalar(text("SELECT count(*) FROM exploration_jobs")) == 0
        assert observer.scalar(text("SELECT count(*) FROM procrastinate_jobs")) == 0


def test_capacity_is_atomic_across_different_requests(postgres):
    _, sessions = postgres
    with sessions.begin() as session:
        for _ in range(19):
            job = new_job()
            session.add(job)
            dispatch_job(session, job, jobs.defer_exploration)

    def submit(index):
        with sessions() as session:
            try:
                response = Response()
                main.explore(
                    ExplorationRequest(coordinates={"latitude": 30 + index, "longitude": 80}),
                    SimpleNamespace(client=SimpleNamespace(host=f"client-{index}")),
                    response,
                    session,
                )
                return response.status_code
            except HTTPException as error:
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(submit, [1, 2]))
    assert sorted(statuses) == [202, 503]
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(ExplorationJobRecord)) == 20


def test_dead_queue_worker_is_retired_and_requeued_atomically(postgres):
    engine, sessions = postgres
    with sessions.begin() as session:
        job = new_job()
        session.add(job)
        dispatch_job(session, job, jobs.defer_exploration)
        old_queue_id = job.queue_job_id
        job.status = "running"
        identifier = job.id
        session.execute(
            text("UPDATE procrastinate_jobs SET status='doing', worker_id=NULL WHERE id=:id"),
            {"id": old_queue_id},
        )
    with sessions.begin() as session:
        report = reconcile_session(session, jobs.defer_exploration)
    assert report["requeued"] == 1
    with sessions() as session:
        job = session.get(ExplorationJobRecord, identifier)
        assert job.status == "pending" and job.generation == 2
        assert job.queue_job_id != old_queue_id
    with engine.connect() as connection:
        assert (
            connection.scalar(
                text("SELECT status FROM procrastinate_jobs WHERE id=:id"), {"id": old_queue_id}
            )
            == "failed"
        )


def test_upgrade_legacy_001_and_fresh_database(postgres, monkeypatch):
    engine, _ = postgres
    monkeypatch.setattr(db, "engine", engine)
    fields = [
        "queue_job_id",
        "generation",
        "dispatch_attempts",
        "lease_until",
        "run_token",
        "result_dir",
        "result_hash",
    ]
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP INDEX uq_exploration_active_request")
        for name in fields:
            connection.exec_driver_sql(f"ALTER TABLE exploration_jobs DROP COLUMN {name}")
        connection.exec_driver_sql("CREATE TABLE alembic_version (version_num varchar(32) PRIMARY KEY)")
        connection.exec_driver_sql("INSERT INTO alembic_version VALUES ('001')")
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    assert set(fields).issubset(
        {column["name"] for column in inspect(engine).get_columns("exploration_jobs")}
    )
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP SCHEMA public CASCADE")
        connection.exec_driver_sql("CREATE SCHEMA public")
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    assert set(fields).issubset(
        {column["name"] for column in inspect(engine).get_columns("exploration_jobs")}
    )
