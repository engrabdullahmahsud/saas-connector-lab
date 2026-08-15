from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_unique_user_data(prefix="user"):
    unique_id = uuid4().hex[:8]

    return {
        "username": f"{prefix}_{unique_id}",
        "email": f"{prefix}_{unique_id}@example.com",
        "password": "TestPassword123!",
    }


def login_user(user):
    response = client.post(
        "/auth/login",
        json={
            "username": user.username
            if hasattr(user, "username")
            else user["username"],
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_user(prefix="user"):
    user_data = create_unique_user_data(prefix)

    response = client.post(
        "/users/",
        json=user_data,
    )

    assert response.status_code == 201

    return response.json()


def test_create_user():
    user_data = create_unique_user_data()

    response = client.post(
        "/users/",
        json=user_data,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert "password_hash" not in data
    assert "id" in data


def test_duplicate_user():
    user_data = create_unique_user_data()

    first_response = client.post(
        "/users/",
        json=user_data,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/users/",
        json=user_data,
    )

    assert second_response.status_code == 409

    data = second_response.json()

    assert data["detail"] == "Username or email already exists"


def test_get_users(test_user):
    token = login_user(test_user)

    response = client.get(
        "/users/",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    user_ids = [user["id"] for user in data]

    assert test_user.id in user_ids


def test_get_users_unauthenticated():
    response = client.get("/users/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_update_user(test_user):
    token = login_user(test_user)

    update_data = {
        "username": f"updated_{uuid4().hex[:8]}",
        "email": f"updated_{uuid4().hex[:8]}@example.com",
    }

    response = client.put(
        f"/users/{test_user.id}",
        json=update_data,
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == test_user.id
    assert data["username"] == update_data["username"]
    assert data["email"] == update_data["email"]


def test_update_user_not_found(test_user):
    token = login_user(test_user)

    response = client.put(
        "/users/999999999",
        json={
            "username": "updated_user",
            "email": "updated@example.com",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_update_user_unauthenticated(test_user):
    response = client.put(
        f"/users/{test_user.id}",
        json={
            "username": "updated_user",
            "email": "updated@example.com",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_update_other_user_forbidden(test_user):
    other_user = create_user("other_user")

    token = login_user(test_user)

    response = client.put(
        f"/users/{other_user['id']}",
        json={
            "username": f"changed_{uuid4().hex[:8]}",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "You can only update your own account"
    )


def test_update_user_duplicate_username(test_user):
    second_user_data = create_unique_user_data("second_user")

    create_response = client.post(
        "/users/",
        json=second_user_data,
    )

    assert create_response.status_code == 201

    token = login_user(test_user)

    response = client.put(
        f"/users/{test_user.id}",
        json={
            "username": second_user_data["username"],
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 409

    data = response.json()

    assert data["detail"] == "Username or email already exists"


def test_delete_user(test_user):
    token = login_user(test_user)

    response = client.delete(
        f"/users/{test_user.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["detail"] == "User deleted successfully"


def test_delete_user_not_found(test_user):
    token = login_user(test_user)

    response = client.delete(
        "/users/999999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_delete_user_unauthenticated(test_user):
    response = client.delete(
        f"/users/{test_user.id}"
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_delete_other_user_forbidden(test_user):
    other_user = create_user("delete_other")

    token = login_user(test_user)

    response = client.delete(
        f"/users/{other_user['id']}",
        headers=auth_headers(token),
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "You can only delete your own account"
    )
