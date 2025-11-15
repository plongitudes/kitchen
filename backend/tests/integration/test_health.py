"""Integration tests for health check and basic endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
def test_health_check(client: TestClient):
    """Test the /health endpoint returns healthy status."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "environment" in data


@pytest.mark.integration
@pytest.mark.api
def test_root_endpoint(client: TestClient):
    """Test the root / endpoint returns welcome message."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"


@pytest.mark.integration
@pytest.mark.api
def test_protected_endpoint_without_auth(client: TestClient):
    """Test that protected endpoint requires authentication."""
    response = client.get("/me")

    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.auth
def test_protected_endpoint_with_auth(async_authenticated_client: TestClient, async_test_user):
    """Test that protected endpoint works with valid JWT token."""
    response = async_authenticated_client.get("/me")

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == async_test_user.username
    assert data["id"] == str(async_test_user.id)
    assert "created_at" in data
