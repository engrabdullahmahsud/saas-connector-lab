from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_unique_user_data(prefix="member"):
    unique_id = uuid4().hex[:8]

    return {
        "username": f"{prefix}_{unique_id}",
        "email": f"{prefix}_{unique_id}@example.com",
        "password": "TestPassword123!",
    }


def create_user(prefix="member"):
    response = client.post(
        "/users/",
        json=create_unique_user_data(prefix),
    )

    assert response.status_code == 201

    return response.json()


def login_user(user):
    response = client.post(
        "/auth/login",
        json={
            "username": (
                user.username
                if hasattr(user, "username")
                else user["username"]
            ),
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_join_channel(test_user, test_channel):
    token = login_user(test_user)

    response = client.post(
        f"/channel-members/{test_channel.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == test_user.id
    assert data["channel_id"] == test_channel.id
    assert "id" in data


def test_duplicate_membership(test_user, test_channel):
    token = login_user(test_user)

    first_response = client.post(
        f"/channel-members/{test_channel.id}",
        headers=auth_headers(token),
    )

    assert first_response.status_code in (201, 409)

    second_response = client.post(
        f"/channel-members/{test_channel.id}",
        headers=auth_headers(token),
    )

    assert second_response.status_code == 409

    assert (
        second_response.json()["detail"]
        == "User is already a member of this channel"
    )


def test_join_channel_with_invalid_channel(test_user):
    token = login_user(test_user)

    response = client.post(
        "/channel-members/999999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Channel not found"


def test_join_channel_unauthenticated(test_channel):
    response = client.post(
        f"/channel-members/{test_channel.id}",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_channel_members(test_user, test_channel):
    token = login_user(test_user)

    join_response = client.post(
        f"/channel-members/{test_channel.id}",
        headers=auth_headers(token),
    )

    assert join_response.status_code in (201, 409)

    response = client.get(
        f"/channel-members/channel/{test_channel.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    member_user_ids = [
        membership["user_id"]
        for membership in data
    ]

    assert test_user.id in member_user_ids


def test_non_member_cannot_get_channel_members(test_channel):
    non_member = create_user("non_member")
    token = login_user(non_member)

    response = client.get(
        f"/channel-members/channel/{test_channel.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "User is not a member of this channel"
    )


def test_leave_channel(test_user, test_channel):
    token = login_user(test_user)

    join_response = client.post(
        f"/channel-members/{test_channel.id}",
        headers=auth_headers(token),
    )

    assert join_response.status_code in (201, 409)

    response = client.delete(
        f"/channel-members/{test_channel.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Left channel successfully"

    members_response = client.get(
        f"/channel-members/channel/{test_channel.id}",
        headers=auth_headers(token),
    )

    assert members_response.status_code == 403


def test_non_member_cannot_leave_channel(test_user, test_channel):
    token = login_user(test_user)

    response = client.delete(
        f"/channel-members/{test_channel.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "User is not a member of this channel"
    )


def test_leave_channel_unauthenticated(test_channel):
    response = client.delete(
        f"/channel-members/{test_channel.id}",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_leave_invalid_channel(test_user):
    token = login_user(test_user)

    response = client.delete(
        "/channel-members/999999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Channel not found"
