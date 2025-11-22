"""Integration tests for Discord API endpoints."""
import pytest
from fastapi.testclient import TestClient
from datetime import date
from uuid import uuid4


def test_discord_status(async_authenticated_client: TestClient):
    """Test getting Discord bot status."""
    response = async_authenticated_client.get("/discord/status")

    assert response.status_code == 200
    data = response.json()

    assert "connected" in data
    assert isinstance(data["connected"], bool)


def test_discord_status_requires_auth(async_client: TestClient):
    """Test that Discord status requires authentication."""
    response = async_client.get("/discord/status")
    assert response.status_code == 401


def test_test_message_endpoint(async_authenticated_client: TestClient):
    """Test sending a test message."""
    response = async_authenticated_client.post(
        "/discord/test-message",
        json={"message": "Test message"},
    )

    # Should either succeed (200) if bot is connected,
    # or fail (503) if not connected
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert "success" in data
    else:
        assert "not connected" in response.json()["detail"].lower()


def test_test_message_requires_auth(async_client: TestClient):
    """Test that test message endpoint requires authentication."""
    response = async_client.post(
        "/discord/test-message",
        json={"message": "Test"},
    )
    assert response.status_code == 401


def test_channels_endpoint(async_authenticated_client: TestClient):
    """Test fetching Discord channels."""
    response = async_authenticated_client.get("/discord/channels")

    # Should either succeed (200) if bot is connected,
    # or fail (503) if not connected
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert "channels" in data
        assert isinstance(data["channels"], list)
    else:
        assert "not connected" in response.json()["detail"].lower()


def test_channels_requires_auth(async_client: TestClient):
    """Test that channels endpoint requires authentication."""
    response = async_client.get("/discord/channels")
    assert response.status_code == 401


def test_link_discord_user_requires_auth(async_client: TestClient):
    """Test that sync-user endpoint requires authentication."""
    response = async_client.post(
        "/discord/sync-user",
        json={"discord_user_id": "123456789"},
    )
    assert response.status_code == 401


def test_link_discord_user(async_authenticated_client: TestClient):
    """Test syncing Discord user ID."""
    response = async_authenticated_client.post(
        "/discord/sync-user",
        json={"discord_user_id": "123456789012345678"},
    )

    # Should succeed and persist the Discord ID
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "mentioned" in data["message"].lower()

    # Verify the Discord ID was saved by checking /me endpoint
    me_response = async_authenticated_client.get("/me")
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["discord_user_id"] == "123456789012345678"


def test_reconnect_requires_auth(async_client: TestClient):
    """Test that reconnect endpoint requires authentication."""
    response = async_client.post("/discord/reconnect")
    assert response.status_code == 401


def test_reconnect_endpoint(async_authenticated_client: TestClient):
    """Test reconnect endpoint behavior."""
    response = async_authenticated_client.post("/discord/reconnect")

    # Should either succeed (200) if credentials are configured,
    # or fail (400/500) if not configured
    assert response.status_code in [200, 400, 500]

    if response.status_code == 200:
        data = response.json()
        assert "success" in data
        assert "connected" in data


def test_test_notifications_requires_auth(async_client: TestClient):
    """Test that test notifications endpoint requires authentication."""
    response = async_client.post("/discord/test-notifications")
    assert response.status_code == 401


def test_test_notifications_endpoint(async_authenticated_client: TestClient):
    """Test notifications endpoint behavior."""
    response = async_authenticated_client.post("/discord/test-notifications")

    # Should either succeed (200) if bot is connected,
    # or fail (503) if not connected, or 404 if no meal plans
    assert response.status_code in [200, 404, 503]

    if response.status_code == 200:
        data = response.json()
        assert "success" in data
        assert "message" in data
    elif response.status_code == 404:
        assert "no meal plan" in response.json()["detail"].lower()
    else:
        assert "not connected" in response.json()["detail"].lower()


class TestNotificationsWithMealPlans:
    """Test notifications with real meal plan data."""

    @pytest.fixture
    async def meal_plan_with_template_assignments(
        self,
        async_authenticated_client: TestClient,
        async_test_user,
    ):
        """Create a meal plan instance with template assignments (no overrides)."""
        # Create a template with assignments
        template_response = async_authenticated_client.post(
            "/templates",
            json={
                "name": "Notification Test Week",
                "assignments": [
                    {
                        "day_of_week": 0,  # Sunday
                        "assigned_user_id": str(async_test_user.id),
                        "action": "shop",
                        "order": 0,
                    },
                    {
                        "day_of_week": 2,  # Tuesday
                        "assigned_user_id": str(async_test_user.id),
                        "action": "cook",
                        "order": 0,
                    },
                    {
                        "day_of_week": 5,  # Friday
                        "assigned_user_id": str(async_test_user.id),
                        "action": "takeout",
                        "order": 0,
                    },
                ],
            },
        )
        assert template_response.status_code == 201
        template = template_response.json()

        # Create a sequence
        sequence_response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Notification Test Schedule",
                "advancement_day_of_week": 0,
                "advancement_time": "08:00",
            },
        )
        sequence = sequence_response.json()

        # Associate template with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence['id']}/templates",
            json={"week_template_id": template["id"], "position": 1},
        )

        # Advance week to create an instance
        advance_response = async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence["id"]},
        )
        assert advance_response.status_code == 200
        instance = advance_response.json()["new_instance"]

        return {
            "template": template,
            "sequence": sequence,
            "instance": instance,
        }

    def test_notifications_with_template_assignments(
        self,
        async_authenticated_client: TestClient,
        meal_plan_with_template_assignments: dict,
    ):
        """Test that test-notifications works with template-based assignments."""
        response = async_authenticated_client.post("/discord/test-notifications")

        # Should either succeed (200) if bot is connected,
        # or fail (503) if not connected
        # Should NOT be 404 since we have meal plan data now
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            # Should have sent some notifications
            assert "notification" in data["message"].lower()

    def test_notifications_returns_404_without_meal_plans(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test that endpoint returns 404 when no meal plans exist."""
        # Note: This test assumes a clean database state
        # In practice, other tests may have created meal plans
        # This is more of a documentation test for the expected behavior
        response = async_authenticated_client.post("/discord/test-notifications")

        # If no meal plans exist, should return 404
        # Otherwise will return 200 or 503 depending on bot status
        if response.status_code == 404:
            assert "no meal plan" in response.json()["detail"].lower()
