"""Integration tests for Settings API endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_get_settings_creates_default(async_authenticated_client: TestClient):
    """Test that GET /settings creates default settings if none exist."""
    response = async_authenticated_client.get("/settings")

    assert response.status_code == 200
    data = response.json()

    # Check default values
    assert data["notification_time"] == "07:00"
    assert data["notification_timezone"] == "UTC"
    assert data["discord_bot_token"] is None
    assert data["notification_channel_id"] is None
    assert data["test_channel_id"] is None


def test_update_settings(async_authenticated_client: TestClient):
    """Test updating settings with all fields."""
    update_data = {
        "discord_bot_token": "test-token-123",
        "notification_channel_id": "123456789",
        "test_channel_id": "987654321",
        "notification_time": "08:30",
        "notification_timezone": "America/New_York",
    }

    response = async_authenticated_client.put("/settings", json=update_data)

    assert response.status_code == 200
    data = response.json()

    assert data["discord_bot_token"] == "test-token-123"
    assert data["notification_channel_id"] == "123456789"
    assert data["test_channel_id"] == "987654321"
    assert data["notification_time"] == "08:30"
    assert data["notification_timezone"] == "America/New_York"


def test_update_settings_partial(async_authenticated_client: TestClient):
    """Test partial update of settings."""
    # First create settings with all fields
    async_authenticated_client.put(
        "/settings",
        json={
            "discord_bot_token": "original-token",
            "notification_channel_id": "111111",
            "test_channel_id": "222222",
            "notification_time": "07:00",
            "notification_timezone": "UTC",
        },
    )

    # Update only test_channel_id
    response = async_authenticated_client.put(
        "/settings",
        json={"test_channel_id": "333333"},
    )

    assert response.status_code == 200
    data = response.json()

    # Test channel should be updated
    assert data["test_channel_id"] == "333333"

    # Other fields should remain unchanged
    assert data["discord_bot_token"] == "original-token"
    assert data["notification_channel_id"] == "111111"
    assert data["notification_time"] == "07:00"


def test_update_settings_null_values(async_authenticated_client: TestClient):
    """Test setting fields to null."""
    # First create settings
    async_authenticated_client.put(
        "/settings",
        json={
            "discord_bot_token": "token",
            "notification_channel_id": "123",
            "test_channel_id": "456",
        },
    )

    # Clear test_channel_id
    response = async_authenticated_client.put(
        "/settings",
        json={"test_channel_id": None},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["test_channel_id"] is None


def test_settings_requires_auth(async_client: TestClient):
    """Test that settings endpoints require authentication."""
    # GET without auth
    response = async_client.get("/settings")
    assert response.status_code == 401

    # PUT without auth
    response = async_client.put("/settings", json={"notification_time": "09:00"})
    assert response.status_code == 401
