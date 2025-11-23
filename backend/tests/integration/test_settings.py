"""Integration tests for Settings API endpoints.

Note: Discord configuration (bot token, channel IDs) has been moved to
environment variables and is no longer part of the Settings API.
"""
from fastapi.testclient import TestClient


def test_get_settings_creates_default(async_authenticated_client: TestClient):
    """Test that GET /settings creates default settings if none exist."""
    response = async_authenticated_client.get("/settings")

    assert response.status_code == 200
    data = response.json()

    # Check default values (Discord config is now in env vars, not API)
    assert data["notification_time"] == "07:00"
    assert data["notification_timezone"] == "UTC"
    assert "id" in data


def test_update_settings(async_authenticated_client: TestClient):
    """Test updating settings with all fields."""
    update_data = {
        "notification_time": "08:30",
        "notification_timezone": "America/New_York",
    }

    response = async_authenticated_client.put("/settings", json=update_data)

    assert response.status_code == 200
    data = response.json()

    assert data["notification_time"] == "08:30"
    assert data["notification_timezone"] == "America/New_York"


def test_update_settings_partial(async_authenticated_client: TestClient):
    """Test partial update of settings."""
    # First create settings
    async_authenticated_client.put(
        "/settings",
        json={
            "notification_time": "07:00",
            "notification_timezone": "UTC",
        },
    )

    # Update only notification_time
    response = async_authenticated_client.put(
        "/settings",
        json={"notification_time": "09:00"},
    )

    assert response.status_code == 200
    data = response.json()

    # notification_time should be updated
    assert data["notification_time"] == "09:00"

    # notification_timezone should remain unchanged
    assert data["notification_timezone"] == "UTC"


def test_update_settings_timezone(async_authenticated_client: TestClient):
    """Test updating timezone setting."""
    # First create settings
    async_authenticated_client.put(
        "/settings",
        json={
            "notification_time": "07:00",
            "notification_timezone": "UTC",
        },
    )

    # Update timezone
    response = async_authenticated_client.put(
        "/settings",
        json={"notification_timezone": "Europe/London"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notification_timezone"] == "Europe/London"


def test_settings_requires_auth(async_client: TestClient):
    """Test that settings endpoints require authentication."""
    # GET without auth
    response = async_client.get("/settings")
    assert response.status_code == 401

    # PUT without auth
    response = async_client.put("/settings", json={"notification_time": "09:00"})
    assert response.status_code == 401
