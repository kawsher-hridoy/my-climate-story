"""Atomic queue references, bounded recovery and completed exploration artifacts."""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    # Migration 001 historically created current metadata; tolerate its new-install shape.
    existing = {column["name"] for column in sa.inspect(connection).get_columns("exploration_jobs")}
    columns = [
        sa.Column("queue_job_id", sa.BigInteger(), nullable=True),
        sa.Column("generation", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dispatch_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("run_token", sa.String(36), nullable=True),
        sa.Column("result_dir", sa.String(100), nullable=True),
        sa.Column("result_hash", sa.String(64), nullable=True),
    ]
    for column in columns:
        if column.name not in existing:
            op.add_column("exploration_jobs", column)
    # Preserve historical rows, but only the newest outstanding request owns each key.
    duplicates = connection.execute(
        sa.text(
            "SELECT id, request_key FROM exploration_jobs WHERE status IN ('pending','running') "
            "ORDER BY created_at DESC, id DESC"
        )
    ).mappings()
    seen = set()
    for row in duplicates:
        if row["request_key"] in seen:
            connection.execute(
                sa.text("UPDATE exploration_jobs SET status='failed', message=:message WHERE id=:id"),
                {
                    "id": row["id"],
                    "message": "Superseded duplicate request; submit a fresh exploration if needed.",
                },
            )
        seen.add(row["request_key"])
    indexes = {index["name"] for index in sa.inspect(connection).get_indexes("exploration_jobs")}
    if "uq_exploration_active_request" not in indexes:
        op.create_index(
            "uq_exploration_active_request",
            "exploration_jobs",
            ["request_key"],
            unique=True,
            postgresql_where=sa.text("status IN ('pending','running')"),
            sqlite_where=sa.text("status IN ('pending','running')"),
        )


def downgrade():
    op.drop_index("uq_exploration_active_request", table_name="exploration_jobs")
    for name in [
        "result_hash",
        "result_dir",
        "run_token",
        "lease_until",
        "dispatch_attempts",
        "generation",
        "queue_job_id",
    ]:
        op.drop_column("exploration_jobs", name)
