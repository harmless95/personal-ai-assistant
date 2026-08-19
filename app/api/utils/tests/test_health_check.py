from fastapi.testclient import TestClient

from app.main import app

client_test = TestClient(app=app)


def test_health_check() -> None:
    response = client_test.get("/api/v1/utils/health-check")
    assert response.status_code == 200
    assert response.text == "true"
