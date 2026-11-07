"""Transactional dispatch, bounded recovery and generation fencing for exploration work."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from .db import ExplorationJobRecord, Session
from .exploration_artifacts import IncompleteExploration, migrate_legacy_bundle, verified_bundle

CAPACITY = 20
MAX_DISPATCHES = 3
PENDING_LEASE = timedelta(minutes=15)
RUNNING_LEASE = timedelta(minutes=10)
TOTAL_LIFETIME = timedelta(hours=1)
HEARTBEAT_GRACE = timedelta(seconds=90)


def utcnow():
    return datetime.now(timezone.utc)


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def lock_capacity(session):
    """Serialize capacity checks and inserts, including requests for different places."""
    if session.bind.dialect.name == "postgresql":
        session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext('my-climate-story:exploration-capacity'))")
        )


def queue_state(session, job):
    if session.bind.dialect.name != "postgresql":
        # Isolated SQLite tests replace this adapter; no pretend queue implementation.
        return (
            {"id": job.queue_job_id, "status": "todo", "last_heartbeat": None} if job.queue_job_id else None
        )
    where = "q.id=:queue_id" if job.queue_job_id else "q.args->>'exploration_id'=:job_id"
    return (
        session.execute(
            text(
                "SELECT q.id, q.status::text AS status, w.last_heartbeat "
                "FROM procrastinate_jobs q LEFT JOIN procrastinate_workers w ON w.id=q.worker_id "
                f"WHERE {where} ORDER BY q.id DESC LIMIT 1"
            ),
            {"queue_id": job.queue_job_id, "job_id": job.id},
        )
        .mappings()
        .first()
    )


def retire_queue(session, state, dead_worker=False):
    if state is None or session.bind.dialect.name != "postgresql":
        return
    session.execute(text("SELECT procrastinate_cancel_job_v1(:id, true, false)"), {"id": state["id"]})
    if state["status"] == "doing" and dead_worker:
        session.execute(text("SELECT procrastinate_finish_job_v1(:id, 'failed', false)"), {"id": state["id"]})


def fail_job(job, message, now):
    job.status = "failed"
    job.message = message
    job.run_token = None
    job.lease_until = None
    job.updated_at = now


def dispatch_job(session, job, submit, now=None):
    """The caller owns one transaction containing both rows; submit must not commit."""
    now = now or utcnow()
    job.generation = (job.generation or 0) + 1
    job.dispatch_attempts = (job.dispatch_attempts or 0) + 1
    job.status = "pending"
    job.run_token = None
    job.result_dir = None
    job.result_hash = None
    job.lease_until = now + PENDING_LEASE
    job.updated_at = now
    job.message = "Queued for NASA data retrieval."
    session.flush()
    job.queue_job_id = submit(session, job)
    session.flush()


def reconcile_session(session, submit, now=None):
    """Repair legacy/orphaned work in bounded transactions without promoting partial files."""
    now = now or utcnow()
    lock_capacity(session)
    repaired = failed = migrated = 0
    legacy = session.scalars(
        select(ExplorationJobRecord)
        .where(ExplorationJobRecord.status == "completed", ExplorationJobRecord.result_hash.is_(None))
        .with_for_update(skip_locked=True)
        .limit(100)
    ).all()
    for job in legacy:
        if migrate_legacy_bundle(job):
            migrated += 1
        else:
            fail_job(job, "Older result is incomplete and needs a fresh retrieval.", now)
            failed += 1
    outstanding = session.scalars(
        select(ExplorationJobRecord)
        .where(ExplorationJobRecord.status.in_(["pending", "running"]))
        .order_by(ExplorationJobRecord.created_at)
        .with_for_update(skip_locked=True)
        .limit(100)
    ).all()
    for job in outstanding:
        state = queue_state(session, job)
        expired = now - aware(job.created_at) >= TOTAL_LIFETIME
        if expired:
            retire_queue(session, state)
            fail_job(job, "Retrieval expired. Submit a new exploration to try again.", now)
            failed += 1
            continue
        if state and not job.queue_job_id:
            job.queue_job_id = state["id"]
            job.dispatch_attempts = max(job.dispatch_attempts or 0, 1)
        heartbeat = state.get("last_heartbeat") if state else None
        dead = bool(
            state
            and state["status"] == "doing"
            and (heartbeat is None or now - aware(heartbeat) > HEARTBEAT_GRACE)
        )
        lease_expired = job.lease_until is not None and aware(job.lease_until) <= now
        queue_missing = state is None
        queue_terminal = bool(state and state["status"] not in ["todo", "doing"])
        if not any([dead, lease_expired, queue_missing, queue_terminal]):
            if job.lease_until is None:
                job.lease_until = now + (RUNNING_LEASE if job.status == "running" else PENDING_LEASE)
            continue
        # A live but overlong worker is fenced off and asked to abort; do not run copies concurrently.
        live_overlong = bool(state and state["status"] == "doing" and not dead and lease_expired)
        retire_queue(session, state, dead_worker=dead)
        if (job.dispatch_attempts or 0) >= MAX_DISPATCHES or live_overlong:
            fail_job(job, "Retrieval could not finish within its retry limit. Please try again later.", now)
            failed += 1
        else:
            dispatch_job(session, job, submit, now)
            repaired += 1
    session.flush()
    return {"requeued": repaired, "failed": failed, "migrated": migrated}


def reconcile_jobs():
    from .jobs import defer_exploration

    with Session.begin() as session:
        return reconcile_session(session, defer_exploration)


def completed_job(session, release_id, story_id):
    return session.scalar(
        select(ExplorationJobRecord)
        .where(
            ExplorationJobRecord.release_id == release_id,
            ExplorationJobRecord.story_id == story_id,
            ExplorationJobRecord.status == "completed",
        )
        .order_by(ExplorationJobRecord.updated_at.desc())
        .limit(1)
    )


def completed_story(session, release_id, story_id):
    job = completed_job(session, release_id, story_id)
    if job is None:
        raise IncompleteExploration("No completed exploration")
    return verified_bundle(job)[1]
