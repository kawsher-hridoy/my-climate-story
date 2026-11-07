import argparse
import json

from .config import ROOT


def main():
    parser = argparse.ArgumentParser(description="My Climate Story operations")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in [
        "ingest",
        "build",
        "migrate",
        "seed",
        "worker",
        "queue-schema",
        "validate",
        "openapi",
        "imerg",
        "imerg-discover",
        "refresh-power",
        "refresh-global",
        "publish",
    ]:
        commands.add_parser(command)
    gazetteer = commands.add_parser("gazetteer")
    gazetteer.add_argument("--bangladesh-only", action="store_true")
    images = commands.add_parser("imagery")
    images.add_argument("--places", default="")
    review = commands.add_parser("review-temperature")
    review.add_argument("--reviewer", required=True)
    review.add_argument("--evidence", required=True)
    review = commands.add_parser("review-imagery")
    review.add_argument("--place", required=True)
    review.add_argument("--reviewer", required=True)
    review.add_argument("--evidence", required=True)
    args = parser.parse_args()
    if args.command == "ingest":
        from pipelines.build import import_archive

        result = import_archive()
    elif args.command == "build":
        from pipelines.build import build_release

        result = build_release()
    elif args.command == "migrate":
        from alembic import command
        from alembic.config import Config

        command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
        result = {"database": "migrated"}
    elif args.command == "seed":
        from .catalog import seed_release

        result = seed_release()
    elif args.command == "queue-schema":
        from sqlalchemy import text

        from .db import engine
        from .jobs import app

        with engine.connect() as connection:
            exists = connection.scalar(text("SELECT to_regclass('public.procrastinate_jobs')"))
        if not exists:
            with app.open():
                app.schema_manager.apply_schema()
        result = {"queue_schema": "ready"}
    elif args.command == "worker":
        from .jobs import worker

        worker()
        return
    elif args.command == "gazetteer":
        from pipelines.gazetteer import import_places

        result = import_places(include_global=not args.bangladesh_only)
    elif args.command == "imagery":
        from pipelines.imagery import prepare_all

        result = prepare_all(args.places.split(",") if args.places else None)
    elif args.command == "review-temperature":
        from pipelines.build import review_temperature

        result = review_temperature(args.reviewer, args.evidence)
    elif args.command == "review-imagery":
        from pipelines.imagery import review_pair

        result = review_pair(args.place, args.reviewer, args.evidence)
    elif args.command == "imerg":
        from pipelines.imerg import ingest

        result = ingest()
    elif args.command == "imerg-discover":
        from pipelines.imerg import discover

        catalog = discover()
        result = {key: value for key, value in catalog.items() if key != "granules"}
    elif args.command == "refresh-power":
        from pipelines.refresh import refresh_power

        result = refresh_power()
    elif args.command == "refresh-global":
        from pipelines.refresh import refresh_global

        result = refresh_global()
    elif args.command == "validate":
        from pipelines.validation import validate_release

        result = validate_release()
    elif args.command == "openapi":
        from .files import write_json
        from .main import app

        write_json(ROOT / "docs" / "openapi.json", app.openapi())
        result = {"openapi": "docs/openapi.json"}
    elif args.command == "publish":
        from pipelines.storage import publish

        result = publish()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
