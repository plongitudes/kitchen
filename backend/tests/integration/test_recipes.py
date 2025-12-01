"""
Integration tests for recipe management API.

Tests cover:
- Recipe CRUD operations
- Ingredient management
- Instruction management
- Retirement validation
- Template usage checking
- Owner filtering
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime


class TestRecipeBasicOperations:
    """Test basic recipe CRUD operations."""

    def test_create_recipe(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test creating a recipe with ingredients and instructions."""
        response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Spaghetti Carbonara",
                "recipe_type": "dinner",
                "prep_time_minutes": 10,
                "cook_time_minutes": 20,
                "prep_notes": "Bring water to boil while preparing sauce",
                "source_url": "https://example.com/carbonara",
                "ingredients": [
                    {
                        "ingredient_name": "Spaghetti",
                        "quantity": 1,
                        "unit": "pound",
                        "order": 1,
                    },
                    {
                        "ingredient_name": "Eggs",
                        "quantity": 4,
                        "unit": "whole",
                        "order": 2,
                    },
                    {
                        "ingredient_name": "Parmesan",
                        "quantity": 1,
                        "unit": "cup",
                        "order": 3,
                        "prep_note": "finely grated",
                    },
                ],
                "instructions": [
                    {
                        "step_number": 1,
                        "description": "Boil pasta according to package directions",
                        "duration_minutes": 10,
                    },
                    {
                        "step_number": 2,
                        "description": "Whisk eggs and cheese together",
                        "duration_minutes": 2,
                    },
                    {
                        "step_number": 3,
                        "description": "Toss hot pasta with egg mixture",
                        "duration_minutes": 3,
                    },
                ],
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify recipe fields
        assert data["name"] == "Spaghetti Carbonara"
        assert data["recipe_type"] == "dinner"
        assert data["prep_time_minutes"] == 10
        assert data["cook_time_minutes"] == 20
        assert data["prep_notes"] == "Bring water to boil while preparing sauce"
        assert data["source_url"] == "https://example.com/carbonara"
        assert "id" in data
        assert "owner_id" in data
        assert data["retired_at"] is None

        # Verify ingredients
        assert len(data["ingredients"]) == 3
        assert data["ingredients"][0]["ingredient_name"] == "Spaghetti"
        assert data["ingredients"][0]["quantity"] == 1
        assert data["ingredients"][0]["unit"] == "pound"
        # Verify prep_note is present on Parmesan
        assert data["ingredients"][2]["ingredient_name"] == "Parmesan"
        assert data["ingredients"][2]["prep_note"] == "finely grated"

        # Verify instructions
        assert len(data["instructions"]) == 3
        assert data["instructions"][0]["step_number"] == 1
        assert data["instructions"][1]["step_number"] == 2
        assert data["instructions"][2]["step_number"] == 3

    def test_get_recipe_by_id(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test retrieving a recipe by ID."""
        # Create a recipe
        create_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Test Recipe",
                "recipe_type": "lunch",
                "cook_time_minutes": 15,
                "ingredients": [
                    {
                        "ingredient_name": "Test Ingredient",
                        "quantity": 1,
                        "unit": "cup",
                        "order": 1,
                    }
                ],
                "instructions": [
                    {"step_number": 1, "description": "Test step"}
                ],
            },
        )
        recipe_id = create_response.json()["id"]

        # Get the recipe
        response = async_authenticated_client.get(f"/recipes/{recipe_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == recipe_id
        assert data["name"] == "Test Recipe"
        assert len(data["ingredients"]) == 1
        assert len(data["instructions"]) == 1

    def test_list_recipes(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test listing all recipes."""
        # Create multiple recipes
        for i in range(3):
            async_authenticated_client.post(
                "/recipes",
                json={
                    "name": f"Recipe {i}",
                    "recipe_type": "dinner",
                    "cook_time_minutes": 20,
                    "ingredients": [],
                    "instructions": [],
                },
            )

        # List recipes
        response = async_authenticated_client.get("/recipes")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_update_recipe(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test updating a recipe."""
        # Create a recipe
        create_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Original Name",
                "recipe_type": "breakfast",
                "cook_time_minutes": 10,
                "ingredients": [],
                "instructions": [],
            },
        )
        recipe_id = create_response.json()["id"]

        # Update the recipe
        response = async_authenticated_client.put(
            f"/recipes/{recipe_id}",
            json={
                "name": "Updated Name",
                "prep_time_minutes": 5,
                "postmortem_notes": "This recipe is amazing!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["prep_time_minutes"] == 5
        assert data["postmortem_notes"] == "This recipe is amazing!"
        # Recipe type should remain unchanged
        assert data["recipe_type"] == "breakfast"
        assert data["cook_time_minutes"] == 10


class TestRecipeRetirement:
    """Test recipe retirement and validation."""

    def test_retire_recipe(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test soft-deleting a recipe."""
        # Create a recipe
        create_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "To Be Retired",
                "recipe_type": "dinner",
                "cook_time_minutes": 30,
                "ingredients": [],
                "instructions": [],
            },
        )
        recipe_id = create_response.json()["id"]

        # Retire the recipe
        response = async_authenticated_client.delete(f"/recipes/{recipe_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["retired_at"] is not None

        # Verify it doesn't appear in default list
        list_response = async_authenticated_client.get("/recipes")
        recipes = list_response.json()
        assert not any(r["id"] == recipe_id for r in recipes)

    def test_list_retired_recipes(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test listing retired recipes with include_retired flag."""
        # Create and retire a recipe
        create_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Retired Recipe",
                "recipe_type": "dinner",
                "cook_time_minutes": 20,
                "ingredients": [],
                "instructions": [],
            },
        )
        recipe_id = create_response.json()["id"]
        async_authenticated_client.delete(f"/recipes/{recipe_id}")

        # List with include_retired
        response = async_authenticated_client.get("/recipes?include_retired=true")

        assert response.status_code == 200
        recipes = response.json()
        assert any(r["id"] == recipe_id for r in recipes)

    def test_restore_recipe(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test restoring a retired recipe."""
        # Create and retire a recipe
        create_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "To Be Restored",
                "recipe_type": "lunch",
                "cook_time_minutes": 15,
                "ingredients": [],
                "instructions": [],
            },
        )
        recipe_id = create_response.json()["id"]
        async_authenticated_client.delete(f"/recipes/{recipe_id}")

        # Restore the recipe
        response = async_authenticated_client.post(f"/recipes/{recipe_id}/restore")

        assert response.status_code == 200
        data = response.json()
        assert data["retired_at"] is None

        # Verify it appears in default list again
        list_response = async_authenticated_client.get("/recipes")
        recipes = list_response.json()
        assert any(r["id"] == recipe_id for r in recipes)

    def test_cannot_retire_recipe_in_active_template(
        self,
        async_authenticated_client: TestClient,
        async_test_user,
    ):
        """Test that recipes used in active week templates cannot be retired."""
        # Create a recipe
        recipe_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Template Recipe",
                "recipe_type": "dinner",
                "cook_time_minutes": 30,
                "ingredients": [],
                "instructions": [],
            },
        )
        recipe_id = recipe_response.json()["id"]

        # Create a schedule sequence
        sequence_response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Test Schedule",
                "advancement_day_of_week": 0,
                "advancement_time": "08:00",
            },
        )
        sequence_id = sequence_response.json()["id"]

        # Create a template with the recipe in an assignment
        template_response = async_authenticated_client.post(
            "/templates",
            json={
                "name": "Test Week",
                "assignments": [
                    {
                        "day_of_week": 1,
                        "assigned_user_id": str(async_test_user.id),
                        "action": "cook",
                        "recipe_id": recipe_id,
                        "order": 0,
                    }
                ],
            },
        )
        template_id = template_response.json()["id"]

        # Associate template with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template_id, "position": 1},
        )

        # Try to retire the recipe
        response = async_authenticated_client.delete(f"/recipes/{recipe_id}")

        assert response.status_code == 400
        assert "used in active week templates" in response.json()["detail"].lower()


class TestRecipeIngredients:
    """Test ingredient management."""

    @pytest.fixture
    def recipe_with_ingredients(self, async_authenticated_client: TestClient):
        """Create a recipe with ingredients for testing."""
        response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Test Recipe",
                "recipe_type": "dinner",
                "cook_time_minutes": 20,
                "ingredients": [
                    {
                        "ingredient_name": "Ingredient 1",
                        "quantity": 1,
                        "unit": "cup",
                        "order": 1,
                    },
                    {
                        "ingredient_name": "Ingredient 2",
                        "quantity": 2,
                        "unit": "tablespoon",
                        "order": 2,
                    },
                ],
                "instructions": [],
            },
        )
        return response.json()

    def test_list_ingredients(
        self,
        async_authenticated_client: TestClient,
        recipe_with_ingredients: dict,
    ):
        """Test listing recipe ingredients."""
        recipe_id = recipe_with_ingredients["id"]

        response = async_authenticated_client.get(f"/recipes/{recipe_id}/ingredients")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["ingredient_name"] == "Ingredient 1"
        assert data[1]["ingredient_name"] == "Ingredient 2"

    def test_add_ingredient(
        self,
        async_authenticated_client: TestClient,
        recipe_with_ingredients: dict,
    ):
        """Test adding an ingredient to a recipe."""
        recipe_id = recipe_with_ingredients["id"]

        response = async_authenticated_client.post(
            f"/recipes/{recipe_id}/ingredients",
            json={
                "ingredient_name": "New Ingredient",
                "quantity": 3,
                "unit": "teaspoon",
                "order": 3,
                "prep_note": "finely chopped",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["ingredient_name"] == "New Ingredient"
        assert data["quantity"] == 3
        assert data["unit"] == "teaspoon"
        assert data["prep_note"] == "finely chopped"

        # Verify it appears in the list
        list_response = async_authenticated_client.get(
            f"/recipes/{recipe_id}/ingredients"
        )
        ingredients = list_response.json()
        assert len(ingredients) == 3

    def test_update_ingredient(
        self,
        async_authenticated_client: TestClient,
        recipe_with_ingredients: dict,
    ):
        """Test updating an ingredient."""
        recipe_id = recipe_with_ingredients["id"]
        ingredient_id = recipe_with_ingredients["ingredients"][0]["id"]

        response = async_authenticated_client.put(
            f"/recipes/{recipe_id}/ingredients/{ingredient_id}",
            json={
                "quantity": 2.5,
                "unit": "ounce",
                "prep_note": "diced into 1-inch cubes",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 2.5
        assert data["unit"] == "ounce"
        assert data["prep_note"] == "diced into 1-inch cubes"
        # Name should remain unchanged
        assert data["ingredient_name"] == "Ingredient 1"

    def test_delete_ingredient(
        self,
        async_authenticated_client: TestClient,
        recipe_with_ingredients: dict,
    ):
        """Test deleting an ingredient."""
        recipe_id = recipe_with_ingredients["id"]
        ingredient_id = recipe_with_ingredients["ingredients"][0]["id"]

        response = async_authenticated_client.delete(
            f"/recipes/{recipe_id}/ingredients/{ingredient_id}"
        )

        assert response.status_code == 204

        # Verify it's removed from the list
        list_response = async_authenticated_client.get(
            f"/recipes/{recipe_id}/ingredients"
        )
        ingredients = list_response.json()
        assert len(ingredients) == 1
        assert ingredients[0]["id"] != ingredient_id


class TestRecipeInstructions:
    """Test instruction management."""

    @pytest.fixture
    def recipe_with_instructions(self, async_authenticated_client: TestClient):
        """Create a recipe with instructions for testing."""
        response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Test Recipe",
                "recipe_type": "dinner",
                "cook_time_minutes": 20,
                "ingredients": [],
                "instructions": [
                    {
                        "step_number": 1,
                        "description": "Step 1",
                        "duration_minutes": 5,
                    },
                    {
                        "step_number": 2,
                        "description": "Step 2",
                        "duration_minutes": 10,
                    },
                ],
            },
        )
        return response.json()

    def test_list_instructions(
        self,
        async_authenticated_client: TestClient,
        recipe_with_instructions: dict,
    ):
        """Test listing recipe instructions."""
        recipe_id = recipe_with_instructions["id"]

        response = async_authenticated_client.get(f"/recipes/{recipe_id}/instructions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["step_number"] == 1
        assert data[1]["step_number"] == 2

    def test_add_instruction(
        self,
        async_authenticated_client: TestClient,
        recipe_with_instructions: dict,
    ):
        """Test adding an instruction to a recipe."""
        recipe_id = recipe_with_instructions["id"]

        response = async_authenticated_client.post(
            f"/recipes/{recipe_id}/instructions",
            json={
                "step_number": 3,
                "description": "Step 3",
                "duration_minutes": 5,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["step_number"] == 3
        assert data["description"] == "Step 3"

        # Verify it appears in the list
        list_response = async_authenticated_client.get(
            f"/recipes/{recipe_id}/instructions"
        )
        instructions = list_response.json()
        assert len(instructions) == 3

    def test_update_instruction(
        self,
        async_authenticated_client: TestClient,
        recipe_with_instructions: dict,
    ):
        """Test updating an instruction."""
        recipe_id = recipe_with_instructions["id"]
        instruction_id = recipe_with_instructions["instructions"][0]["id"]

        response = async_authenticated_client.put(
            f"/recipes/{recipe_id}/instructions/{instruction_id}",
            json={
                "description": "Updated step 1",
                "duration_minutes": 7,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated step 1"
        assert data["duration_minutes"] == 7
        # Step number should remain unchanged
        assert data["step_number"] == 1

    def test_delete_instruction(
        self,
        async_authenticated_client: TestClient,
        recipe_with_instructions: dict,
    ):
        """Test deleting an instruction."""
        recipe_id = recipe_with_instructions["id"]
        instruction_id = recipe_with_instructions["instructions"][0]["id"]

        response = async_authenticated_client.delete(
            f"/recipes/{recipe_id}/instructions/{instruction_id}"
        )

        assert response.status_code == 204

        # Verify it's removed from the list
        list_response = async_authenticated_client.get(
            f"/recipes/{recipe_id}/instructions"
        )
        instructions = list_response.json()
        assert len(instructions) == 1
        assert instructions[0]["id"] != instruction_id


class TestRecipePrepSteps:
    """Test prep step management."""

    @pytest.fixture
    def recipe_with_ingredients_and_prep_steps(self, async_authenticated_client: TestClient):
        """Create a recipe with ingredients and prep steps for testing."""
        response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Test Recipe with Prep",
                "recipe_type": "dinner",
                "cook_time_minutes": 20,
                "ingredients": [
                    {
                        "ingredient_name": "Onion",
                        "quantity": 1,
                        "unit": "whole",
                        "order": 0,
                    },
                    {
                        "ingredient_name": "Garlic",
                        "quantity": 3,
                        "unit": "clove",
                        "order": 1,
                    },
                    {
                        "ingredient_name": "Tomatoes",
                        "quantity": 2,
                        "unit": "whole",
                        "order": 2,
                    },
                ],
                "instructions": [],
                "prep_steps": [
                    {
                        "description": "Dice the onion",
                        "order": 0,
                        "ingredient_orders": [0],
                    },
                    {
                        "description": "Mince the garlic",
                        "order": 1,
                        "ingredient_orders": [1],
                    },
                ],
            },
        )
        return response.json()

    def test_create_recipe_with_prep_steps(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test creating a recipe with prep steps linked to ingredients."""
        response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Recipe with Prep Steps",
                "recipe_type": "dinner",
                "cook_time_minutes": 30,
                "ingredients": [
                    {
                        "ingredient_name": "Cabbage",
                        "quantity": 1,
                        "unit": "whole",
                        "order": 0,
                    },
                    {
                        "ingredient_name": "Carrots",
                        "quantity": 2,
                        "unit": "whole",
                        "order": 1,
                    },
                ],
                "instructions": [
                    {"step_number": 1, "description": "Cook everything"},
                ],
                "prep_steps": [
                    {
                        "description": "Slice the cabbage thinly",
                        "order": 0,
                        "ingredient_orders": [0],
                    },
                    {
                        "description": "Julienne the carrots",
                        "order": 1,
                        "ingredient_orders": [1],
                    },
                ],
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Verify prep steps were created
        assert len(data["prep_steps"]) == 2
        assert data["prep_steps"][0]["description"] == "Slice the cabbage thinly"
        assert data["prep_steps"][1]["description"] == "Julienne the carrots"

        # Verify ingredient links (ingredient_ids should be populated)
        assert len(data["prep_steps"][0]["ingredient_ids"]) == 1
        assert len(data["prep_steps"][1]["ingredient_ids"]) == 1

    def test_create_recipe_with_prep_step_multiple_ingredients(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test creating a prep step that links to multiple ingredients."""
        response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Recipe with Multi-Ingredient Prep",
                "recipe_type": "dinner",
                "cook_time_minutes": 25,
                "ingredients": [
                    {"ingredient_name": "Onion", "quantity": 1, "unit": "whole", "order": 0},
                    {"ingredient_name": "Garlic", "quantity": 3, "unit": "clove", "order": 1},
                    {"ingredient_name": "Peppers", "quantity": 2, "unit": "whole", "order": 2},
                ],
                "instructions": [],
                "prep_steps": [
                    {
                        "description": "Dice the aromatics",
                        "order": 0,
                        "ingredient_orders": [0, 1],  # Links to both onion and garlic
                    },
                ],
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Prep step should link to 2 ingredients
        assert len(data["prep_steps"]) == 1
        assert len(data["prep_steps"][0]["ingredient_ids"]) == 2

    def test_list_prep_steps(
        self,
        async_authenticated_client: TestClient,
        recipe_with_ingredients_and_prep_steps: dict,
    ):
        """Test listing prep steps for a recipe."""
        recipe_id = recipe_with_ingredients_and_prep_steps["id"]

        response = async_authenticated_client.get(f"/recipes/{recipe_id}/prep-steps")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["description"] == "Dice the onion"
        assert data[1]["description"] == "Mince the garlic"

    def test_add_prep_step(
        self,
        async_authenticated_client: TestClient,
        recipe_with_ingredients_and_prep_steps: dict,
    ):
        """Test adding a prep step to a recipe."""
        recipe_id = recipe_with_ingredients_and_prep_steps["id"]
        tomato_id = recipe_with_ingredients_and_prep_steps["ingredients"][2]["id"]

        response = async_authenticated_client.post(
            f"/recipes/{recipe_id}/prep-steps",
            json={
                "description": "Chop the tomatoes",
                "order": 2,
                "ingredient_ids": [tomato_id],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Chop the tomatoes"
        assert data["order"] == 2
        assert tomato_id in data["ingredient_ids"]

        # Verify it appears in the list
        list_response = async_authenticated_client.get(f"/recipes/{recipe_id}/prep-steps")
        prep_steps = list_response.json()
        assert len(prep_steps) == 3

    def test_update_prep_step(
        self,
        async_authenticated_client: TestClient,
        recipe_with_ingredients_and_prep_steps: dict,
    ):
        """Test updating a prep step."""
        recipe_id = recipe_with_ingredients_and_prep_steps["id"]
        prep_step_id = recipe_with_ingredients_and_prep_steps["prep_steps"][0]["id"]

        response = async_authenticated_client.put(
            f"/recipes/{recipe_id}/prep-steps/{prep_step_id}",
            json={
                "description": "Finely dice the onion",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Finely dice the onion"
        # Order should remain unchanged
        assert data["order"] == 0

    def test_update_prep_step_change_ingredients(
        self,
        async_authenticated_client: TestClient,
        recipe_with_ingredients_and_prep_steps: dict,
    ):
        """Test updating prep step to link to different ingredients."""
        recipe_id = recipe_with_ingredients_and_prep_steps["id"]
        prep_step_id = recipe_with_ingredients_and_prep_steps["prep_steps"][0]["id"]
        garlic_id = recipe_with_ingredients_and_prep_steps["ingredients"][1]["id"]
        tomato_id = recipe_with_ingredients_and_prep_steps["ingredients"][2]["id"]

        response = async_authenticated_client.put(
            f"/recipes/{recipe_id}/prep-steps/{prep_step_id}",
            json={
                "ingredient_ids": [garlic_id, tomato_id],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["ingredient_ids"]) == 2
        assert garlic_id in data["ingredient_ids"]
        assert tomato_id in data["ingredient_ids"]

    def test_delete_prep_step(
        self,
        async_authenticated_client: TestClient,
        recipe_with_ingredients_and_prep_steps: dict,
    ):
        """Test deleting a prep step."""
        recipe_id = recipe_with_ingredients_and_prep_steps["id"]
        prep_step_id = recipe_with_ingredients_and_prep_steps["prep_steps"][0]["id"]

        response = async_authenticated_client.delete(
            f"/recipes/{recipe_id}/prep-steps/{prep_step_id}"
        )

        assert response.status_code == 204

        # Verify it's removed from the list
        list_response = async_authenticated_client.get(f"/recipes/{recipe_id}/prep-steps")
        prep_steps = list_response.json()
        assert len(prep_steps) == 1
        assert prep_steps[0]["id"] != prep_step_id

    def test_update_recipe_replaces_prep_steps(
        self,
        async_authenticated_client: TestClient,
        recipe_with_ingredients_and_prep_steps: dict,
    ):
        """Test that updating recipe with prep_steps replaces all existing prep steps."""
        recipe_id = recipe_with_ingredients_and_prep_steps["id"]

        response = async_authenticated_client.put(
            f"/recipes/{recipe_id}",
            json={
                "prep_steps": [
                    {
                        "description": "New prep step",
                        "order": 0,
                        "ingredient_orders": [0, 1, 2],
                    },
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should have only the new prep step
        assert len(data["prep_steps"]) == 1
        assert data["prep_steps"][0]["description"] == "New prep step"
        # Should link to all 3 ingredients
        assert len(data["prep_steps"][0]["ingredient_ids"]) == 3


class TestRecipeUsage:
    """Test recipe usage checking."""

    def test_check_recipe_usage_not_used(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test checking usage for a recipe not used in any templates."""
        # Create a recipe
        recipe_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Unused Recipe",
                "recipe_type": "dinner",
                "cook_time_minutes": 20,
                "ingredients": [],
                "instructions": [],
            },
        )
        recipe_id = recipe_response.json()["id"]

        # Check usage
        response = async_authenticated_client.get(f"/recipes/{recipe_id}/usage")

        assert response.status_code == 200
        data = response.json()
        assert data["is_used"] is False
        assert len(data["templates"]) == 0

    def test_check_recipe_usage_in_template(
        self,
        async_authenticated_client: TestClient,
        async_test_user,
    ):
        """Test checking usage for a recipe used in a week template."""
        # Create a recipe
        recipe_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Used Recipe",
                "recipe_type": "dinner",
                "cook_time_minutes": 30,
                "ingredients": [],
                "instructions": [],
            },
        )
        recipe_id = recipe_response.json()["id"]

        # Create a schedule sequence
        sequence_response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Test Schedule",
                "advancement_day_of_week": 0,
                "advancement_time": "08:00",
            },
        )
        sequence_id = sequence_response.json()["id"]

        # Create a template with the recipe in an assignment
        template_response = async_authenticated_client.post(
            "/templates",
            json={
                "name": "Usage Test Week",
                "assignments": [
                    {
                        "day_of_week": 1,
                        "assigned_user_id": str(async_test_user.id),
                        "action": "cook",
                        "recipe_id": recipe_id,
                        "order": 0,
                    }
                ],
            },
        )
        template_id = template_response.json()["id"]

        # Associate template with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template_id, "position": 1},
        )

        # Check usage
        response = async_authenticated_client.get(f"/recipes/{recipe_id}/usage")

        assert response.status_code == 200
        data = response.json()
        assert data["is_used"] is True
        assert len(data["templates"]) == 1
        assert data["templates"][0]["name"] == "Usage Test Week"


class TestRecipeFiltering:
    """Test recipe filtering options."""

    def test_filter_by_recipe_type(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test filtering recipes by type."""
        # Create recipes of different types
        async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Breakfast Recipe",
                "recipe_type": "breakfast",
                "cook_time_minutes": 10,
                "ingredients": [],
                "instructions": [],
            },
        )
        async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Dinner Recipe",
                "recipe_type": "dinner",
                "cook_time_minutes": 30,
                "ingredients": [],
                "instructions": [],
            },
        )

        # Filter by breakfast
        response = async_authenticated_client.get("/recipes?recipe_type=breakfast")

        assert response.status_code == 200
        recipes = response.json()
        assert all(r["recipe_type"] == "breakfast" for r in recipes)
        assert any(r["name"] == "Breakfast Recipe" for r in recipes)

    def test_filter_by_owner(
        self,
        async_authenticated_client: TestClient,
        async_test_user,
    ):
        """Test filtering recipes by owner."""
        # Create a recipe (owned by async_test_user)
        async_authenticated_client.post(
            "/recipes",
            json={
                "name": "My Recipe",
                "recipe_type": "lunch",
                "cook_time_minutes": 15,
                "ingredients": [],
                "instructions": [],
            },
        )

        # Filter by owner
        response = async_authenticated_client.get(
            f"/recipes?owner_id={async_test_user.id}"
        )

        assert response.status_code == 200
        recipes = response.json()
        assert all(r["owner_id"] == str(async_test_user.id) for r in recipes)
