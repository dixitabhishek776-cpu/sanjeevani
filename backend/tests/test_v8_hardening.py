from fastapi.testclient import TestClient
from app.main import app

def test_payload_limit(monkeypatch):
    monkeypatch.setattr("app.main.MAX_BODY_BYTES", 32)
    with TestClient(app) as client:
        r = client.post("/v1/auth/password-reset/request", json={"email":"a"*100})
        assert r.status_code == 413

def test_livez_is_dependency_free():
    with TestClient(app) as client:
        r = client.get("/livez")
        assert r.status_code == 200
