from fastapi.testclient import TestClient

from src.app.main import app

client = TestClient(app)


def test_get_frontend_root():
    """Verify that the frontend HTML view is served at '/'."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DTU Sentiment Demo" in response.text
    assert "window.DATASET =" in response.text


def test_post_sentiment_positive():
    """Verify sentiment calculation endpoint with positive feedback."""
    response = client.post("/v1/sentiment", json={"text": "Great course, learned a lot."})
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "label" in data
    assert data["score"] > 0
    assert data["label"] in ("positive", "really positive")


def test_post_sentiment_neutral_unknown():
    """Verify sentiment calculation endpoint with unrecognized tokens."""
    response = client.post("/v1/sentiment", json={"text": "xyzzy qwerty nonexistingtoken"})
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 0.0
    assert data["label"] == "neutral"


def test_get_metrics():
    """Verify operational metrics endpoint."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "success_requests" in data
    assert "failed_requests" in data


def test_batch_invalid_dataset():
    """Verify validation on batch evaluation endpoint when row length is not 2."""
    response = client.post(
        "/api/batch",
        json={"service_url": "http://localhost:8000", "dataset": [["only_one_element"]]},
    )
    assert response.status_code == 400
