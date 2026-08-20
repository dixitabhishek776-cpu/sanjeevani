from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_idempotency_migration_is_head_candidate():
    migration = ROOT / "backend/alembic/versions/0006_idempotency.py"
    text = migration.read_text()
    assert 'revision = "0006_idempotency"' in text
    assert 'down_revision = "0005_memory_outbox"' in text
    assert 'uq_idempotency_user_key' in text
    assert 'response_encrypted' in text

def test_chat_requires_retry_safe_idempotency_support():
    text = (ROOT / "backend/app/routers/chat.py").read_text()
    assert 'Idempotency-Key' in text
    assert 'request_hash' in text
    assert '409' in text
    assert 'response_encrypted' in text

def test_staging_has_worker_and_healthchecks():
    text = (ROOT / "docker-compose.staging.yml").read_text()
    assert 'worker:' in text
    assert 'condition: service_healthy' in text
    assert 'healthcheck:' in text
