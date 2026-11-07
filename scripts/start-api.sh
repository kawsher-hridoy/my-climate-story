#!/bin/sh
set -eu
python scripts/bootstrap_data.py
climate migrate
climate queue-schema
climate seed
climate validate
if python -c "import sys; from climate.db import Session, PlaceRecord; from sqlalchemy import select; s=Session(); sys.exit(0 if s.scalar(select(PlaceRecord.id).where(PlaceRecord.id.like('geonames-%')).limit(1)) is None else 1)"; then
    climate gazetteer
fi
exec uvicorn climate.main:app --host 0.0.0.0 --port 8000 --no-access-log --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1,::1}"
