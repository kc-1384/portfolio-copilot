# Tests for the /health endpoints.

from fastapi.testclient import TestClient

from app.core.db import ping_database
from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_database_ok() -> None:
    app.dependency_overrides[ping_database] = lambda: True
    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_ready_returns_503_when_database_is_down() -> None:
    app.dependency_overrides[ping_database] = lambda: False
    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["database"] == "unreachable"
