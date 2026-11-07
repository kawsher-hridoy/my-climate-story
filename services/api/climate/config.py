from pathlib import Path

from psycopg.conninfo import make_conninfo
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    # An explicit URL remains available for local/test deployments. Compose passes
    # components so reserved password characters cannot alter URL structure.
    database_url: str | None = Field(default=None, repr=False)
    postgres_host: str = "localhost"
    postgres_port: int = Field(default=55432, ge=1, le=65535)
    postgres_user: str = "climate"
    postgres_password: str = Field(default="climate_dev_password", repr=False)
    postgres_db: str = "climate"
    app_env: str = "development"
    app_contact_url: str = "http://localhost:5173/about"
    public_asset_base_url: str = "/media"
    earthdata_username: str = ""
    earthdata_password: str = ""
    earthdata_token: str = ""
    s3_endpoint_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_bucket: str = ""
    s3_public_base_url: str = ""
    data_dir: Path = ROOT / "data" / "processed"
    raw_dir: Path = ROOT / "data" / "raw"
    staging_dir: Path = ROOT / "data" / "staging"
    content_dir: Path = ROOT / "content"

    @model_validator(mode="after")
    def resolve_database_url(self):
        if not self.database_url:
            self.database_url = URL.create(
                "postgresql+psycopg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                database=self.postgres_db,
            ).render_as_string(hide_password=False)
        return self

    @property
    def queue_conninfo(self) -> str:
        """Use libpq's own quoting rather than treating a SQLAlchemy URL as a URI."""
        url = make_url(self.database_url)
        if url.get_backend_name() != "postgresql":
            # Isolated SQLite tests never open the PostgreSQL queue connector.
            return self.database_url
        parameters = {
            "host": url.host,
            "port": url.port,
            "user": url.username,
            "password": url.password,
            "dbname": url.database,
            **dict(url.query),
        }
        return make_conninfo(**{key: value for key, value in parameters.items() if value is not None})


settings = Settings()
