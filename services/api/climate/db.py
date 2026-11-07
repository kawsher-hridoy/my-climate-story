from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import settings


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class PlaceRecord(Base):
    __tablename__ = "places"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    name_bn: Mapped[str] = mapped_column(String(200), default="")
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    country: Mapped[str] = mapped_column(String(2), default="BD")
    division: Mapped[str] = mapped_column(String(200), default="")
    feature_type: Mapped[str] = mapped_column(String(30), default="city")
    population: Mapped[int] = mapped_column(Integer, default=0)
    featured: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (Index("ix_places_coords", "latitude", "longitude"),)


class PlaceAliasRecord(Base):
    __tablename__ = "place_aliases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    place_id: Mapped[str] = mapped_column(String(100), index=True)
    normalized: Mapped[str] = mapped_column(Text, index=True)
    name: Mapped[str] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("place_id", "normalized"),)


class ReleaseRecord(Base):
    __tablename__ = "data_releases"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    manifest: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="prepared")


class SourceRequestRecord(Base):
    __tablename__ = "source_requests"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dataset: Mapped[str] = mapped_column(String(100))
    release_id: Mapped[str] = mapped_column(String(100), index=True)
    checksum: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSON)


class SeriesRecord(Base):
    __tablename__ = "climate_series"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    dataset: Mapped[str] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(50))
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    publication_state: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict] = mapped_column(JSON)


class ObservationRecord(Base):
    __tablename__ = "observations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    series_id: Mapped[str] = mapped_column(String(100), index=True)
    period: Mapped[str] = mapped_column(String(20))
    resolution: Mapped[str] = mapped_column(String(20))
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    __table_args__ = (UniqueConstraint("series_id", "period", "resolution"),)


class ReviewRecord(Base):
    __tablename__ = "publication_reviews"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    subject: Mapped[str] = mapped_column(String(100), index=True)
    reviewer: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30))
    evidence: Mapped[dict] = mapped_column(JSON)


class ImageryRecord(Base):
    __tablename__ = "imagery_pairs"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    place_id: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict] = mapped_column(JSON)


class ExplorationJobRecord(Base):
    __tablename__ = "exploration_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_key: Mapped[str] = mapped_column(String(64), index=True)
    release_id: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    story_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    request_payload: Mapped[dict] = mapped_column(JSON)
    message: Mapped[str] = mapped_column(Text, default="Queued for NASA data retrieval.")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    queue_job_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    generation: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    dispatch_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    run_token: Mapped[str | None] = mapped_column(String(36), nullable=True)
    result_dir: Mapped[str | None] = mapped_column(String(100), nullable=True)
    result_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    __table_args__ = (
        Index(
            "uq_exploration_active_request",
            "request_key",
            unique=True,
            postgresql_where=text("status IN ('pending', 'running')"),
            sqlite_where=text("status IN ('pending', 'running')"),
        ),
    )


engine = create_engine(settings.database_url, pool_pre_ping=True)
Session = sessionmaker(engine, expire_on_commit=False)


def get_session():
    with Session() as session:
        yield session
