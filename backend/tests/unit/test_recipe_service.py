"""
Unit tests for RecipeService.

Tests cover:
- get_recipes: listing with filters (owner, type, retired)
- get_recipe_by_id: fetching with ingredients/instructions
- create_recipe: creating recipes with ingredients and instructions
- update_recipe: updating fields and replacing ingredients/instructions
- delete_recipe: soft delete with usage validation
- restore_recipe: undeleting retired recipes
- check_recipe_usage: finding templates using a recipe
- Ingredient CRUD: get, create, update, delete
- Instruction CRUD: get, create, update, delete
"""

import pytest
from uuid import uuid4
from datetime import datetime

from fastapi import HTTPException
from app.services.recipe_service import RecipeService
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    RecipeIngredientCreate,
    RecipeIngredientUpdate,
    RecipeInstructionCreate,
    RecipeInstructionUpdate,
)
from tests.factories import (
    UserFactory,
    RecipeFactory,
    RecipeIngredientFactory,
    RecipeInstructionFactory,
    WeekTemplateFactory,
    WeekDayAssignmentFactory,
    CommonIngredientFactory,
    IngredientAliasFactory,
)


@pytest.mark.asyncio
class TestGetRecipes:
    """Test the get_recipes method."""

    async def test_returns_all_active_recipes(self, async_db_session, async_test_user):
        """Test that active recipes are returned."""
        recipe1 = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe A")
        recipe2 = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe B")
        async_db_session.add(recipe1)
        async_db_session.add(recipe2)
        await async_db_session.commit()

        result = await RecipeService.get_recipes(async_db_session)

        names = [r.name for r in result]
        assert "Recipe A" in names
        assert "Recipe B" in names

    async def test_filters_by_owner(self, async_db_session, async_test_user, async_second_test_user):
        """Test that recipes can be filtered by owner."""
        recipe1 = RecipeFactory.build(owner_id=async_test_user.id, name="User1 Recipe")
        recipe2 = RecipeFactory.build(owner_id=async_second_test_user.id, name="User2 Recipe")
        async_db_session.add(recipe1)
        async_db_session.add(recipe2)
        await async_db_session.commit()

        result = await RecipeService.get_recipes(async_db_session, owner_id=async_test_user.id)

        names = [r.name for r in result]
        assert "User1 Recipe" in names
        assert "User2 Recipe" not in names

    async def test_filters_by_recipe_type(self, async_db_session, async_test_user):
        """Test that recipes can be filtered by type."""
        dinner = RecipeFactory.build(owner_id=async_test_user.id, name="Dinner", recipe_type="dinner")
        lunch = RecipeFactory.build(owner_id=async_test_user.id, name="Lunch", recipe_type="lunch")
        async_db_session.add(dinner)
        async_db_session.add(lunch)
        await async_db_session.commit()

        result = await RecipeService.get_recipes(async_db_session, recipe_type="dinner")

        names = [r.name for r in result]
        assert "Dinner" in names
        assert "Lunch" not in names

    async def test_excludes_retired_by_default(self, async_db_session, async_test_user):
        """Test that retired recipes are excluded by default."""
        active = RecipeFactory.build(owner_id=async_test_user.id, name="Active Recipe")
        retired = RecipeFactory.build(owner_id=async_test_user.id, name="Retired Recipe", retired_at=datetime.utcnow())
        async_db_session.add(active)
        async_db_session.add(retired)
        await async_db_session.commit()

        result = await RecipeService.get_recipes(async_db_session)

        names = [r.name for r in result]
        assert "Active Recipe" in names
        assert "Retired Recipe" not in names

    async def test_includes_retired_when_requested(self, async_db_session, async_test_user):
        """Test that retired recipes can be included."""
        active = RecipeFactory.build(owner_id=async_test_user.id, name="Active Recipe 2")
        retired = RecipeFactory.build(owner_id=async_test_user.id, name="Retired Recipe 2", retired_at=datetime.utcnow())
        async_db_session.add(active)
        async_db_session.add(retired)
        await async_db_session.commit()

        result = await RecipeService.get_recipes(async_db_session, include_retired=True)

        names = [r.name for r in result]
        assert "Active Recipe 2" in names
        assert "Retired Recipe 2" in names

    async def test_returns_sorted_by_name(self, async_db_session, async_test_user):
        """Test that recipes are sorted alphabetically."""
        recipe_c = RecipeFactory.build(owner_id=async_test_user.id, name="Charlie Casserole")
        recipe_a = RecipeFactory.build(owner_id=async_test_user.id, name="Alpha Appetizer")
        recipe_b = RecipeFactory.build(owner_id=async_test_user.id, name="Bravo Breakfast")
        async_db_session.add(recipe_c)
        async_db_session.add(recipe_a)
        async_db_session.add(recipe_b)
        await async_db_session.commit()

        result = await RecipeService.get_recipes(async_db_session)

        test_recipes = [r for r in result if r.name in ["Alpha Appetizer", "Bravo Breakfast", "Charlie Casserole"]]
        names = [r.name for r in test_recipes]
        assert names == sorted(names)


@pytest.mark.asyncio
class TestGetRecipeById:
    """Test the get_recipe_by_id method."""

    async def test_gets_existing_recipe(self, async_db_session, async_test_user):
        """Test fetching an existing recipe."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Fetchable Recipe")
        async_db_session.add(recipe)
        await async_db_session.commit()

        result = await RecipeService.get_recipe_by_id(async_db_session, recipe.id)

        assert result is not None
        assert result.id == recipe.id
        assert result.name == "Fetchable Recipe"

    async def test_returns_none_for_missing_recipe(self, async_db_session):
        """Test that None is returned for non-existent recipe."""
        fake_id = uuid4()

        result = await RecipeService.get_recipe_by_id(async_db_session, fake_id)

        assert result is None

    async def test_includes_ingredients(self, async_db_session, async_test_user):
        """Test that ingredients are loaded."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe with Ingredients")
        async_db_session.add(recipe)
        await async_db_session.flush()

        ingredient = RecipeIngredientFactory.build(
            recipe_id=recipe.id,
            ingredient_name="Flour",
            quantity=2.0,
            unit="cup",
        )
        async_db_session.add(ingredient)
        await async_db_session.commit()

        result = await RecipeService.get_recipe_by_id(async_db_session, recipe.id)

        assert result is not None
        assert len(result.ingredients) == 1
        assert result.ingredients[0].ingredient_name == "Flour"

    async def test_includes_instructions(self, async_db_session, async_test_user):
        """Test that instructions are loaded."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe with Instructions")
        async_db_session.add(recipe)
        await async_db_session.flush()

        instruction = RecipeInstructionFactory.build(
            recipe_id=recipe.id,
            step_number=1,
            description="Mix ingredients",
        )
        async_db_session.add(instruction)
        await async_db_session.commit()

        result = await RecipeService.get_recipe_by_id(async_db_session, recipe.id)

        assert result is not None
        assert len(result.instructions) == 1
        assert result.instructions[0].description == "Mix ingredients"


@pytest.mark.asyncio
class TestCreateRecipe:
    """Test the create_recipe method."""

    async def test_creates_basic_recipe(self, async_db_session, async_test_user):
        """Test creating a recipe without ingredients or instructions."""
        recipe_data = RecipeCreate(
            name="New Recipe",
            recipe_type="dinner",
            description="A new dinner recipe",
            ingredients=[],
            instructions=[],
        )

        result = await RecipeService.create_recipe(async_db_session, recipe_data, async_test_user.id)

        assert result is not None
        assert result.name == "New Recipe"
        assert result.recipe_type == "dinner"
        assert result.owner_id == async_test_user.id

    async def test_creates_recipe_with_ingredients(self, async_db_session, async_test_user):
        """Test creating a recipe with ingredients."""
        recipe_data = RecipeCreate(
            name="Recipe with Ingredients",
            recipe_type="dinner",
            ingredients=[
                RecipeIngredientCreate(ingredient_name="Flour", quantity=2.0, unit="cup", order=0),
                RecipeIngredientCreate(ingredient_name="Sugar", quantity=1.0, unit="cup", order=1),
            ],
            instructions=[],
        )

        result = await RecipeService.create_recipe(async_db_session, recipe_data, async_test_user.id)

        assert result is not None
        assert len(result.ingredients) == 2
        names = [i.ingredient_name for i in result.ingredients]
        assert "Flour" in names
        assert "Sugar" in names

    async def test_creates_recipe_with_instructions(self, async_db_session, async_test_user):
        """Test creating a recipe with instructions."""
        recipe_data = RecipeCreate(
            name="Recipe with Instructions",
            recipe_type="dinner",
            ingredients=[],
            instructions=[
                RecipeInstructionCreate(step_number=1, description="Preheat oven"),
                RecipeInstructionCreate(step_number=2, description="Mix ingredients"),
            ],
        )

        result = await RecipeService.create_recipe(async_db_session, recipe_data, async_test_user.id)

        assert result is not None
        assert len(result.instructions) == 2
        descriptions = [i.description for i in result.instructions]
        assert "Preheat oven" in descriptions
        assert "Mix ingredients" in descriptions

    async def test_auto_matches_common_ingredient(self, async_db_session, async_test_user):
        """Test that ingredients are auto-matched to common ingredients."""
        # Create a common ingredient with alias
        common = CommonIngredientFactory.build(name="all-purpose flour", category="pantry")
        async_db_session.add(common)
        await async_db_session.flush()

        alias = IngredientAliasFactory.build(common_ingredient_id=common.id, alias="flour")
        async_db_session.add(alias)
        await async_db_session.commit()

        recipe_data = RecipeCreate(
            name="Recipe with Common Ingredient",
            recipe_type="dinner",
            ingredients=[
                RecipeIngredientCreate(ingredient_name="flour", quantity=2.0, unit="cup", order=0),
            ],
            instructions=[],
        )

        result = await RecipeService.create_recipe(async_db_session, recipe_data, async_test_user.id)

        assert result is not None
        assert len(result.ingredients) == 1
        assert result.ingredients[0].common_ingredient_id == common.id


@pytest.mark.asyncio
class TestUpdateRecipe:
    """Test the update_recipe method."""

    async def test_updates_recipe_name(self, async_db_session, async_test_user):
        """Test updating only the recipe name."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Original Name")
        async_db_session.add(recipe)
        await async_db_session.commit()

        update_data = RecipeUpdate(name="Updated Name")
        result = await RecipeService.update_recipe(async_db_session, recipe.id, update_data)

        assert result is not None
        assert result.name == "Updated Name"

    async def test_raises_for_missing_recipe(self, async_db_session):
        """Test that HTTPException is raised when recipe doesn't exist."""
        fake_id = uuid4()
        update_data = RecipeUpdate(name="Whatever")

        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.update_recipe(async_db_session, fake_id, update_data)

        assert exc_info.value.status_code == 404
        assert "Recipe not found" in str(exc_info.value.detail)

    async def test_replaces_ingredients(self, async_db_session, async_test_user):
        """Test that updating ingredients replaces all existing ones."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe to Update")
        async_db_session.add(recipe)
        await async_db_session.flush()

        old_ingredient = RecipeIngredientFactory.build(
            recipe_id=recipe.id,
            ingredient_name="Old Ingredient",
            quantity=1.0,
            unit="cup",
        )
        async_db_session.add(old_ingredient)
        await async_db_session.commit()

        update_data = RecipeUpdate(
            ingredients=[
                RecipeIngredientCreate(ingredient_name="New Ingredient", quantity=2.0, unit="tablespoon", order=0),
            ]
        )

        result = await RecipeService.update_recipe(async_db_session, recipe.id, update_data)

        assert result is not None
        assert len(result.ingredients) == 1
        assert result.ingredients[0].ingredient_name == "New Ingredient"

    async def test_replaces_instructions(self, async_db_session, async_test_user):
        """Test that updating instructions replaces all existing ones."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe to Update 2")
        async_db_session.add(recipe)
        await async_db_session.flush()

        old_instruction = RecipeInstructionFactory.build(
            recipe_id=recipe.id,
            step_number=1,
            description="Old step",
        )
        async_db_session.add(old_instruction)
        await async_db_session.commit()

        update_data = RecipeUpdate(
            instructions=[
                RecipeInstructionCreate(step_number=1, description="New step"),
            ]
        )

        result = await RecipeService.update_recipe(async_db_session, recipe.id, update_data)

        assert result is not None
        assert len(result.instructions) == 1
        assert result.instructions[0].description == "New step"


@pytest.mark.asyncio
class TestDeleteRecipe:
    """Test the delete_recipe method."""

    async def test_soft_deletes_recipe(self, async_db_session, async_test_user):
        """Test that deleting sets retired_at timestamp."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="To Delete")
        async_db_session.add(recipe)
        await async_db_session.commit()

        result = await RecipeService.delete_recipe(async_db_session, recipe.id)

        assert result is not None
        assert result.retired_at is not None

    async def test_raises_for_missing_recipe(self, async_db_session):
        """Test that HTTPException is raised when recipe doesn't exist."""
        fake_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.delete_recipe(async_db_session, fake_id)

        assert exc_info.value.status_code == 404

    async def test_raises_for_already_retired(self, async_db_session, async_test_user):
        """Test that HTTPException is raised when recipe is already retired."""
        recipe = RecipeFactory.build(
            owner_id=async_test_user.id,
            name="Already Retired",
            retired_at=datetime.utcnow(),
        )
        async_db_session.add(recipe)
        await async_db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.delete_recipe(async_db_session, recipe.id)

        assert exc_info.value.status_code == 400
        assert "already retired" in str(exc_info.value.detail)

    async def test_raises_when_used_in_template(self, async_db_session, async_test_user):
        """Test that HTTPException is raised when recipe is used in active template."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Used Recipe")
        async_db_session.add(recipe)
        await async_db_session.flush()

        template = WeekTemplateFactory.build(name="Template Using Recipe")
        async_db_session.add(template)
        await async_db_session.flush()

        assignment = WeekDayAssignmentFactory.build(
            week_template_id=template.id,
            recipe_id=recipe.id,
            assigned_user_id=async_test_user.id,
            day_of_week=1,
            action="cook",
        )
        async_db_session.add(assignment)
        await async_db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.delete_recipe(async_db_session, recipe.id)

        assert exc_info.value.status_code == 400
        assert "used in active week templates" in str(exc_info.value.detail)


@pytest.mark.asyncio
class TestRestoreRecipe:
    """Test the restore_recipe method."""

    async def test_restores_retired_recipe(self, async_db_session, async_test_user):
        """Test that a retired recipe can be restored."""
        recipe = RecipeFactory.build(
            owner_id=async_test_user.id,
            name="To Restore",
            retired_at=datetime.utcnow(),
        )
        async_db_session.add(recipe)
        await async_db_session.commit()

        result = await RecipeService.restore_recipe(async_db_session, recipe.id)

        assert result is not None
        assert result.retired_at is None

    async def test_raises_for_missing_recipe(self, async_db_session):
        """Test that HTTPException is raised when recipe doesn't exist."""
        fake_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.restore_recipe(async_db_session, fake_id)

        assert exc_info.value.status_code == 404

    async def test_raises_for_active_recipe(self, async_db_session, async_test_user):
        """Test that HTTPException is raised when recipe is not retired."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Active Recipe")
        async_db_session.add(recipe)
        await async_db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.restore_recipe(async_db_session, recipe.id)

        assert exc_info.value.status_code == 400
        assert "not retired" in str(exc_info.value.detail)


@pytest.mark.asyncio
class TestCheckRecipeUsage:
    """Test the check_recipe_usage method."""

    async def test_returns_templates_using_recipe(self, async_db_session, async_test_user):
        """Test finding templates that use a recipe."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Shared Recipe")
        async_db_session.add(recipe)
        await async_db_session.flush()

        template = WeekTemplateFactory.build(name="Template 1")
        async_db_session.add(template)
        await async_db_session.flush()

        assignment = WeekDayAssignmentFactory.build(
            week_template_id=template.id,
            recipe_id=recipe.id,
            assigned_user_id=async_test_user.id,
            day_of_week=1,
            action="cook",
        )
        async_db_session.add(assignment)
        await async_db_session.commit()

        result = await RecipeService.check_recipe_usage(async_db_session, recipe.id)

        assert len(result) == 1
        assert result[0]["name"] == "Template 1"

    async def test_excludes_retired_templates(self, async_db_session, async_test_user):
        """Test that retired templates are not included."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe in Retired Template")
        async_db_session.add(recipe)
        await async_db_session.flush()

        template = WeekTemplateFactory.build(name="Retired Template", retired_at=datetime.utcnow())
        async_db_session.add(template)
        await async_db_session.flush()

        assignment = WeekDayAssignmentFactory.build(
            week_template_id=template.id,
            recipe_id=recipe.id,
            assigned_user_id=async_test_user.id,
            day_of_week=1,
            action="cook",
        )
        async_db_session.add(assignment)
        await async_db_session.commit()

        result = await RecipeService.check_recipe_usage(async_db_session, recipe.id)

        assert len(result) == 0

    async def test_returns_empty_for_unused_recipe(self, async_db_session, async_test_user):
        """Test that empty list is returned for unused recipe."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Unused Recipe")
        async_db_session.add(recipe)
        await async_db_session.commit()

        result = await RecipeService.check_recipe_usage(async_db_session, recipe.id)

        assert len(result) == 0


@pytest.mark.asyncio
class TestIngredientCRUD:
    """Test ingredient CRUD operations."""

    async def test_get_ingredients(self, async_db_session, async_test_user):
        """Test getting ingredients for a recipe."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe")
        async_db_session.add(recipe)
        await async_db_session.flush()

        ing1 = RecipeIngredientFactory.build(recipe_id=recipe.id, ingredient_name="Flour", order=0)
        ing2 = RecipeIngredientFactory.build(recipe_id=recipe.id, ingredient_name="Sugar", order=1)
        async_db_session.add(ing1)
        async_db_session.add(ing2)
        await async_db_session.commit()

        result = await RecipeService.get_ingredients(async_db_session, recipe.id)

        assert len(result) == 2
        assert result[0].ingredient_name == "Flour"
        assert result[1].ingredient_name == "Sugar"

    async def test_create_ingredient(self, async_db_session, async_test_user):
        """Test adding an ingredient to a recipe."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe")
        async_db_session.add(recipe)
        await async_db_session.commit()

        ingredient_data = RecipeIngredientCreate(
            ingredient_name="Butter",
            quantity=0.5,
            unit="cup",
            order=0,
        )

        result = await RecipeService.create_ingredient(async_db_session, recipe.id, ingredient_data)

        assert result is not None
        assert result.ingredient_name == "Butter"
        assert result.quantity == 0.5

    async def test_create_ingredient_raises_for_missing_recipe(self, async_db_session):
        """Test that HTTPException is raised when recipe doesn't exist."""
        fake_id = uuid4()
        ingredient_data = RecipeIngredientCreate(
            ingredient_name="Salt",
            quantity=1.0,
            unit="teaspoon",
            order=0,
        )

        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.create_ingredient(async_db_session, fake_id, ingredient_data)

        assert exc_info.value.status_code == 404

    async def test_update_ingredient(self, async_db_session, async_test_user):
        """Test updating an ingredient."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe")
        async_db_session.add(recipe)
        await async_db_session.flush()

        ingredient = RecipeIngredientFactory.build(
            recipe_id=recipe.id,
            ingredient_name="Original",
            quantity=1.0,
            unit="cup",
        )
        async_db_session.add(ingredient)
        await async_db_session.commit()

        update_data = RecipeIngredientUpdate(quantity=2.0, unit="tablespoon")
        result = await RecipeService.update_ingredient(async_db_session, ingredient.id, update_data)

        assert result.quantity == 2.0
        assert result.unit == "tablespoon"

    async def test_update_ingredient_raises_for_missing(self, async_db_session):
        """Test that HTTPException is raised when ingredient doesn't exist."""
        fake_id = uuid4()
        update_data = RecipeIngredientUpdate(quantity=2.0)

        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.update_ingredient(async_db_session, fake_id, update_data)

        assert exc_info.value.status_code == 404

    async def test_delete_ingredient(self, async_db_session, async_test_user):
        """Test deleting an ingredient."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe")
        async_db_session.add(recipe)
        await async_db_session.flush()

        ingredient = RecipeIngredientFactory.build(recipe_id=recipe.id, ingredient_name="ToDelete")
        async_db_session.add(ingredient)
        await async_db_session.commit()
        ingredient_id = ingredient.id

        await RecipeService.delete_ingredient(async_db_session, ingredient_id)

        # Verify it's gone
        result = await RecipeService.get_ingredients(async_db_session, recipe.id)
        assert len(result) == 0

    async def test_delete_ingredient_raises_for_missing(self, async_db_session):
        """Test that HTTPException is raised when ingredient doesn't exist."""
        fake_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.delete_ingredient(async_db_session, fake_id)

        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
class TestInstructionCRUD:
    """Test instruction CRUD operations."""

    async def test_get_instructions(self, async_db_session, async_test_user):
        """Test getting instructions for a recipe."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe")
        async_db_session.add(recipe)
        await async_db_session.flush()

        inst1 = RecipeInstructionFactory.build(recipe_id=recipe.id, step_number=1, description="Step 1")
        inst2 = RecipeInstructionFactory.build(recipe_id=recipe.id, step_number=2, description="Step 2")
        async_db_session.add(inst1)
        async_db_session.add(inst2)
        await async_db_session.commit()

        result = await RecipeService.get_instructions(async_db_session, recipe.id)

        assert len(result) == 2
        assert result[0].description == "Step 1"
        assert result[1].description == "Step 2"

    async def test_create_instruction(self, async_db_session, async_test_user):
        """Test adding an instruction to a recipe."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe")
        async_db_session.add(recipe)
        await async_db_session.commit()

        instruction_data = RecipeInstructionCreate(
            step_number=1,
            description="Mix all ingredients",
            duration_minutes=5,
        )

        result = await RecipeService.create_instruction(async_db_session, recipe.id, instruction_data)

        assert result is not None
        assert result.description == "Mix all ingredients"
        assert result.duration_minutes == 5

    async def test_create_instruction_raises_for_missing_recipe(self, async_db_session):
        """Test that HTTPException is raised when recipe doesn't exist."""
        fake_id = uuid4()
        instruction_data = RecipeInstructionCreate(step_number=1, description="Do something")

        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.create_instruction(async_db_session, fake_id, instruction_data)

        assert exc_info.value.status_code == 404

    async def test_update_instruction(self, async_db_session, async_test_user):
        """Test updating an instruction."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe")
        async_db_session.add(recipe)
        await async_db_session.flush()

        instruction = RecipeInstructionFactory.build(
            recipe_id=recipe.id,
            step_number=1,
            description="Original",
        )
        async_db_session.add(instruction)
        await async_db_session.commit()

        update_data = RecipeInstructionUpdate(description="Updated", duration_minutes=10)
        result = await RecipeService.update_instruction(async_db_session, instruction.id, update_data)

        assert result.description == "Updated"
        assert result.duration_minutes == 10

    async def test_update_instruction_raises_for_missing(self, async_db_session):
        """Test that HTTPException is raised when instruction doesn't exist."""
        fake_id = uuid4()
        update_data = RecipeInstructionUpdate(description="Whatever")

        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.update_instruction(async_db_session, fake_id, update_data)

        assert exc_info.value.status_code == 404

    async def test_delete_instruction(self, async_db_session, async_test_user):
        """Test deleting an instruction."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe")
        async_db_session.add(recipe)
        await async_db_session.flush()

        instruction = RecipeInstructionFactory.build(recipe_id=recipe.id, step_number=1, description="ToDelete")
        async_db_session.add(instruction)
        await async_db_session.commit()
        instruction_id = instruction.id

        await RecipeService.delete_instruction(async_db_session, instruction_id)

        # Verify it's gone
        result = await RecipeService.get_instructions(async_db_session, recipe.id)
        assert len(result) == 0

    async def test_delete_instruction_raises_for_missing(self, async_db_session):
        """Test that HTTPException is raised when instruction doesn't exist."""
        fake_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await RecipeService.delete_instruction(async_db_session, fake_id)

        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
class TestFindCommonIngredient:
    """Test the find_common_ingredient helper."""

    async def test_finds_by_alias(self, async_db_session):
        """Test finding common ingredient by alias."""
        common = CommonIngredientFactory.build(name="all-purpose flour", category="pantry")
        async_db_session.add(common)
        await async_db_session.flush()

        alias = IngredientAliasFactory.build(common_ingredient_id=common.id, alias="flour")
        async_db_session.add(alias)
        await async_db_session.commit()

        result = await RecipeService.find_common_ingredient(async_db_session, "flour")

        assert result == common.id

    async def test_finds_by_name(self, async_db_session):
        """Test finding common ingredient by exact name."""
        common = CommonIngredientFactory.build(name="butter", category="dairy")
        async_db_session.add(common)
        await async_db_session.commit()

        result = await RecipeService.find_common_ingredient(async_db_session, "butter")

        assert result == common.id

    async def test_case_insensitive(self, async_db_session):
        """Test that search is case-insensitive."""
        common = CommonIngredientFactory.build(name="Milk", category="dairy")
        async_db_session.add(common)
        await async_db_session.commit()

        result = await RecipeService.find_common_ingredient(async_db_session, "MILK")

        assert result == common.id

    async def test_returns_none_when_not_found(self, async_db_session):
        """Test that None is returned when no match found."""
        result = await RecipeService.find_common_ingredient(async_db_session, "nonexistent")

        assert result is None
