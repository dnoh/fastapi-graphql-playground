"""The liveness probe.

Deliberately not a GraphQL field: a health check that needs the GraphQL layer
to work cannot tell you the GraphQL layer is broken. It also touches no
database, so it stays honest about what it claims (the process is up).
"""

from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_ok() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
