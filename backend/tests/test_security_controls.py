import os
from fastapi.testclient import TestClient
from app.main import app, metrics

def test_livez():
    with TestClient(app) as client:
        r = client.get('/livez')
        assert r.status_code == 200
        assert r.json()['status'] == 'ok'

def test_metrics_requires_token(monkeypatch):
    monkeypatch.setenv('SANJEEVANI_METRICS_TOKEN', 'test-metrics-token')
    with TestClient(app) as client:
        assert client.get('/metrics').status_code == 404
        r = client.get('/metrics', headers={'Authorization':'Bearer test-metrics-token'})
        assert r.status_code == 200
        assert 'sanjeevani_http_requests_total' in r.text

def test_security_headers_and_request_id():
    with TestClient(app) as client:
        r = client.get('/livez')
        assert r.headers['X-Content-Type-Options'] == 'nosniff'
        assert r.headers['X-Frame-Options'] == 'DENY'
        assert r.headers['X-Request-ID']

def test_metrics_labels_are_low_cardinality():
    # Regression guard: the implementation must not include query strings or user IDs in labels.
    text = metrics.prometheus()
    assert 'user_id=' not in text
    assert '?token=' not in text
