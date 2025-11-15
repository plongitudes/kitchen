"""
Integration tests for grocery list generation and Pint unit aggregation.

Tests cover:
- Grocery list generation from meal plan instances
- Pint unit conversions (volume, weight)
- Ingredient aggregation by name
- Shopping day range logic
- Multiple recipes with same ingredient
- Edge cases (no recipes, special units)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta


class TestGroceryListGeneration:
    """Test grocery list generation with Pint aggregation."""

    @pytest.fixture
    async def meal_plan_with_recipes(
        self,
        async_authenticated_client: TestClient,
        async_test_user,
    ):
        """Create a meal plan instance with recipes that have ingredients."""
        # Create recipes first
        recipe1_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Pasta Carbonara",
                "recipe_type": "dinner",
                "cook_time_minutes": 20,
                "ingredients": [
                    {"ingredient_name": "Pasta", "quantity": 1, "unit": "pound", "order": 1},
                    {"ingredient_name": "Eggs", "quantity": 4, "unit": "whole", "order": 2},
                    {"ingredient_name": "Milk", "quantity": 1, "unit": "cup", "order": 3},
                ],
                "instructions": [
                    {"step_number": 1, "description": "Boil pasta"},
                    {"step_number": 2, "description": "Mix eggs and milk"},
                ],
            },
        )
        recipe1 = recipe1_response.json()

        recipe2_response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Mac and Cheese",
                "recipe_type": "dinner",
                "cook_time_minutes": 30,
                "ingredients": [
                    {"ingredient_name": "Pasta", "quantity": 500, "unit": "gram", "order": 1},
                    {"ingredient_name": "Milk", "quantity": 8, "unit": "fluid_ounce", "order": 2},
                    {"ingredient_name": "Cheese", "quantity": 2, "unit": "cup", "order": 3},
                ],
                "instructions": [
                    {"step_number": 1, "description": "Cook pasta"},
                    {"step_number": 2, "description": "Make cheese sauce"},
                ],
            },
        )
        recipe2 = recipe2_response.json()

        # Create schedule with weeks
        sequence_response = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Test Schedule",
                "advancement_day_of_week": 0,
                "advancement_time": "08:00",
            },
        )
        sequence_id = sequence_response.json()["id"]

        # Create template with cooking assignments
        template_response = async_authenticated_client.post(
            "/templates",
            json={
                "name": "Pasta Week",
                "assignments": [
                    {
                        "day_of_week": 0,  # Sunday - shopping day
                        "assigned_user_id": str(async_test_user.id),
                        "action": "shop",
                        "order": 0,
                    },
                    {
                        "day_of_week": 1,  # Monday - cook recipe 1
                        "assigned_user_id": str(async_test_user.id),
                        "action": "cook",
                        "recipe_id": recipe1["id"],
                        "order": 0,
                    },
                    {
                        "day_of_week": 3,  # Wednesday - cook recipe 2
                        "assigned_user_id": str(async_test_user.id),
                        "action": "cook",
                        "recipe_id": recipe2["id"],
                        "order": 0,
                    },
                ],
            },
        )
        template = template_response.json()

        # Associate template with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence_id}/templates",
            json={"week_template_id": template["id"], "position": 1},
        )

        # Create meal plan instance
        instance_response = async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence_id},
        )
        instance = instance_response.json()["new_instance"]

        return {
            "instance_id": instance["id"],
            "recipe1": recipe1,
            "recipe2": recipe2,
            "start_date": date.fromisoformat(instance["instance_start_date"]),
        }

    def test_generate_grocery_list(
        self,
        async_authenticated_client: TestClient,
        meal_plan_with_recipes: dict,
    ):
        """Test generating a grocery list with ingredient aggregation."""
        instance_id = meal_plan_with_recipes["instance_id"]
        start_date = meal_plan_with_recipes["start_date"]

        # Shopping day is Sunday (day 0)
        shopping_date = start_date

        # Generate grocery list
        response = async_authenticated_client.post(
            f"/meal-plans/{instance_id}/grocery-lists/generate",
            json={"shopping_date": shopping_date.isoformat()},
        )

        assert response.status_code == 201
        data = response.json()

        # Verify grocery list structure
        assert data["shopping_date"] == shopping_date.isoformat()
        assert data["meal_plan_instance_id"] == instance_id
        assert "items" in data
        assert len(data["items"]) > 0

        # Verify ingredients are aggregated
        items_by_name = {item["ingredient_name"].lower(): item for item in data["items"]}

        # Check pasta aggregation (1 pound + 500 grams)
        assert "pasta" in items_by_name
        pasta_item = items_by_name["pasta"]
        # 1 pound ≈ 453.6 grams, plus 500 grams = 953.6 grams
        assert pasta_item["unit"] == "gram"
        assert 950 < pasta_item["total_quantity"] < 960  # Allow small rounding

        # Check milk aggregation (1 cup + 8 fl oz)
        assert "milk" in items_by_name
        milk_item = items_by_name["milk"]
        # 1 cup + 8 fl oz (1 cup) = 2 cups
        assert milk_item["unit"] == "cup"
        assert abs(milk_item["total_quantity"] - 2.0) < 0.01

        # Check items with no conversion
        assert "eggs" in items_by_name
        assert items_by_name["eggs"]["unit"] == "whole"
        assert items_by_name["eggs"]["total_quantity"] == 4

        assert "cheese" in items_by_name
        assert items_by_name["cheese"]["unit"] == "cup"
        assert items_by_name["cheese"]["total_quantity"] == 2

    def test_grocery_list_tracks_source_recipes(
        self,
        async_authenticated_client: TestClient,
        meal_plan_with_recipes: dict,
    ):
        """Test that grocery list items track which recipes they came from."""
        instance_id = meal_plan_with_recipes["instance_id"]
        start_date = meal_plan_with_recipes["start_date"]
        recipe1_id = meal_plan_with_recipes["recipe1"]["id"]
        recipe2_id = meal_plan_with_recipes["recipe2"]["id"]

        # Generate grocery list
        response = async_authenticated_client.post(
            f"/meal-plans/{instance_id}/grocery-lists/generate",
            json={"shopping_date": start_date.isoformat()},
        )

        data = response.json()
        items_by_name = {item["ingredient_name"].lower(): item for item in data["items"]}

        # Pasta appears in both recipes
        pasta_item = items_by_name["pasta"]
        assert recipe1_id in pasta_item["source_recipe_ids"]
        assert recipe2_id in pasta_item["source_recipe_ids"]

        # Eggs only in recipe 1
        eggs_item = items_by_name["eggs"]
        assert recipe1_id in eggs_item["source_recipe_ids"]
        assert recipe2_id not in eggs_item["source_recipe_ids"]

        # Cheese only in recipe 2
        cheese_item = items_by_name["cheese"]
        assert recipe2_id in cheese_item["source_recipe_ids"]
        assert recipe1_id not in cheese_item["source_recipe_ids"]

    def test_list_grocery_lists(
        self,
        async_authenticated_client: TestClient,
        meal_plan_with_recipes: dict,
    ):
        """Test listing all grocery lists."""
        instance_id = meal_plan_with_recipes["instance_id"]
        start_date = meal_plan_with_recipes["start_date"]

        # Generate a grocery list
        async_authenticated_client.post(
            f"/meal-plans/{instance_id}/grocery-lists/generate",
            json={"shopping_date": start_date.isoformat()},
        )

        # List all grocery lists
        response = async_authenticated_client.get("/meal-plans/grocery-lists/all")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(gl["shopping_date"] == start_date.isoformat() for gl in data)

    def test_list_instance_grocery_lists(
        self,
        async_authenticated_client: TestClient,
        meal_plan_with_recipes: dict,
    ):
        """Test listing grocery lists for a specific instance."""
        instance_id = meal_plan_with_recipes["instance_id"]
        start_date = meal_plan_with_recipes["start_date"]

        # Generate two grocery lists for different dates
        async_authenticated_client.post(
            f"/meal-plans/{instance_id}/grocery-lists/generate",
            json={"shopping_date": start_date.isoformat()},
        )
        async_authenticated_client.post(
            f"/meal-plans/{instance_id}/grocery-lists/generate",
            json={"shopping_date": (start_date + timedelta(days=7)).isoformat()},
        )

        # List grocery lists for this instance
        response = async_authenticated_client.get(
            f"/meal-plans/{instance_id}/grocery-lists"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(gl["meal_plan_instance_id"] == instance_id for gl in data)

    def test_get_grocery_list_by_id(
        self,
        async_authenticated_client: TestClient,
        meal_plan_with_recipes: dict,
    ):
        """Test getting a specific grocery list by ID."""
        instance_id = meal_plan_with_recipes["instance_id"]
        start_date = meal_plan_with_recipes["start_date"]

        # Generate grocery list
        create_response = async_authenticated_client.post(
            f"/meal-plans/{instance_id}/grocery-lists/generate",
            json={"shopping_date": start_date.isoformat()},
        )
        grocery_list_id = create_response.json()["id"]

        # Get by ID
        response = async_authenticated_client.get(
            f"/meal-plans/grocery-lists/{grocery_list_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == grocery_list_id
        assert "items" in data
        assert len(data["items"]) > 0

    def test_regenerate_grocery_list_replaces_old(
        self,
        async_authenticated_client: TestClient,
        meal_plan_with_recipes: dict,
    ):
        """Test that regenerating a grocery list for same date replaces the old one."""
        instance_id = meal_plan_with_recipes["instance_id"]
        start_date = meal_plan_with_recipes["start_date"]

        # Generate grocery list first time
        first_response = async_authenticated_client.post(
            f"/meal-plans/{instance_id}/grocery-lists/generate",
            json={"shopping_date": start_date.isoformat()},
        )
        first_list_id = first_response.json()["id"]
        first_item_count = len(first_response.json()["items"])

        # Generate again for same date
        second_response = async_authenticated_client.post(
            f"/meal-plans/{instance_id}/grocery-lists/generate",
            json={"shopping_date": start_date.isoformat()},
        )
        second_list_id = second_response.json()["id"]

        # Should reuse the same grocery list
        assert first_list_id == second_list_id

        # List all for this instance - should only have one
        list_response = async_authenticated_client.get(
            f"/meal-plans/{instance_id}/grocery-lists"
        )
        lists = list_response.json()
        matching_lists = [
            gl for gl in lists if gl["shopping_date"] == start_date.isoformat()
        ]
        assert len(matching_lists) == 1

    def test_case_insensitive_ingredient_grouping(
        self,
        async_authenticated_client: TestClient,
        async_test_user,
    ):
        """Test that ingredients are grouped case-insensitively."""
        # Create recipes with different casings of same ingredient
        recipe1 = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Test Recipe 1",
                "recipe_type": "lunch",
                "cook_time_minutes": 10,
                "ingredients": [
                    {"ingredient_name": "Milk", "quantity": 1, "unit": "cup", "order": 1},
                ],
                "instructions": [{"step_number": 1, "description": "Test"}],
            },
        ).json()

        recipe2 = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Test Recipe 2",
                "recipe_type": "lunch",
                "cook_time_minutes": 10,
                "ingredients": [
                    {"ingredient_name": "milk", "quantity": 1, "unit": "cup", "order": 1},
                ],
                "instructions": [{"step_number": 1, "description": "Test"}],
            },
        ).json()

        # Create schedule and instance
        sequence = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Test",
                "advancement_day_of_week": 0,
                "advancement_time": "08:00",
            },
        ).json()

        # Create template with assignments
        template = async_authenticated_client.post(
            "/templates",
            json={
                "name": "Test Week",
                "assignments": [
                    {
                        "day_of_week": 0,
                        "assigned_user_id": str(async_test_user.id),
                        "action": "shop",
                        "order": 0,
                    },
                    {
                        "day_of_week": 1,
                        "assigned_user_id": str(async_test_user.id),
                        "action": "cook",
                        "recipe_id": recipe1["id"],
                        "order": 0,
                    },
                    {
                        "day_of_week": 2,
                        "assigned_user_id": str(async_test_user.id),
                        "action": "cook",
                        "recipe_id": recipe2["id"],
                        "order": 0,
                    },
                ],
            },
        ).json()

        # Associate template with sequence
        async_authenticated_client.post(
            f"/schedules/{sequence['id']}/templates",
            json={"week_template_id": template["id"], "position": 1},
        )

        instance = async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence["id"]},
        ).json()["new_instance"]

        # Generate grocery list
        grocery_list = async_authenticated_client.post(
            f"/meal-plans/{instance['id']}/grocery-lists/generate",
            json={"shopping_date": instance["instance_start_date"]},
        ).json()

        # Should have only ONE milk item with quantity 2
        milk_items = [
            item for item in grocery_list["items"]
            if item["ingredient_name"].lower() == "milk"
        ]
        assert len(milk_items) == 1
        assert milk_items[0]["total_quantity"] == 2.0
        assert milk_items[0]["unit"] == "cup"
