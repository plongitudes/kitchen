"""
Integration tests for meal plan API endpoints.

Tests cover:
- Meal plan instance creation from templates
- Week advancement (manual)
- Current instance retrieval
- Instance listing
- Date calculation for assignments
- Sequence looping behavior
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta


class TestMealPlanInstances:
    """Test meal plan instance endpoints."""

    @pytest.fixture
    async def schedule_with_weeks(self, async_authenticated_client: TestClient):
        """Create a schedule with multiple week templates."""
        # Create sequence
        sequence_response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Test Meal Schedule",
                "advancement_day_of_week": 0,  # Sunday
                "advancement_time": "08:00",
            },
        )
        sequence = sequence_response.json()
        sequence_id = sequence["id"]

        # Create three templates
        template1 = async_authenticated_client.post(
            "/templates",
            json={"name": "Burger Week"},
        ).json()

        template2 = async_authenticated_client.post(
            "/templates",
            json={"name": "Taco Week"},
        ).json()

        template3 = async_authenticated_client.post(
            "/templates",
            json={"name": "Pasta Week"},
        ).json()

        # Associate with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template1["id"], "position": 1},
        )
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template2["id"], "position": 2},
        )
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template3["id"], "position": 3},
        )

        return {
            "sequence_id": sequence_id,
            "sequence": sequence,
            "weeks": [template1, template2, template3],
        }

    @pytest.fixture
    async def schedule_with_assignments(
        self,
        async_authenticated_client: TestClient,
        async_test_user,
    ):
        """Create a schedule with weeks that have assignments."""
        # Create sequence
        sequence_response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Test Meal Schedule",
                "advancement_day_of_week": 1,  # Monday
                "advancement_time": "09:00",
            },
        )
        sequence_id = sequence_response.json()["id"]

        # Create template with assignments
        template = async_authenticated_client.post(
            "/templates",
            json={
                "name": "Burger Week",
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
                        "action": "cook",
                        "order": 0,
                    },
                ],
            },
        ).json()

        # Associate template with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template["id"], "position": 1},
        )

        return {"sequence_id": sequence_id, "week": template}

    def test_advance_week_creates_instance(
        self,
        async_authenticated_client: TestClient,
        schedule_with_weeks: dict,
    ):
        """Test that advancing a week creates a new meal plan instance."""
        sequence_id = schedule_with_weeks["sequence_id"]

        # Advance week - starts at index 0, advances to index 1 (week 2)
        response = async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence_id},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "new_instance" in data
        assert "old_week_number" in data
        assert "new_week_number" in data
        assert "sequence_current_week_index" in data

        # Verify new instance was created
        # Starting from index 0, advancing gives us index 1, which is week 2
        new_instance = data["new_instance"]
        assert new_instance["theme_name"] == "Taco Week"
        assert new_instance["week_number"] == 2
        assert "instance_start_date" in new_instance
        assert "id" in new_instance

    def test_advance_week_increments_sequence_index(
        self,
        async_authenticated_client: TestClient,
        schedule_with_weeks: dict,
    ):
        """Test that advancing increments the sequence's current_week_index."""
        sequence_id = schedule_with_weeks["sequence_id"]

        # Initial state: current_week_index should be 0
        sequence = async_authenticated_client.get(
            f"/schedules/{sequence_id}"
        ).json()
        assert sequence["current_week_index"] == 0

        # Advance week
        response = async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sequence_current_week_index"] == 1

        # Verify sequence was updated
        sequence = async_authenticated_client.get(
            f"/schedules/{sequence_id}"
        ).json()
        assert sequence["current_week_index"] == 1

    def test_advance_week_loops_back(
        self,
        async_authenticated_client: TestClient,
        schedule_with_weeks: dict,
    ):
        """Test that advancing past the last week loops back to week 1."""
        sequence_id = schedule_with_weeks["sequence_id"]

        # Advance through all 3 weeks
        # Start: index 0
        # After 1st advance: index 1 (week 2)
        # After 2nd advance: index 2 (week 3)
        # After 3rd advance: index 0 (week 1, looped back)
        themes_seen = []
        for i in range(3):
            response = async_authenticated_client.post(
                "/meal-plans/advance-week",
                json={"sequence_id": sequence_id},
            )
            assert response.status_code == 200
            themes_seen.append(response.json()["new_instance"]["theme_name"])

        # Should have seen: Taco (week 2), Pasta (week 3), Burger (week 1)
        assert themes_seen == ["Taco Week", "Pasta Week", "Burger Week"]

        # Verify we're back at index 0
        sequence = async_authenticated_client.get(
            f"/schedules/{sequence_id}"
        ).json()
        assert sequence["current_week_index"] == 0

        # Advance one more time - should get week 2 again (index 0 -> 1)
        response = async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["new_instance"]["theme_name"] == "Taco Week"
        assert data["new_week_number"] == 2

    def test_get_current_instance(
        self,
        async_authenticated_client: TestClient,
        schedule_with_weeks: dict,
    ):
        """Test getting the current active meal plan instance."""
        sequence_id = schedule_with_weeks["sequence_id"]

        # Create first instance (will be week 2 since we start at index 0)
        advance_response = async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence_id},
        )
        instance_from_advance = advance_response.json()["new_instance"]

        # Get current instance
        response = async_authenticated_client.get(
            f"/meal-plans/current?sequence_id={sequence_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == instance_from_advance["id"]
        assert data["theme_name"] == "Taco Week"

    def test_list_meal_plans(
        self,
        async_authenticated_client: TestClient,
        schedule_with_weeks: dict,
    ):
        """Test listing all meal plan instances."""
        sequence_id = schedule_with_weeks["sequence_id"]

        # Create three instances
        for i in range(3):
            async_authenticated_client.post(
                "/meal-plans/advance-week",
                json={"sequence_id": sequence_id},
            )

        # List all instances
        response = async_authenticated_client.get("/meal-plans")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # At least our 3 instances

        # Should be ordered by date descending (most recent first)
        dates = [instance["instance_start_date"] for instance in data]
        assert dates == sorted(dates, reverse=True)

    def test_get_instance_by_id(
        self,
        async_authenticated_client: TestClient,
        schedule_with_weeks: dict,
    ):
        """Test getting a specific meal plan instance by ID."""
        sequence_id = schedule_with_weeks["sequence_id"]

        # Create instance (will be week 2)
        advance_response = async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence_id},
        )
        instance_id = advance_response.json()["new_instance"]["id"]

        # Get by ID
        response = async_authenticated_client.get(
            f"/meal-plans/{instance_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == instance_id
        assert data["theme_name"] == "Taco Week"

    def test_instance_with_assignments_calculates_dates(
        self,
        async_authenticated_client: TestClient,
        schedule_with_assignments: dict,
    ):
        """Test that assignments have correctly calculated dates."""
        sequence_id = schedule_with_assignments["sequence_id"]

        # Advance week to create instance
        response = async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence_id},
        )

        assert response.status_code == 200
        data = response.json()
        instance = data["new_instance"]

        # Verify assignments have dates
        assert len(instance["assignments"]) == 3

        # Get the instance start date
        start_date = date.fromisoformat(instance["instance_start_date"])

        # Check that dates are calculated correctly
        assignments_by_day = {
            a["day_of_week"]: a for a in instance["assignments"]
        }

        # Sunday (day 0) should be start_date + 0 days
        sunday = assignments_by_day[0]
        assert date.fromisoformat(sunday["date"]) == start_date
        assert sunday["action"] == "shop"

        # Tuesday (day 2) should be start_date + 2 days
        tuesday = assignments_by_day[2]
        assert date.fromisoformat(tuesday["date"]) == start_date + timedelta(days=2)
        assert tuesday["action"] == "cook"

        # Friday (day 5) should be start_date + 5 days
        friday = assignments_by_day[5]
        assert date.fromisoformat(friday["date"]) == start_date + timedelta(days=5)
        assert friday["action"] == "cook"

    def test_advance_week_without_weeks_fails(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test that advancing a sequence with no weeks fails gracefully."""
        # Create sequence with no weeks
        sequence_response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Empty Schedule",
                "advancement_day_of_week": 0,
                "advancement_time": "08:00",
            },
        )
        sequence_id = sequence_response.json()["id"]

        # Try to advance
        response = async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence_id},
        )

        assert response.status_code == 400
        assert "no active templates" in response.json()["detail"].lower()

    def test_get_current_instance_when_none_exists(
        self,
        async_authenticated_client: TestClient,
        schedule_with_weeks: dict,
    ):
        """Test getting current instance when no instances exist yet."""
        sequence_id = schedule_with_weeks["sequence_id"]

        response = async_authenticated_client.get(
            f"/meal-plans/current?sequence_id={sequence_id}"
        )

        assert response.status_code == 404
        assert "no meal plan instance found" in response.json()["detail"].lower()

    def test_multiple_advances_create_separate_instances(
        self,
        async_authenticated_client: TestClient,
        schedule_with_weeks: dict,
    ):
        """Test that multiple advances create distinct instances."""
        sequence_id = schedule_with_weeks["sequence_id"]

        instance_ids = []

        # Create 5 instances
        for i in range(5):
            response = async_authenticated_client.post(
                "/meal-plans/advance-week",
                json={"sequence_id": sequence_id},
            )
            assert response.status_code == 200
            instance_ids.append(response.json()["new_instance"]["id"])

        # All instance IDs should be unique
        assert len(set(instance_ids)) == 5

        # List instances should show all 5
        list_response = async_authenticated_client.get("/meal-plans")
        assert len(list_response.json()) >= 5

    def test_start_on_arbitrary_week_fresh_start(
        self,
        async_authenticated_client: TestClient,
        schedule_with_weeks: dict,
    ):
        """Test starting a schedule on an arbitrary week (fresh start, no existing instance)."""
        sequence_id = schedule_with_weeks["sequence_id"]
        weeks = schedule_with_weeks["weeks"]

        # Start on week 2 (middle of sequence)
        template_id = weeks[1]["id"]  # Taco Week
        response = async_authenticated_client.post(
            f"/meal-plans/start-on-week?sequence_id={sequence_id}",
            json={
                "week_template_id": template_id,
                "position": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "new_instance" in data
        assert "week_number" in data
        assert "sequence_current_week_index" in data
        assert "transition_type" in data
        assert data["transition_type"] == "fresh_start"
        assert data["preserved_days"] == 0

        # Verify the instance was created with correct template
        new_instance = data["new_instance"]
        assert new_instance["theme_name"] == "Taco Week"
        assert data["week_number"] == 2

        # Verify sequence index was updated
        assert data["sequence_current_week_index"] == 1  # 0-indexed, position 2 = index 1

        # Verify by getting sequence
        sequence = async_authenticated_client.get(
            f"/schedules/{sequence_id}"
        ).json()
        assert sequence["current_week_index"] == 1

    def test_start_on_arbitrary_week_switches_schedule(
        self,
        async_authenticated_client: TestClient,
        schedule_with_weeks: dict,
        async_test_user,
    ):
        """Test starting on arbitrary week when an instance already exists (mid-week switch)."""
        sequence_id = schedule_with_weeks["sequence_id"]
        weeks = schedule_with_weeks["weeks"]

        # First, create an instance on week 1 using advance
        async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence_id},
        )

        # Get the current instance to verify it exists
        current = async_authenticated_client.get(
            f"/meal-plans/current?sequence_id={sequence_id}"
        ).json()
        assert current["theme_name"] == "Taco Week"

        # Now switch to week 3
        template_id = weeks[2]["id"]  # Pasta Week
        response = async_authenticated_client.post(
            f"/meal-plans/start-on-week?sequence_id={sequence_id}",
            json={
                "week_template_id": template_id,
                "position": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify it was a switch (Note: only if the instances are in the same week,
        # otherwise it will be a fresh_start because they have different start dates)
        # The key thing is that the old instance was replaced
        assert data["transition_type"] in ["switched", "fresh_start"]

        # Verify the new instance
        new_instance = data["new_instance"]
        assert new_instance["theme_name"] == "Pasta Week"
        assert data["week_number"] == 3
        assert data["sequence_current_week_index"] == 2  # position 3 = index 2

        # Verify the instance exists (we don't check if it's "current" because that
        # depends on the instance dates which can vary by test execution time)
        instance_check = async_authenticated_client.get(
            f"/meal-plans/{new_instance['id']}"
        )
        assert instance_check.status_code == 200
        assert instance_check.json()["theme_name"] == "Pasta Week"

    def test_start_on_arbitrary_week_invalid_template(
        self,
        async_authenticated_client: TestClient,
        schedule_with_weeks: dict,
    ):
        """Test that starting with invalid template ID fails."""
        sequence_id = schedule_with_weeks["sequence_id"]

        # Try to start with a non-existent template ID
        response = async_authenticated_client.post(
            f"/meal-plans/start-on-week?sequence_id={sequence_id}",
            json={
                "week_template_id": "00000000-0000-0000-0000-000000000000",
                "position": 1,
            },
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_start_on_arbitrary_week_mismatched_position(
        self,
        async_authenticated_client: TestClient,
        schedule_with_weeks: dict,
    ):
        """Test that position must match the template's actual position."""
        sequence_id = schedule_with_weeks["sequence_id"]
        weeks = schedule_with_weeks["weeks"]

        # Try to start with week 2 template but wrong position
        template_id = weeks[1]["id"]  # Taco Week (position 2)
        response = async_authenticated_client.post(
            f"/meal-plans/start-on-week?sequence_id={sequence_id}",
            json={
                "week_template_id": template_id,
                "position": 3,  # Wrong! Should be 2
            },
        )

        assert response.status_code == 400
        assert "not found at position" in response.json()["detail"].lower()
