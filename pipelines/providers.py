import time
from urllib.parse import urlparse

import httpx
from climate.config import settings


def get_public_json(url: str, params: dict | None = None, allowed_hosts: set[str] | None = None) -> dict:
    host = urlparse(url).hostname
    if allowed_hosts is not None and host not in allowed_hosts:
        raise ValueError("Unsupported upstream host")
    with httpx.Client(
        timeout=httpx.Timeout(60, connect=15),
        headers={"User-Agent": f"MyClimateStory/0.1 (+{settings.app_contact_url})"},
    ) as client:
        for attempt in range(3):
            try:
                response = client.get(url, params=params)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < 2:
                        retry = response.headers.get("Retry-After", "")
                        time.sleep(min(int(retry), 30) if retry.isdigit() else 2 ** (attempt + 1))
                        continue
                response.raise_for_status()
                return response.json()
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt == 2:
                    raise
                time.sleep(2 ** (attempt + 1))
    raise RuntimeError("Upstream request failed after bounded retries")


def power_request(latitude: float, longitude: float, start=1981, end=2025) -> dict:
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Invalid coordinates")
    return get_public_json(
        "https://power.larc.nasa.gov/api/temporal/monthly/point",
        {
            "parameters": "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M",
            "community": "AG",
            "longitude": longitude,
            "latitude": latitude,
            "start": start,
            "end": end,
            "format": "JSON",
        },
        allowed_hosts={"power.larc.nasa.gov"},
    )
