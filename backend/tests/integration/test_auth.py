"""Integration tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
def test_register_new_user(async_client: TestClient):
    """Test user registration creates a new user."""
    response = async_client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "password": "securepass123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data
    assert "password_hash" not in data  # Should not expose password


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
def test_register_duplicate_username(async_client: TestClient, async_test_user):
    """Test that registering with existing username fails."""
    response = async_client.post(
        "/auth/register",
        json={
            "username": async_test_user.username,
            "password": "anotherpass123",
        },
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
def test_login_success(async_client: TestClient, async_test_user):
    """Test successful login returns access token."""
    response = async_client.post(
        "/auth/login",
        data={
            "username": async_test_user.username,
            "password": "testpass123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
def test_login_wrong_password(async_client: TestClient, async_test_user):
    """Test login with wrong password fails."""
    response = async_client.post(
        "/auth/login",
        data={
            "username": async_test_user.username,
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
def test_login_nonexistent_user(async_client: TestClient):
    """Test login with nonexistent username fails."""
    response = async_client.post(
        "/auth/login",
        data={
            "username": "nonexistent",
            "password": "anypassword",
        },
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
def test_token_contains_user_info(async_authenticated_client: TestClient, async_test_user):
    """Test that JWT token can be used to authenticate requests."""
    # async_authenticated_client already has authentication set up
    # Use token to access protected endpoint
    response = async_authenticated_client.get("/me")

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == async_test_user.username
