"""
Integration tests for schedule API endpoints.

Tests cover:
- Schedule sequence CRUD operations
- Week template CRUD operations
- Week day assignment CRUD operations
- Reordering weeks
- Getting current week
- Soft delete (retirement) of weeks
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4


class TestScheduleSequences:
    """Test schedule sequence endpoints."""

    def test_create_schedule_sequence(self, async_authenticated_client: TestClient):
        """Test creating a new schedule sequence."""
        response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Weekly Meal Rotation",
                "advancement_day_of_week": 0,  # Sunday
                "advancement_time": "08:00",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Weekly Meal Rotation"
        assert data["advancement_day_of_week"] == 0
        assert data["advancement_time"] == "08:00"
        assert data["current_week_index"] == 0
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_schedule_invalid_time(self, async_authenticated_client: TestClient):
        """Test creating schedule with invalid time format."""
        response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Test Schedule",
                "advancement_day_of_week": 0,
                "advancement_time": "25:00",  # Invalid hour
            },
        )

        assert response.status_code == 422

    def test_list_schedules(self, async_authenticated_client: TestClient):
        """Test listing all schedule sequences."""
        # Create two schedules
        async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Schedule 1",
                "advancement_day_of_week": 0,
                "advancement_time": "08:00",
            },
        )
        async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Schedule 2",
                "advancement_day_of_week": 1,
                "advancement_time": "09:00",
            },
        )

        # List schedules
        response = async_authenticated_client.get("/schedules")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert all("name" in s for s in data)

    def test_get_schedule_by_id(self, async_authenticated_client: TestClient):
        """Test getting a single schedule by ID."""
        # Create schedule
        create_response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Test Schedule",
                "advancement_day_of_week": 2,
                "advancement_time": "10:00",
            },
        )
        sequence_id = create_response.json()["id"]

        # Get by ID
        response = async_authenticated_client.get(f"/schedules/{sequence_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sequence_id
        assert data["name"] == "Test Schedule"
        assert "week_mappings" in data  # Should include week mappings list

    def test_get_nonexistent_schedule(self, async_authenticated_client: TestClient):
        """Test getting a schedule that doesn't exist."""
        fake_id = str(uuid4())
        response = async_authenticated_client.get(f"/schedules/{fake_id}")
        assert response.status_code == 404

    def test_update_schedule(self, async_authenticated_client: TestClient):
        """Test updating a schedule sequence."""
        # Create schedule
        create_response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Original Name",
                "advancement_day_of_week": 0,
                "advancement_time": "08:00",
            },
        )
        sequence_id = create_response.json()["id"]

        # Update schedule
        response = async_authenticated_client.put(
            f"/schedules/{sequence_id}",
            json={
                "name": "Updated Name",
                "advancement_day_of_week": 3,
                "advancement_time": "12:00",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["advancement_day_of_week"] == 3
        assert data["advancement_time"] == "12:00"


class TestScheduleWeeks:
    """Test schedule week template endpoints."""

    @pytest.fixture
    def schedule_sequence(self, async_authenticated_client: TestClient):
        """Create a schedule sequence for testing."""
        response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Test Schedule",
                "advancement_day_of_week": 0,
                "advancement_time": "08:00",
            },
        )
        return response.json()

    def test_create_week_template(
        self, async_authenticated_client: TestClient, schedule_sequence: dict
    ):
        """Test creating a week template."""
        sequence_id = schedule_sequence["id"]

        # Create template
        template_response = async_authenticated_client.post(
            "/templates",
            json={"name": "Burger Week"},
        )
        assert template_response.status_code == 201
        template_data = template_response.json()
        assert template_data["name"] == "Burger Week"
        template_id = template_data["id"]

        # Associate with sequence
        response = async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template_id, "position": 1},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["week_template_id"] == template_id
        assert data["sequence_id"] == sequence_id
        assert data["position"] == 1

    def test_create_week_with_assignments(
        self,
        async_authenticated_client: TestClient,
        schedule_sequence: dict,
        async_test_user,
    ):
        """Test creating a week template with initial assignments."""
        sequence_id = schedule_sequence["id"]

        # Create template with assignments
        template_response = async_authenticated_client.post(
            "/templates",
            json={
                "name": "Taco Week",
                "assignments": [
                    {
                        "day_of_week": 1,  # Monday
                        "assigned_user_id": str(async_test_user.id),
                        "action": "cook",
                        "order": 0,
                    },
                    {
                        "day_of_week": 2,  # Tuesday
                        "assigned_user_id": str(async_test_user.id),
                        "action": "shop",
                        "order": 0,
                    },
                ],
            },
        )
        assert template_response.status_code == 201
        data = template_response.json()
        template_id = data["id"]

        # Associate with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template_id, "position": 1},
        )

        # Verify template has assignments
        assert data["name"] == "Taco Week"
        assert len(data["day_assignments"]) == 2
        assert data["day_assignments"][0]["action"] == "cook"
        assert data["day_assignments"][1]["action"] == "shop"

    def test_list_weeks_in_sequence(
        self, async_authenticated_client: TestClient, schedule_sequence: dict
    ):
        """Test listing all week templates in a sequence."""
        sequence_id = schedule_sequence["id"]

        # Create multiple templates
        template1_response = async_authenticated_client.post(
            "/templates",
            json={"name": "Week 1"},
        )
        template1_id = template1_response.json()["id"]

        template2_response = async_authenticated_client.post(
            "/templates",
            json={"name": "Week 2"},
        )
        template2_id = template2_response.json()["id"]

        # Associate with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template1_id, "position": 1},
        )
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template2_id, "position": 2},
        )

        # Get sequence detail which includes template mappings
        response = async_authenticated_client.get(f"/schedules/{sequence_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["week_mappings"]) == 2
        assert data["week_mappings"][0]["position"] == 1
        assert data["week_mappings"][1]["position"] == 2

    def test_get_week_by_id(
        self, async_authenticated_client: TestClient, schedule_sequence: dict
    ):
        """Test getting a specific week template."""
        sequence_id = schedule_sequence["id"]

        # Create template
        create_response = async_authenticated_client.post(
            "/templates",
            json={"name": "Pasta Week"},
        )
        template_id = create_response.json()["id"]

        # Associate with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template_id, "position": 1},
        )

        # Get template
        response = async_authenticated_client.get(f"/templates/{template_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["name"] == "Pasta Week"
        assert "day_assignments" in data

    def test_update_week(
        self, async_authenticated_client: TestClient, schedule_sequence: dict
    ):
        """Test updating a week template."""
        sequence_id = schedule_sequence["id"]

        # Create template
        create_response = async_authenticated_client.post(
            "/templates",
            json={"name": "Original Theme"},
        )
        template_id = create_response.json()["id"]

        # Associate with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template_id, "position": 1},
        )

        # Update template
        response = async_authenticated_client.put(
            f"/templates/{template_id}",
            json={"name": "Updated Theme"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Theme"

    def test_retire_week(
        self, async_authenticated_client: TestClient, schedule_sequence: dict
    ):
        """Test soft deleting (retiring) a week template."""
        sequence_id = schedule_sequence["id"]

        # Create template
        create_response = async_authenticated_client.post(
            "/templates",
            json={"name": "To Be Retired"},
        )
        template_id = create_response.json()["id"]

        # Associate with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template_id, "position": 1},
        )

        # Retire template
        response = async_authenticated_client.delete(f"/templates/{template_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Template retired successfully"
        assert data["template_id"] == str(template_id)

        # Verify it's not in default template list
        list_response = async_authenticated_client.get("/templates")
        assert template_id not in [t["id"] for t in list_response.json()]

        # Verify it appears when including retired
        list_response = async_authenticated_client.get("/templates?include_retired=true")
        assert template_id in [t["id"] for t in list_response.json()]

    def test_reorder_weeks(
        self, async_authenticated_client: TestClient, schedule_sequence: dict
    ):
        """Test reordering week templates in a sequence."""
        sequence_id = schedule_sequence["id"]

        # Create three templates
        template1 = async_authenticated_client.post(
            "/templates",
            json={"name": "Week 1"},
        ).json()
        template2 = async_authenticated_client.post(
            "/templates",
            json={"name": "Week 2"},
        ).json()
        template3 = async_authenticated_client.post(
            "/templates",
            json={"name": "Week 3"},
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

        # Reorder: swap template 1 and template 3
        response = async_authenticated_client.put(
            f"/schedules/{sequence_id}/templates/reorder",
            json={"template_ids": [template3["id"], template2["id"], template1["id"]]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Templates reordered successfully"

        # Verify new order by getting sequence detail
        sequence_response = async_authenticated_client.get(f"/schedules/{sequence_id}")
        sequence_data = sequence_response.json()
        assert sequence_data["week_mappings"][0]["week_template_id"] == template3["id"]
        assert sequence_data["week_mappings"][0]["position"] == 1
        assert sequence_data["week_mappings"][1]["week_template_id"] == template2["id"]
        assert sequence_data["week_mappings"][1]["position"] == 2
        assert sequence_data["week_mappings"][2]["week_template_id"] == template1["id"]
        assert sequence_data["week_mappings"][2]["position"] == 3

    def test_get_current_week(
        self, async_authenticated_client: TestClient, schedule_sequence: dict
    ):
        """Test getting the currently active week."""
        sequence_id = schedule_sequence["id"]

        # Create template
        template1 = async_authenticated_client.post(
            "/templates",
            json={"name": "Week 1"},
        ).json()

        # Associate with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template1["id"], "position": 1},
        )

        # Current template should be the first template (index 0)
        response = async_authenticated_client.get(
            f"/schedules/{sequence_id}/current-template"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template1["id"]
        assert data["name"] == "Week 1"


@pytest.mark.skip(reason="Assignment endpoints changed - assignments now managed through template CRUD")
class TestWeekDayAssignments:
    """Test week day assignment endpoints."""

    @pytest.fixture
    def schedule_with_week(self, async_authenticated_client: TestClient):
        """Create a schedule with a week template."""
        # Create sequence
        sequence_response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Test Schedule",
                "advancement_day_of_week": 0,
                "advancement_time": "08:00",
            },
        )
        sequence_id = sequence_response.json()["id"]

        # Create template
        template_response = async_authenticated_client.post(
            "/templates",
            json={"name": "Test Week"},
        )
        template = template_response.json()

        # Associate with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template["id"], "position": 1},
        )

        return {"sequence_id": sequence_id, "template": template}

    def test_create_assignment(
        self,
        async_authenticated_client: TestClient,
        schedule_with_week: dict,
        async_test_user,
    ):
        """Test creating a day assignment."""
        template_id = schedule_with_week["template"]["id"]

        response = async_authenticated_client.put(
            f"/templates/{template_id}/assignments/1",
            json={
                "assigned_user_id": str(async_test_user.id),
                "action": "cook",
                "position": 1,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["day_of_week"] == 1
        assert data["action"] == "cook"
        assert data["week_template_id"] == template_id

    def test_list_assignments(
        self,
        async_authenticated_client: TestClient,
        schedule_with_week: dict,
        async_test_user,
    ):
        """Test listing all assignments for a week."""
        template_id = schedule_with_week["template"]["id"]

        # Create multiple assignments
        for day in [1, 2, 3]:
            async_authenticated_client.put(
                f"/templates/{template_id}/assignments/{day}",
                json={
                    "assigned_user_id": str(async_test_user.id),
                    "action": "cook",
                    "position": 1,
                },
            )

        # Get template to verify assignments
        response = async_authenticated_client.get(f"/templates/{template_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["day_assignments"]) == 3
        assert data["day_assignments"][0]["day_of_week"] == 1
        assert data["day_assignments"][1]["day_of_week"] == 2
        assert data["day_assignments"][2]["day_of_week"] == 3

    def test_update_assignment(
        self,
        async_authenticated_client: TestClient,
        schedule_with_week: dict,
        async_test_user,
        async_second_test_user,
    ):
        """Test updating a day assignment."""
        template_id = schedule_with_week["template"]["id"]

        # Create assignment
        create_response = async_authenticated_client.put(
            f"/templates/{template_id}/assignments/1",
            json={
                "assigned_user_id": str(async_test_user.id),
                "action": "cook",
                "position": 1,
            },
        )
        assignment_id = create_response.json()["id"]

        # Update assignment via PUT (overwrite the day's assignment)
        response = async_authenticated_client.put(
            f"/templates/{template_id}/assignments/1",
            json={
                "action": "shop",
                "assigned_user_id": str(async_second_test_user.id),
                "position": 1,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "shop"
        assert data["assigned_user_id"] == str(async_second_test_user.id)

    def test_delete_assignment(
        self,
        async_authenticated_client: TestClient,
        schedule_with_week: dict,
        async_test_user,
    ):
        """Test deleting a day assignment."""
        template_id = schedule_with_week["template"]["id"]

        # Create assignment
        create_response = async_authenticated_client.put(
            f"/templates/{template_id}/assignments/1",
            json={
                "assigned_user_id": str(async_test_user.id),
                "action": "cook",
                "position": 1,
            },
        )
        assignment_id = create_response.json()["id"]

        # Delete assignment
        response = async_authenticated_client.delete(
            f"/templates/{template_id}/assignments/{assignment_id}"
        )

        assert response.status_code == 204

        # Verify it's gone
        template_response = async_authenticated_client.get(f"/templates/{template_id}")
        assert assignment_id not in [
            a["id"] for a in template_response.json()["day_assignments"]
        ]

    def test_multiple_assignments_same_day(
        self,
        async_authenticated_client: TestClient,
        schedule_with_week: dict,
        async_test_user,
        async_second_test_user,
    ):
        """Test creating multiple assignments for the same day with different orders."""
        template_id = schedule_with_week["template"]["id"]

        # Create two assignments for Monday
        async_authenticated_client.put(
            f"/templates/{template_id}/assignments/1",
            json={
                "assigned_user_id": str(async_test_user.id),
                "action": "cook",
                "position": 1,
            },
        )
        async_authenticated_client.put(
            f"/templates/{template_id}/assignments/1",
            json={
                "assigned_user_id": str(async_second_test_user.id),
                "action": "shop",
                "position": 2,
            },
        )

        # Get template to check assignments
        response = async_authenticated_client.get(f"/templates/{template_id}")

        data = response.json()
        monday_assignments = [a for a in data["day_assignments"] if a["day_of_week"] == 1]
        assert len(monday_assignments) == 2
        assert monday_assignments[0]["position"] == 0
        assert monday_assignments[0]["action"] == "cook"
        assert monday_assignments[1]["position"] == 1
        assert monday_assignments[1]["action"] == "shop"
