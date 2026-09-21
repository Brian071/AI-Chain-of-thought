import pytest
from fastapi.testclient import TestClient
from app.main import app, model_manager

client = TestClient(app)

def test_homepage():
    response = client.get("/")
    assert response.status_code == 200
    assert "QwQ-32B CoT Offline AI Suite" in response.text

def test_model_status_unloaded():
    response = client.get("/api/model_status")
    assert response.status_code == 200
    assert response.json()["loaded"] is False

def test_load_mock_model_and_chat():
    load_resp = client.post("/api/load_model", json={
        "model_path": "test_model.gguf",
        "n_gpu_layers": 0,
        "n_batch": 256,
        "n_ubatch": 256,
        "use_mock": True
    })
    assert load_resp.status_code == 200
    assert load_resp.json()["status"] == "ok"

    # Verify model status loaded
    status_resp = client.get("/api/model_status")
    assert status_resp.json()["loaded"] is True

    # Test conversion mathml
    math_resp = client.post("/api/convert_mathml", json={"latex": "x^2 + y^2 = z^2"})
    assert math_resp.status_code == 200
    assert "x^2 + y^2 = z^2" in math_resp.json()["mathml"]

def test_chat_sessions():
    sessions_resp = client.get("/api/sessions")
    assert sessions_resp.status_code == 200
    assert "sessions" in sessions_resp.json()
