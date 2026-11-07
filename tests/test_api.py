from unittest.mock import Mock

import pytest
from climate import main
from climate.config import settings
from climate.db import Base, PlaceAliasRecord, PlaceRecord, get_session
from climate.files import read_json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)

    def dependency():
        with sessions() as session:
            yield session

    main.app.dependency_overrides[get_session] = dependency
    monkeypatch.setattr(settings, "app_env", "test")
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "Session", sessions)
    deferred = Mock(return_value=1)
    monkeypatch.setattr(main, "defer_exploration", deferred)
    main.traffic.clear()
    with sessions.begin() as session:
        place = read_json(settings.content_dir / "places.json")[0]
        session.add(
            PlaceRecord(
                id="dhaka",
                name="Dhaka",
                name_bn="ঢাকা",
                latitude=23.8103,
                longitude=90.4125,
                featured=1,
                payload=place,
            )
        )
        session.add(PlaceAliasRecord(place_id="dhaka", normalized="dhaka", name="Dhaka"))
        session.add(PlaceAliasRecord(place_id="dhaka", normalized="ঢাকা", name="ঢাকা"))
    with TestClient(main.app) as http:
        yield http, sessions, deferred
    main.app.dependency_overrides.clear()
    main.traffic.clear()
    engine.dispose()


def test_featured_story_and_pinned_release_contract(client):
    http, _, _ = client
    response = http.get("/api/v1/places/featured")
    assert response.status_code == 200 and len(response.json()) == 12
    story = http.get("/api/v1/stories/dhaka")
    assert story.status_code == 200 and story.headers["etag"]
    data = story.json()
    assert len(data["temperature"]["monthly"]) == 540
    assert not data["rainfall"]["monthly"]
    version = http.get(f"/api/v1/stories/dhaka?release={data['release']['id']}")
    assert "immutable" in version.headers["cache-control"]
    assert version.json() == data


def test_search_bangla_and_literal_wildcards(client):
    http, _, _ = client
    assert http.get("/api/v1/places/search", params={"q": "ঢাকা"}).json()["results"][0]["id"] == "dhaka"
    assert http.get("/api/v1/places/search", params={"q": "%%"}).json()["results"] == []
    assert http.get("/api/v1/places/search", params={"q": "D", "limit": 100}).status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"place_id": "dhaka", "coordinates": {"latitude": 20, "longitude": 90}},
        {"coordinates": {"latitude": 91, "longitude": 90}},
        {"coordinates": {"latitude": 20, "longitude": 181}},
        {"coordinates": {"latitude": "NaN", "longitude": 90}},
        {"coordinates": {"latitude": 20, "longitude": 90}, "upstream_url": "https://example.com"},
    ],
)
def test_invalid_exploration_inputs_are_rejected(client, body):
    http, _, deferred = client
    assert http.post("/api/v1/explorations", json=body).status_code == 422
    deferred.assert_not_called()


def test_featured_exploration_never_queues_upstream(client):
    http, _, deferred = client
    response = http.post("/api/v1/explorations", json={"place_id": "dhaka"})
    assert response.status_code == 200
    assert response.json()["story"]["place"]["id"] == "dhaka"
    deferred.assert_not_called()


def test_duplicate_coordinate_requests_share_one_durable_job(client):
    http, sessions, deferred = client
    body = {"coordinates": {"latitude": 52.52, "longitude": 13.405}}
    one = http.post("/api/v1/explorations", json=body)
    two = http.post("/api/v1/explorations", json=body)
    assert one.status_code == two.status_code == 202
    assert one.json()["job"]["id"] == two.json()["job"]["id"]
    deferred.assert_called_once()
    assert http.get("/api/v1/jobs/" + one.json()["job"]["id"]).json()["status"] == "pending"


def test_queue_unavailable_has_terminal_error(client):
    http, _, deferred = client
    deferred.side_effect = RuntimeError("worker unavailable")
    response = http.post(
        "/api/v1/explorations", json={"coordinates": {"latitude": 52.52, "longitude": 13.405}}
    )
    assert response.status_code == 503
    assert response.json()["code"] == "http_503"


def test_expensive_request_rate_is_bounded(client):
    http, _, _ = client
    for index in range(5):
        assert (
            http.post(
                "/api/v1/explorations", json={"coordinates": {"latitude": 51 + index / 10, "longitude": 13}}
            ).status_code
            == 202
        )
    assert (
        http.post("/api/v1/explorations", json={"coordinates": {"latitude": 53, "longitude": 13}}).status_code
        == 429
    )


def test_csv_preserves_units_and_missing_values(client):
    http, _, _ = client
    story = http.get("/api/v1/stories/dhaka").json()
    series = story["temperature"]["series_id"]
    response = http.get(f"/api/v1/exports/{series}.csv")
    assert response.status_code == 200
    assert "dataset,release,publication_state" in response.text
    assert "°C,nasa-power" in response.text
    assert "198113" not in response.text
    missing = http.get("/api/v1/exports/" + story["rainfall"]["series_id"] + ".csv")
    assert missing.status_code == 404


def test_unknown_and_path_like_ids_do_not_read_files(client):
    http, _, _ = client
    assert http.get("/api/v1/stories/not-a-place").status_code == 404
    assert http.get("/api/v1/stories/dhaka", params={"release": "../private"}).status_code == 422
    assert http.get("/api/v1/sources/not-a-source").status_code == 404
