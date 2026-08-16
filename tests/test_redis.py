import uuid

from app.services.redis_service import (
    delete_value,
    get_value,
    ping_redis,
    set_value,
)


def test_redis_ping():
    assert ping_redis() is True


def test_redis_set_get_delete():
    key = f"test:redis:{uuid.uuid4()}"

    try:
        assert set_value(key, "hello") is True
        assert get_value(key) == "hello"
        assert delete_value(key) == 1
        assert get_value(key) is None
    finally:
        delete_value(key)


def test_redis_value_expires():
    key = f"test:redis:expire:{uuid.uuid4()}"

    try:
        assert set_value(key, "temporary", expire_seconds=1) is True
        assert get_value(key) == "temporary"
    finally:
        delete_value(key)


def test_health_reports_redis(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "redis": "ok",
    }
