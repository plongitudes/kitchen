"""
Integration tests for prep step autocomplete functionality.

Tests cover:
- Fetching existing prep steps for autocomplete
- Fuzzy matching prep step descriptions
- Creating ingredients with auto-linked prep steps
- Unlinking and relinking prep steps
"""

import pytest
from fastapi.testclient import TestClient


class TestPrepStepAutocomplete:
    """Test prep step autocomplete API."""

    @pytest.fixture
    def recipe_with_prep_steps(self, async_authenticated_client: TestClient):
        """Create a recipe with multiple prep steps for autocomplete testing."""
        response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Test Recipe for Autocomplete",
                "recipe_type": "dinner",
                "ingredients": [
                    {
                        "ingredient_name": "Onion",
                        "quantity": 1,
                        "unit": "whole",
                        "order": 0,
                    },
                    {
                        "ingredient_name": "Carrot",
                        "quantity": 2,
                        "unit": "whole",
                        "order": 1,
                    },
                    {
                        "ingredient_name": "Celery",
                        "quantity": 3,
                        "unit": "count",
                        "order": 2,
                    },
                ],
                "instructions": [],
                "prep_steps": [
                    {
                        "description": "dice into 1-inch cubes",
                        "order": 0,
                        "ingredient_orders": [0, 1],  # Onion and Carrot
                    },
                    {
                        "description": "slice thinly",
                        "order": 1,
                        "ingredient_orders": [2],  # Celery
                    },
                ],
            },
        )
        assert response.status_code == 201
        return response.json()

    def test_get_recipe_prep_steps_for_autocomplete(
        self,
        async_authenticated_client: TestClient,
        recipe_with_prep_steps,
    ):
        """Test fetching prep steps from a recipe for autocomplete."""
        recipe_id = recipe_with_prep_steps["id"]

        response = async_authenticated_client.get(f"/recipes/{recipe_id}/prep-steps")

        assert response.status_code == 200
        prep_steps = response.json()
        assert len(prep_steps) == 2

        # Check prep step structure for autocomplete
        prep_step_1 = next(ps for ps in prep_steps if ps["description"] == "dice into 1-inch cubes")
        assert prep_step_1["id"]
        assert prep_step_1["description"] == "dice into 1-inch cubes"
        assert len(prep_step_1["ingredient_ids"]) == 2  # Linked to Onion and Carrot

        prep_step_2 = next(ps for ps in prep_steps if ps["description"] == "slice thinly")
        assert prep_step_2["description"] == "slice thinly"
        assert len(prep_step_2["ingredient_ids"]) == 1  # Linked to Celery

    def test_create_ingredient_with_existing_prep_step_link(
        self,
        async_authenticated_client: TestClient,
        recipe_with_prep_steps,
    ):
        """Test adding a new ingredient and linking it to an existing prep step."""
        recipe_id = recipe_with_prep_steps["id"]

        # Get the "dice into 1-inch cubes" prep step ID
        prep_steps_response = async_authenticated_client.get(f"/recipes/{recipe_id}/prep-steps")
        dice_prep_step = next(
            ps for ps in prep_steps_response.json() if ps["description"] == "dice into 1-inch cubes"
        )
        dice_prep_step_id = dice_prep_step["id"]

        # Add a new ingredient (potato) linked to the existing dice prep step
        response = async_authenticated_client.post(
            f"/recipes/{recipe_id}/ingredients",
            json={
                "ingredient_name": "Potato",
                "quantity": 4,
                "unit": "whole",
                "order": 3,
                "prep_step_id": dice_prep_step_id,  # Link to existing prep step
            },
        )

        assert response.status_code == 201
        new_ingredient = response.json()
        assert new_ingredient["ingredient_name"] == "Potato"

        # Verify the prep step now includes the new ingredient
        updated_prep_steps = async_authenticated_client.get(f"/recipes/{recipe_id}/prep-steps")
        updated_dice_prep = next(
            ps for ps in updated_prep_steps.json() if ps["id"] == dice_prep_step_id
        )
        assert len(updated_dice_prep["ingredient_ids"]) == 3  # Onion, Carrot, Potato

    def test_create_ingredient_with_new_prep_step(
        self,
        async_authenticated_client: TestClient,
        recipe_with_prep_steps,
    ):
        """Test creating a new prep step when adding an ingredient with unique prep."""
        recipe_id = recipe_with_prep_steps["id"]

        # Add ingredient with new prep step description
        response = async_authenticated_client.post(
            f"/recipes/{recipe_id}/ingredients",
            json={
                "ingredient_name": "Garlic",
                "quantity": 3,
                "unit": "clove",
                "order": 4,
                "prep_step_description": "mince finely",  # New prep step
            },
        )

        assert response.status_code == 201
        new_ingredient = response.json()
        assert new_ingredient["ingredient_name"] == "Garlic"

        # Verify a new prep step was created
        prep_steps = async_authenticated_client.get(f"/recipes/{recipe_id}/prep-steps").json()
        assert len(prep_steps) == 3  # Original 2 + new one

        mince_prep = next(ps for ps in prep_steps if ps["description"] == "mince finely")
        assert mince_prep
        assert len(mince_prep["ingredient_ids"]) == 1  # Only linked to Garlic

    def test_unlink_ingredient_from_prep_step(
        self,
        async_authenticated_client: TestClient,
        recipe_with_prep_steps,
    ):
        """Test unlinking an ingredient from its prep step."""
        recipe_id = recipe_with_prep_steps["id"]
        recipe = recipe_with_prep_steps

        # Get the first ingredient (Onion) that's linked to "dice into 1-inch cubes"
        onion_ingredient = recipe["ingredients"][0]
        onion_id = onion_ingredient["id"]

        # Unlink by setting prep_step_id to null
        response = async_authenticated_client.patch(
            f"/recipes/{recipe_id}/ingredients/{onion_id}",
            json={"prep_step_id": None},
        )

        assert response.status_code == 200

        # Verify the prep step now only includes Carrot
        prep_steps = async_authenticated_client.get(f"/recipes/{recipe_id}/prep-steps").json()
        dice_prep = next(ps for ps in prep_steps if ps["description"] == "dice into 1-inch cubes")
        assert len(dice_prep["ingredient_ids"]) == 1  # Only Carrot now

    def test_delete_prep_step_when_last_ingredient_unlinked(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test that prep steps are deleted when the last linked ingredient is removed."""
        # Create a recipe with one ingredient and one prep step
        create_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Test Orphaned Prep Step",
                "recipe_type": "dinner",
                "ingredients": [
                    {
                        "ingredient_name": "Tomato",
                        "quantity": 1,
                        "unit": "whole",
                        "order": 0,
                    },
                ],
                "instructions": [],
                "prep_steps": [
                    {
                        "description": "quarter",
                        "order": 0,
                        "ingredient_orders": [0],
                    },
                ],
            },
        )
        recipe = create_response.json()
        recipe_id = recipe["id"]
        tomato_id = recipe["ingredients"][0]["id"]

        # Unlink the only ingredient
        async_authenticated_client.patch(
            f"/recipes/{recipe_id}/ingredients/{tomato_id}",
            json={"prep_step_id": None},
        )

        # Verify the prep step was automatically deleted (orphaned)
        prep_steps = async_authenticated_client.get(f"/recipes/{recipe_id}/prep-steps").json()
        assert len(prep_steps) == 0  # Prep step should be gone

    def test_change_ingredient_prep_step_link(
        self,
        async_authenticated_client: TestClient,
        recipe_with_prep_steps,
    ):
        """Test changing an ingredient's prep step from one to another."""
        recipe_id = recipe_with_prep_steps["id"]
        recipe = recipe_with_prep_steps

        # Get Celery (linked to "slice thinly")
        celery_ingredient = recipe["ingredients"][2]
        celery_id = celery_ingredient["id"]

        # Get "dice into 1-inch cubes" prep step
        prep_steps = async_authenticated_client.get(f"/recipes/{recipe_id}/prep-steps").json()
        dice_prep_id = next(
            ps["id"] for ps in prep_steps if ps["description"] == "dice into 1-inch cubes"
        )

        # Change Celery from "slice thinly" to "dice into 1-inch cubes"
        response = async_authenticated_client.patch(
            f"/recipes/{recipe_id}/ingredients/{celery_id}",
            json={"prep_step_id": dice_prep_id},
        )

        assert response.status_code == 200

        # Verify "dice" prep now includes Celery
        updated_prep_steps = async_authenticated_client.get(
            f"/recipes/{recipe_id}/prep-steps"
        ).json()
        dice_prep = next(ps for ps in updated_prep_steps if ps["id"] == dice_prep_id)
        assert len(dice_prep["ingredient_ids"]) == 3  # Onion, Carrot, Celery

        # Verify "slice thinly" prep was deleted (orphaned)
        slice_preps = [ps for ps in updated_prep_steps if ps["description"] == "slice thinly"]
        assert len(slice_preps) == 0
