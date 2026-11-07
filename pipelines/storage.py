import mimetypes

import boto3
from climate.config import settings
from climate.files import active_release, read_json

from .release_io import json_bytes, safe_relative, sha256
from .validation import validate_release


def publish() -> dict:
    if not all(
        [
            settings.s3_endpoint_url,
            settings.s3_access_key_id,
            settings.s3_secret_access_key,
            settings.s3_bucket,
        ]
    ):
        return {
            "status": "local",
            "message": "Local artifacts are available. Configure S3-compatible credentials to publish a remote copy.",
        }
    release_id, folder = active_release()
    validate_release(
        release_id, folder=folder, require_ready=True, require_current_reviews=True, write_report=False
    )
    manifest = read_json(folder / "release.json")
    public_files = dict(manifest["output_sha256"])
    public_files["release.json"] = sha256((folder / "release.json").read_bytes())
    client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name="auto",
    )
    count = 0
    for root, prefix, inventory in [
        (folder, f"releases/{release_id}", public_files),
        (settings.data_dir / "assets", "media", manifest["identity"]["asset_sha256"]),
    ]:
        for name, checksum in sorted(inventory.items()):
            # Only declared public outputs/dependencies are uploaded; pinned raw inputs remain local.
            path = root / safe_relative(name)
            body = path.read_bytes()
            if sha256(body) != checksum:
                raise ValueError(f"Artifact changed during publication: {name}")
            content_type = (
                "image/webp"
                if path.suffix == ".webp"
                else mimetypes.guess_type(path)[0] or "application/octet-stream"
            )
            client.put_object(
                Bucket=settings.s3_bucket,
                Key=f"{prefix}/{name}",
                Body=body,
                ContentType=content_type,
                CacheControl="public,max-age=31536000,immutable",
            )
            count += 1
    # Publish the active pointer last; scientific raw files and credentials are never uploaded as public assets.
    client.put_object(
        Bucket=settings.s3_bucket,
        Key="active.json",
        Body=json_bytes({"id": release_id}),
        ContentType="application/json",
        CacheControl="public,max-age=60",
    )
    return {"status": "published", "release_id": release_id, "files": count + 1}
