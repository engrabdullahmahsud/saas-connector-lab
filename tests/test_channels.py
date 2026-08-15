from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_unique_user_data(prefix="channel_user"):
    unique_id = uuid4().hex[:8]

    return {
        "username": f"{prefix}_{unique_id}",
        "email": f"{prefix}_{unique_id}@example.com",
        "password": "TestPassword123!",
    }


def create_user(prefix="channel_user"):
    response = client.post(
        "/users/",
        json=create_unique_user_data(prefix),
    )

    assert response.status_code == 201

    return response.json()


def login_user(user):
    username = (
        user.username
        if hasattr(user, "username")
        else user["username"]
    )

    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_channel(user):
    token = login_user(user)

    response = client.post(
        "/channels/",
        json={
            "name": f"test-channel-{uuid4().hex[:8]}",
            "description": "Test channel",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    return response.json()


def test_create_channel(test_user):
    token = login_user(test_user)

    channel_data = {
        "name": f"test-channel-{uuid4().hex[:8]}",
        "description": "Test channel",
    }

    response = client.post(
        "/channels/",
        json=channel_data,
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == channel_data["name"]
    assert data["description"] == channel_data["description"]
    assert data["created_by"] == test_user.id
    assert "id" in data


def test_create_channel_unauthenticated():
    response = client.post(
        "/channels/",
        json={
            "name": f"test-channel-{uuid4().hex[:8]}",
            "description": "Test channel",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_create_channel_ignores_created_by():
    user = create_user()
    token = login_user(user)

    response = client.post(
        "/channels/",
        json={
            "name": f"test-channel-{uuid4().hex[:8]}",
            "description": "Test channel",
            "created_by": 999999999,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["created_by"] == user["id"]


def test_duplicate_channel(test_user):
    token = login_user(test_user)

    channel_data = {
        "name": f"test-channel-{uuid4().hex[:8]}",
        "description": "Test channel",
    }

    first_response = client.post(
        "/channels/",
        json=channel_data,
        headers=auth_headers(token),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/channels/",
        json=channel_data,
        headers=auth_headers(token),
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Channel already exists"


def test_get_channels(test_user, test_channel):
    token = login_user(test_user)

    response = client.get(
        "/channels/",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    channel_ids = [
        channel["id"]
        for channel in data
    ]

    assert test_channel.id in channel_ids


def test_get_channels_unauthenticated():
    response = client.get("/channels/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_delete_channel(test_channel, test_user):
    token = login_user(test_user)

    response = client.delete(
        f"/channels/{test_channel.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Channel deleted successfully"


def test_delete_channel_unauthenticated(test_channel):
    response = client.delete(
        f"/channels/{test_channel.id}"
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_delete_channel_not_found(test_user):
    token = login_user(test_user)

    response = client.delete(
        "/channels/999999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Channel not found"


def test_non_owner_cannot_delete_channel():
    owner = create_user("channel_owner")
    non_owner = create_user("channel_non_owner")

    channel = create_channel(owner)

    token = login_user(non_owner)

    response = client.delete(
        f"/channels/{channel['id']}",
        headers=auth_headers(token),
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "Only the channel owner can delete this channel"
    )
