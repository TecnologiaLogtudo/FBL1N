from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_health_endpoints() -> None:
    app = create_app()
    client = TestClient(app)

    live = client.get("/health/live")
    ready = client.get("/health/ready")

    assert live.status_code == 200
    assert ready.status_code == 200
    assert live.json()["status"] == "ok"
    assert ready.json()["status"] == "ready"
