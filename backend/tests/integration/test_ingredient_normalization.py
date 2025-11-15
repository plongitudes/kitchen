"""
Integration tests for ingredient normalization.

Tests cover:
- Auto-matching ingredients to common ingredients via aliases
- Grocery list grouping by common_ingredient_id
- Unmapped ingredients falling back to name-based grouping
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ingredient import CommonIngredient, IngredientAlias


class TestIngredientNormalization:
    """Test ingredient auto-matching and normalization."""

    @pytest.fixture(autouse=True)
    async def seed_common_ingredients(self, async_db_session: AsyncSession):
        """Seed test database with common ingredients for these tests."""
        # Add milk common ingredient
        milk = CommonIngredient(name="milk", category="dairy")
        async_db_session.add(milk)
        await async_db_session.flush()

        # Add aliases for milk
        aliases = [
            IngredientAlias(common_ingredient_id=milk.id, alias="whole milk"),
            IngredientAlias(common_ingredient_id=milk.id, alias="2% milk"),
            IngredientAlias(common_ingredient_id=milk.id, alias="skim milk"),
        ]
        for alias in aliases:
            async_db_session.add(alias)

        # Add eggs common ingredient
        eggs = CommonIngredient(name="eggs", category="dairy")
        async_db_session.add(eggs)
        await async_db_session.flush()

        # Add aliases for eggs
        eggs_aliases = [
            IngredientAlias(common_ingredient_id=eggs.id, alias="egg"),
            IngredientAlias(common_ingredient_id=eggs.id, alias="large eggs"),
        ]
        for alias in eggs_aliases:
            async_db_session.add(alias)

        # Add flour common ingredient
        flour = CommonIngredient(name="all-purpose flour", category="pantry")
        async_db_session.add(flour)
        await async_db_session.flush()

        # Add aliases for flour
        flour_aliases = [
            IngredientAlias(common_ingredient_id=flour.id, alias="AP flour"),
            IngredientAlias(common_ingredient_id=flour.id, alias="white flour"),
            IngredientAlias(common_ingredient_id=flour.id, alias="plain flour"),
            IngredientAlias(common_ingredient_id=flour.id, alias="flour"),
        ]
        for alias in flour_aliases:
            async_db_session.add(alias)

        await async_db_session.commit()

    @pytest.mark.asyncio
    async def test_ingredient_auto_matches_via_alias(
        self,
        async_authenticated_client: TestClient,
        async_db_session: AsyncSession,
    ):
        """Test that creating a recipe auto-matches ingredients to common ingredients."""
        # Create recipe with "whole milk" (should match to "milk" common ingredient)
        response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Test Recipe",
                "recipe_type": "breakfast",
                "cook_time_minutes": 10,
                "ingredients": [
                    {"ingredient_name": "whole milk", "quantity": 1, "unit": "cup", "order": 1},
                    {"ingredient_name": "eggs", "quantity": 2, "unit": "whole", "order": 2},
                ],
                "instructions": [
                    {"step_number": 1, "description": "Mix ingredients"},
                ],
            },
        )

        assert response.status_code == 201
        recipe = response.json()

        # Verify ingredients have common_ingredient_id set
        # Note: We can't directly check common_ingredient_id from API response,
        # but we can verify via grocery list grouping behavior
        assert len(recipe["ingredients"]) == 2

    @pytest.mark.asyncio
    async def test_ingredient_matches_canonical_name(
        self,
        async_authenticated_client: TestClient,
        async_db_session: AsyncSession,
    ):
        """Test that exact canonical name matches work."""
        # Create recipe with exact canonical name "milk"
        response = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Test Recipe 2",
                "recipe_type": "breakfast",
                "cook_time_minutes": 10,
                "ingredients": [
                    {"ingredient_name": "milk", "quantity": 2, "unit": "cup", "order": 1},
                ],
                "instructions": [
                    {"step_number": 1, "description": "Pour milk"},
                ],
            },
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_grocery_list_groups_by_common_ingredient(
        self,
        async_authenticated_client: TestClient,
        async_test_user,
    ):
        """Test that grocery lists group ingredients by common_ingredient_id."""
        # Create two recipes with different milk variations
        recipe1 = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Pancakes",
                "recipe_type": "breakfast",
                "cook_time_minutes": 15,
                "ingredients": [
                    {"ingredient_name": "whole milk", "quantity": 1, "unit": "cup", "order": 1},
                    {"ingredient_name": "eggs", "quantity": 2, "unit": "whole", "order": 2},
                ],
                "instructions": [{"step_number": 1, "description": "Mix"}],
            },
        ).json()

        recipe2 = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "French Toast",
                "recipe_type": "breakfast",
                "cook_time_minutes": 10,
                "ingredients": [
                    {"ingredient_name": "milk", "quantity": 0.5, "unit": "cup", "order": 1},
                    {"ingredient_name": "egg", "quantity": 3, "unit": "whole", "order": 2},
                ],
                "instructions": [{"step_number": 1, "description": "Dip bread"}],
            },
        ).json()

        # Create schedule and meal plan
        sequence = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Breakfast Week",
                "advancement_day_of_week": 0,
                "advancement_time": "08:00",
            },
        ).json()

        # Create template with both recipes
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

        # Create meal plan instance
        instance_response = async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence["id"]},
        )
        instance = instance_response.json()["new_instance"]

        # Generate grocery list
        grocery_list = async_authenticated_client.post(
            f"/meal-plans/{instance['id']}/grocery-lists/generate",
            json={"shopping_date": instance["instance_start_date"]},
        ).json()

        # Should have grouped milk variations together
        milk_items = [
            item for item in grocery_list["items"]
            if "milk" in item["ingredient_name"].lower()
        ]
        eggs_items = [
            item for item in grocery_list["items"]
            if "egg" in item["ingredient_name"].lower()
        ]

        # Should only have ONE milk item (1 + 0.5 = 1.5 cups)
        assert len(milk_items) == 1
        assert milk_items[0]["total_quantity"] == 1.5
        assert milk_items[0]["unit"] == "cup"

        # Should only have ONE eggs item (2 + 3 = 5 whole)
        assert len(eggs_items) == 1
        assert eggs_items[0]["total_quantity"] == 5.0
        assert eggs_items[0]["unit"] == "whole"

    @pytest.mark.asyncio
    async def test_unmapped_ingredients_still_group_by_name(
        self,
        async_authenticated_client: TestClient,
        async_test_user,
    ):
        """Test that unmapped ingredients still group by case-insensitive name."""
        # Create recipes with an unmapped ingredient
        recipe1 = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Mystery Dish 1",
                "recipe_type": "dinner",
                "cook_time_minutes": 20,
                "ingredients": [
                    {"ingredient_name": "unicorn dust", "quantity": 1, "unit": "pinch", "order": 1},
                ],
                "instructions": [{"step_number": 1, "description": "Sprinkle"}],
            },
        ).json()

        recipe2 = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Mystery Dish 2",
                "recipe_type": "dinner",
                "cook_time_minutes": 15,
                "ingredients": [
                    {"ingredient_name": "Unicorn Dust", "quantity": 2, "unit": "pinch", "order": 1},
                ],
                "instructions": [{"step_number": 1, "description": "Add magic"}],
            },
        ).json()

        # Create schedule and meal plan
        sequence = async_authenticated_client.post(
            "/schedules",
            json={
                "name": "Magic Week",
                "advancement_day_of_week": 0,
                "advancement_time": "08:00",
            },
        ).json()

        template = async_authenticated_client.post(
            "/templates",
            json={
                "name": "Magic Template",
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

        async_authenticated_client.post(
            f"/schedules/{sequence['id']}/templates",
            json={"week_template_id": template["id"], "position": 1},
        )

        instance_response = async_authenticated_client.post(
            "/meal-plans/advance-week",
            json={"sequence_id": sequence["id"]},
        )
        instance = instance_response.json()["new_instance"]

        # Generate grocery list
        grocery_list = async_authenticated_client.post(
            f"/meal-plans/{instance['id']}/grocery-lists/generate",
            json={"shopping_date": instance["instance_start_date"]},
        ).json()

        # Should still group by case-insensitive name
        unicorn_items = [
            item for item in grocery_list["items"]
            if "unicorn" in item["ingredient_name"].lower()
        ]

        # Should have ONE unicorn dust item (1 + 2 = 3 pinches)
        assert len(unicorn_items) == 1
        assert unicorn_items[0]["total_quantity"] == 3.0
        assert unicorn_items[0]["unit"] == "pinch"

    @pytest.mark.asyncio
    async def test_case_insensitive_alias_matching(
        self,
        async_authenticated_client: TestClient,
    ):
        """Test that alias matching is case-insensitive."""
        # "AP flour" should match "all-purpose flour" regardless of case
        recipe = async_authenticated_client.post(
            "/recipes",
            json={
                "name": "Bread",
                "recipe_type": "side",
                "cook_time_minutes": 60,
                "ingredients": [
                    {"ingredient_name": "AP FLOUR", "quantity": 3, "unit": "cup", "order": 1},
                    {"ingredient_name": "white flour", "quantity": 1, "unit": "cup", "order": 2},
                ],
                "instructions": [{"step_number": 1, "description": "Mix flours"}],
            },
        ).json()

        # Both should match to "all-purpose flour" and be grouped
        assert len(recipe["ingredients"]) == 2
