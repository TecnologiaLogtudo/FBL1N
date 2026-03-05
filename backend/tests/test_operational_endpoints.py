from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_metrics_endpoint_returns_shape() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()

    assert "total_jobs" in data
    assert "active_jobs" in data
    assert "completed_jobs" in data
    assert "failed_jobs" in data
    assert "expired_jobs" in data
    assert "avg_duration_seconds" in data
    assert "success_rate" in data


def test_history_endpoint_empty_initially() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/process/history")
    assert response.status_code == 200
    assert response.json() == []
