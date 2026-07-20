from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_homepage_serves_firstaidops_interface() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "FirstAidOps" in response.text
    assert "Research guidance" in response.text


def test_health_reports_index_readiness() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert isinstance(response.json()["index_ready"], bool)


def test_research_rejects_short_question() -> None:
    response = client.post("/research", json={"question": "short"})
    assert response.status_code == 422


def test_research_rejects_overly_broad_question() -> None:
    response = client.post("/research", json={"question": "tell me everything"})
    assert response.status_code == 422
