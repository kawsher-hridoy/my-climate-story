import asyncio

import pytest
import yaml
from climate import main
from climate.config import ROOT, Settings
from fastapi import HTTPException, Request
from psycopg.conninfo import conninfo_to_dict
from sqlalchemy.engine import make_url
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


@pytest.mark.parametrize("password", ["plain-example", "Example@Strong/Password42", "space #?%:$&+é"])
def test_database_components_preserve_reserved_password_characters(password, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    config = Settings(
        _env_file=None,
        database_url=None,
        postgres_host="db",
        postgres_port=5432,
        postgres_user="climate",
        postgres_password=password,
        postgres_db="climate",
    )
    parsed = make_url(config.database_url)
    assert (parsed.host, parsed.port, parsed.database, parsed.password) == ("db", 5432, "climate", password)
    queue_connection = conninfo_to_dict(config.queue_conninfo)
    assert queue_connection["password"] == password
    assert queue_connection["host"] == "db"
    assert password not in repr(config)


def test_explicit_database_url_stays_compatible():
    config = Settings(_env_file=None, database_url="sqlite://", postgres_password="ignored")
    assert config.database_url == "sqlite://"


def test_compose_passes_password_as_a_component_and_trusts_only_caddy():
    compose = yaml.safe_load((ROOT / "infra/compose.yml").read_text())
    for service in ["api", "worker"]:
        environment = compose["services"][service]["environment"]
        assert "DATABASE_URL" not in environment
        assert environment["POSTGRES_HOST"] == "db"
        assert "POSTGRES_PASSWORD" in environment
    assert (
        compose["services"]["api"]["environment"]["FORWARDED_ALLOW_IPS"]
        == "127.0.0.1,::1,${PROXY_IP:-172.30.249.2}"
    )
    assert compose["services"]["web"]["networks"]["proxy"]["ipv4_address"] == "${PROXY_IP:-172.30.249.2}"
    # Pin both peers so Docker cannot allocate the Caddy address to the API first.
    assert (
        compose["services"]["api"]["networks"]["proxy"]["ipv4_address"]
        == "${PROXY_API_IP:-172.30.249.3}"
    )
    assert "ports" not in compose["services"]["api"]
    startup = (ROOT / "scripts/start-api.sh").read_text()
    assert '--forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1,::1}"' in startup


def test_forwarded_clients_have_independent_limits_and_untrusted_headers_are_ignored():
    main.traffic.clear()
    observed = []

    async def application(scope, receive, send):
        request = Request(scope)
        status = 200
        try:
            main.throttle(request, "proxy-regression", 5)
        except HTTPException as error:
            status = error.status_code
        observed.append((request.client.host, status))

    proxy = ProxyHeadersMiddleware(application, trusted_hosts=["127.0.0.1", "::1", "172.30.249.2"])

    async def send_request(peer, forwarded):
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "path": "/",
            "scheme": "http",
            "server": ("api", 8000),
            "client": (peer, 34567),
            "headers": [(b"x-forwarded-for", forwarded.encode())],
        }
        await proxy(scope, None, None)

    async def run():
        for index in range(1, 7):
            await send_request("172.30.249.2", f"198.51.100.{index}")
        for _ in range(5):
            await send_request("172.30.249.2", "198.51.100.1")
        await send_request("203.0.113.99", "198.51.100.200")

    asyncio.run(run())
    try:
        assert observed[:6] == [(f"198.51.100.{index}", 200) for index in range(1, 7)]
        assert observed[-2] == ("198.51.100.1", 429)
        assert observed[-1] == ("203.0.113.99", 200)
    finally:
        main.traffic.clear()
