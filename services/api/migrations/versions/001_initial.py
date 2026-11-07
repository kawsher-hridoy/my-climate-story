"""Initial climate catalog, normalized records, jobs and publication reviews."""

from alembic import op
from climate.db import Base

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS postgis")
        connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    Base.metadata.create_all(connection)
    if connection.dialect.name == "postgresql":
        connection.exec_driver_sql(
            "CREATE INDEX ix_place_aliases_trgm ON place_aliases USING gin (normalized gin_trgm_ops)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX ix_places_geography ON places USING gist ((ST_SetSRID(ST_MakePoint(longitude, latitude),4326)::geography))"
        )


def downgrade():
    Base.metadata.drop_all(op.get_bind())
