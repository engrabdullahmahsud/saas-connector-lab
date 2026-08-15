from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_unique_user_data(prefix="message_user"):
    unique_id = uuid4().hex[:8]

    return {
        "username": f"{prefix}_{unique_id}",
        "email": f"{prefix}_{unique_id}@example.com",
        "password": "TestPassword123!",
    }


def create_user(prefix="message_user"):
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
            "username": user["username"],
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
            "name": f"message-channel-{uuid4().hex[:8]}",
            "description": "Message test channel",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    return response.json()


def join_channel(user, channel):
    token = login_user(user)

    response = client.post(
        f"/channel-members/{channel['id']}",
        headers=auth_headers(token),
    )

    assert response.status_code in (201, 409)

    return response


def create_message(user, channel, content):
    join_channel(user, channel)

    token = login_user(user)

    response = client.post(
        f"/channels/{channel['id']}/messages",
        json={
            "content": content,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    return response.json()


def test_send_message():
    user = create_user()
    channel = create_channel(user)

    data = create_message(
        user,
        channel,
        "Deployment completed successfully.",
    )

    assert data["content"] == "Deployment completed successfully."
    assert data["user_id"] == user["id"]
    assert data["channel_id"] == channel["id"]
    assert "id" in data
    assert "created_at" in data


def test_get_messages():
    user = create_user()
    channel = create_channel(user)

    join_channel(user, channel)

    token = login_user(user)

    first_response = client.post(
        f"/channels/{channel['id']}/messages",
        json={"content": "First message"},
        headers=auth_headers(token),
    )

    second_response = client.post(
        f"/channels/{channel['id']}/messages",
        json={"content": "Second message"},
        headers=auth_headers(token),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(
        f"/channels/{channel['id']}/messages",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    messages = response.json()

    assert len(messages) == 2
    assert messages[0]["content"] == "First message"
    assert messages[1]["content"] == "Second message"


def test_unauthenticated_send_message():
    user = create_user()
    channel = create_channel(user)

    join_channel(user, channel)

    response = client.post(
        f"/channels/{channel['id']}/messages",
        json={
            "content": "This should fail.",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_non_member_cannot_send_message():
    owner = create_user("channel_owner")
    non_member = create_user("non_member")

    channel = create_channel(owner)

    token = login_user(non_member)

    response = client.post(
        f"/channels/{channel['id']}/messages",
        json={
            "content": "This should fail.",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "User is not a member of this channel"
    )


def test_non_member_cannot_read_messages():
    owner = create_user("reader_owner")
    non_member = create_user("reader_non_member")

    channel = create_channel(owner)

    token = login_user(non_member)

    response = client.get(
        f"/channels/{channel['id']}/messages",
        headers=auth_headers(token),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "User is not a member of this channel"
    )


def test_delete_own_message():
    user = create_user("message_owner")
    channel = create_channel(user)

    message = create_message(
        user,
        channel,
        "Message to delete",
    )

    token = login_user(user)

    response = client.delete(
        f"/channels/{channel['id']}/messages/{message['id']}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Message deleted successfully"

    response = client.get(
        f"/channels/{channel['id']}/messages",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_cannot_delete_another_users_message():
    owner = create_user("message_owner")
    other_user = create_user("message_other")

    channel = create_channel(owner)

    message = create_message(
        owner,
        channel,
        "Owner message",
    )

    join_channel(other_user, channel)

    token = login_user(other_user)

    response = client.delete(
        f"/channels/{channel['id']}/messages/{message['id']}",
        headers=auth_headers(token),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You can only delete your own messages"
    )


def test_unauthenticated_cannot_delete_message():
    user = create_user("delete_unauth")
    channel = create_channel(user)

    message = create_message(
        user,
        channel,
        "Protected message",
    )

    response = client.delete(
        f"/channels/{channel['id']}/messages/{message['id']}",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_non_member_cannot_delete_message():
    owner = create_user("delete_owner")
    non_member = create_user("delete_non_member")

    channel = create_channel(owner)

    message = create_message(
        owner,
        channel,
        "Protected message",
    )

    token = login_user(non_member)

    response = client.delete(
        f"/channels/{channel['id']}/messages/{message['id']}",
        headers=auth_headers(token),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "User is not a member of this channel"
    )


def test_delete_message_not_found():
    user = create_user("missing_message")
    channel = create_channel(user)

    join_channel(user, channel)

    token = login_user(user)

    response = client.delete(
        f"/channels/{channel['id']}/messages/999999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"
