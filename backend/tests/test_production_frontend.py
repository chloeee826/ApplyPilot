from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def frontend_dist(tmp_path: Path) -> Path:
    assets = tmp_path / "assets"
    assets.mkdir()
    (tmp_path / "index.html").write_text(
        '<!doctype html><div id="root">ApplyPilot production</div>',
        encoding="utf-8",
    )
    (assets / "app.js").write_text("console.log('ApplyPilot')", encoding="utf-8")
    return tmp_path


def test_production_app_serves_frontend_routes(frontend_dist: Path) -> None:
    client = TestClient(create_app(frontend_dist))

    for path in ("/", "/jobs", "/candidate", "/agent"):
        response = client.get(path)
        assert response.status_code == 200
        assert "ApplyPilot production" in response.text

    client.close()


def test_production_app_keeps_api_and_assets_available(frontend_dist: Path) -> None:
    client = TestClient(create_app(frontend_dist))

    health_response = client.get("/health")
    frontend_health_response = client.get("/api/health")
    asset_response = client.get("/assets/app.js")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert frontend_health_response.status_code == 200
    assert frontend_health_response.json() == {"status": "ok"}
    assert asset_response.status_code == 200
    assert "ApplyPilot" in asset_response.text
    client.close()


def test_production_app_namespaces_api_routes(frontend_dist: Path) -> None:
    application = create_app(frontend_dist)
    documented_paths = application.openapi()["paths"]

    assert "/api/jobs" in documented_paths
    assert "/api/profiles" in documented_paths
    assert "/jobs" not in documented_paths


def test_production_app_rejects_unknown_frontend_route(frontend_dist: Path) -> None:
    client = TestClient(create_app(frontend_dist))

    response = client.get("/unknown-route")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}
    client.close()


def test_production_app_fails_fast_for_incomplete_build(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="Frontend build is incomplete"):
        create_app(tmp_path)
