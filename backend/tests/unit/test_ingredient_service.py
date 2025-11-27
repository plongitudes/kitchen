"""
Unit tests for IngredientService.

Tests cover:
- get_all_ingredients: listing with search/category filters
- get_ingredient_by_id: fetching with aliases
- get_recipe_count: counting recipes using an ingredient
- get_recipes_for_ingredient: listing recipes using an ingredient
- create_ingredient: creating common ingredients
- update_ingredient: updating name and category
- delete_ingredient: deleting unused ingredients
- delete_alias: removing aliases
- get_unmapped_ingredients: listing unmapped recipe ingredients
- map_ingredient: mapping ingredient names to common ingredients
- create_ingredient_with_mapping: creating and mapping in one step
- merge_ingredients: merging multiple ingredients into one
"""

import pytest
from uuid import uuid4

from app.services.ingredient_service import IngredientService
from app.schemas.ingredient import (
    CommonIngredientCreate,
    CommonIngredientUpdate,
    CreateMappingRequest,
)
from tests.factories import (
    UserFactory,
    RecipeFactory,
    RecipeIngredientFactory,
    CommonIngredientFactory,
    IngredientAliasFactory,
)


@pytest.mark.asyncio
class TestGetAllIngredients:
    """Test the get_all_ingredients method."""

    async def test_returns_all_ingredients(self, async_db_session):
        """Test that all ingredients are returned."""
        ing1 = CommonIngredientFactory.build(name="Flour", category="pantry")
        ing2 = CommonIngredientFactory.build(name="Sugar", category="pantry")
        async_db_session.add(ing1)
        async_db_session.add(ing2)
        await async_db_session.commit()

        result = await IngredientService.get_all_ingredients(async_db_session)

        names = [i.name for i in result]
        assert "Flour" in names
        assert "Sugar" in names

    async def test_filters_by_search(self, async_db_session):
        """Test that ingredients can be filtered by search term."""
        flour = CommonIngredientFactory.build(name="All-Purpose Flour", category="pantry")
        sugar = CommonIngredientFactory.build(name="Granulated Sugar", category="pantry")
        async_db_session.add(flour)
        async_db_session.add(sugar)
        await async_db_session.commit()

        result = await IngredientService.get_all_ingredients(async_db_session, search="flour")

        names = [i.name for i in result]
        assert "All-Purpose Flour" in names
        assert "Granulated Sugar" not in names

    async def test_filters_by_category(self, async_db_session):
        """Test that ingredients can be filtered by category."""
        flour = CommonIngredientFactory.build(name="Flour Cat", category="pantry")
        milk = CommonIngredientFactory.build(name="Milk Cat", category="dairy")
        async_db_session.add(flour)
        async_db_session.add(milk)
        await async_db_session.commit()

        result = await IngredientService.get_all_ingredients(async_db_session, category="dairy")

        names = [i.name for i in result]
        assert "Milk Cat" in names
        assert "Flour Cat" not in names

    async def test_returns_sorted_by_name(self, async_db_session):
        """Test that ingredients are sorted alphabetically."""
        ing_c = CommonIngredientFactory.build(name="Cinnamon Sort", category="spice")
        ing_a = CommonIngredientFactory.build(name="Apple Sort", category="produce")
        ing_b = CommonIngredientFactory.build(name="Butter Sort", category="dairy")
        async_db_session.add(ing_c)
        async_db_session.add(ing_a)
        async_db_session.add(ing_b)
        await async_db_session.commit()

        result = await IngredientService.get_all_ingredients(async_db_session)

        test_names = [i.name for i in result if i.name.endswith("Sort")]
        assert test_names == sorted(test_names)


@pytest.mark.asyncio
class TestGetIngredientById:
    """Test the get_ingredient_by_id method."""

    async def test_gets_existing_ingredient(self, async_db_session):
        """Test fetching an existing ingredient."""
        ingredient = CommonIngredientFactory.build(name="Fetchable Ingredient", category="pantry")
        async_db_session.add(ingredient)
        await async_db_session.commit()

        result = await IngredientService.get_ingredient_by_id(async_db_session, ingredient.id)

        assert result is not None
        assert result.name == "Fetchable Ingredient"

    async def test_returns_none_for_missing_ingredient(self, async_db_session):
        """Test that None is returned for non-existent ingredient."""
        fake_id = uuid4()

        result = await IngredientService.get_ingredient_by_id(async_db_session, fake_id)

        assert result is None

    async def test_includes_aliases(self, async_db_session):
        """Test that aliases are loaded."""
        ingredient = CommonIngredientFactory.build(name="Ingredient with Aliases", category="pantry")
        async_db_session.add(ingredient)
        await async_db_session.flush()

        alias = IngredientAliasFactory.build(common_ingredient_id=ingredient.id, alias="flour alias")
        async_db_session.add(alias)
        await async_db_session.commit()

        result = await IngredientService.get_ingredient_by_id(async_db_session, ingredient.id)

        assert result is not None
        assert len(result.aliases) == 1
        assert result.aliases[0].alias == "flour alias"


@pytest.mark.asyncio
class TestGetRecipeCount:
    """Test the get_recipe_count method."""

    async def test_counts_recipes_using_ingredient(self, async_db_session, async_test_user):
        """Test counting recipes that use an ingredient."""
        ingredient = CommonIngredientFactory.build(name="Counted Ingredient", category="pantry")
        async_db_session.add(ingredient)
        await async_db_session.flush()

        recipe1 = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe 1")
        recipe2 = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe 2")
        async_db_session.add(recipe1)
        async_db_session.add(recipe2)
        await async_db_session.flush()

        ri1 = RecipeIngredientFactory.build(
            recipe_id=recipe1.id,
            common_ingredient_id=ingredient.id,
            ingredient_name="flour",
        )
        ri2 = RecipeIngredientFactory.build(
            recipe_id=recipe2.id,
            common_ingredient_id=ingredient.id,
            ingredient_name="flour",
        )
        async_db_session.add(ri1)
        async_db_session.add(ri2)
        await async_db_session.commit()

        result = await IngredientService.get_recipe_count(async_db_session, ingredient.id)

        assert result == 2

    async def test_returns_zero_for_unused_ingredient(self, async_db_session):
        """Test that zero is returned for unused ingredient."""
        ingredient = CommonIngredientFactory.build(name="Unused Ingredient", category="pantry")
        async_db_session.add(ingredient)
        await async_db_session.commit()

        result = await IngredientService.get_recipe_count(async_db_session, ingredient.id)

        assert result == 0


@pytest.mark.asyncio
class TestCreateIngredient:
    """Test the create_ingredient method."""

    async def test_creates_ingredient(self, async_db_session):
        """Test creating a common ingredient."""
        ingredient_data = CommonIngredientCreate(
            name="New Common Ingredient",
            category="pantry",
        )

        result = await IngredientService.create_ingredient(async_db_session, ingredient_data)

        assert result is not None
        assert result.name == "New Common Ingredient"
        assert result.category == "pantry"
        assert result.id is not None


@pytest.mark.asyncio
class TestUpdateIngredient:
    """Test the update_ingredient method."""

    async def test_updates_ingredient_name(self, async_db_session):
        """Test updating the ingredient name."""
        ingredient = CommonIngredientFactory.build(name="Original Name", category="pantry")
        async_db_session.add(ingredient)
        await async_db_session.commit()

        update_data = CommonIngredientUpdate(name="Updated Name")
        result = await IngredientService.update_ingredient(
            async_db_session, ingredient.id, update_data
        )

        assert result is not None
        assert result.name == "Updated Name"

    async def test_updates_ingredient_category(self, async_db_session):
        """Test updating the ingredient category."""
        ingredient = CommonIngredientFactory.build(name="Categorize Me", category="pantry")
        async_db_session.add(ingredient)
        await async_db_session.commit()

        update_data = CommonIngredientUpdate(category="dairy")
        result = await IngredientService.update_ingredient(
            async_db_session, ingredient.id, update_data
        )

        assert result is not None
        assert result.category == "dairy"

    async def test_returns_none_for_missing_ingredient(self, async_db_session):
        """Test that None is returned when ingredient doesn't exist."""
        fake_id = uuid4()
        update_data = CommonIngredientUpdate(name="Whatever")

        result = await IngredientService.update_ingredient(
            async_db_session, fake_id, update_data
        )

        assert result is None


@pytest.mark.asyncio
class TestDeleteIngredient:
    """Test the delete_ingredient method."""

    async def test_deletes_unused_ingredient(self, async_db_session):
        """Test that unused ingredients can be deleted."""
        ingredient = CommonIngredientFactory.build(name="To Delete", category="pantry")
        async_db_session.add(ingredient)
        await async_db_session.commit()
        ingredient_id = ingredient.id

        result = await IngredientService.delete_ingredient(async_db_session, ingredient_id)

        assert result is True

        # Verify it's gone
        check = await IngredientService.get_ingredient_by_id(async_db_session, ingredient_id)
        assert check is None

    async def test_cannot_delete_ingredient_in_use(self, async_db_session, async_test_user):
        """Test that ingredients in use cannot be deleted."""
        ingredient = CommonIngredientFactory.build(name="In Use", category="pantry")
        async_db_session.add(ingredient)
        await async_db_session.flush()

        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe Using Ingredient")
        async_db_session.add(recipe)
        await async_db_session.flush()

        ri = RecipeIngredientFactory.build(
            recipe_id=recipe.id,
            common_ingredient_id=ingredient.id,
            ingredient_name="in use flour",
        )
        async_db_session.add(ri)
        await async_db_session.commit()

        result = await IngredientService.delete_ingredient(async_db_session, ingredient.id)

        assert result is False

        # Verify it still exists
        check = await IngredientService.get_ingredient_by_id(async_db_session, ingredient.id)
        assert check is not None


@pytest.mark.asyncio
class TestDeleteAlias:
    """Test the delete_alias method."""

    async def test_deletes_alias(self, async_db_session):
        """Test deleting an alias."""
        ingredient = CommonIngredientFactory.build(name="Has Alias", category="pantry")
        async_db_session.add(ingredient)
        await async_db_session.flush()

        alias = IngredientAliasFactory.build(common_ingredient_id=ingredient.id, alias="alias to delete")
        async_db_session.add(alias)
        await async_db_session.commit()
        alias_id = alias.id

        result = await IngredientService.delete_alias(async_db_session, ingredient.id, alias_id)

        assert result is True

    async def test_returns_false_for_wrong_ingredient(self, async_db_session):
        """Test that False is returned when alias doesn't belong to ingredient."""
        ing1 = CommonIngredientFactory.build(name="Ingredient 1", category="pantry")
        ing2 = CommonIngredientFactory.build(name="Ingredient 2", category="pantry")
        async_db_session.add(ing1)
        async_db_session.add(ing2)
        await async_db_session.flush()

        alias = IngredientAliasFactory.build(common_ingredient_id=ing2.id, alias="belongs to ing2")
        async_db_session.add(alias)
        await async_db_session.commit()

        # Try to delete from wrong ingredient
        result = await IngredientService.delete_alias(async_db_session, ing1.id, alias.id)

        assert result is False

    async def test_returns_false_for_missing_alias(self, async_db_session):
        """Test that False is returned when alias doesn't exist."""
        ingredient = CommonIngredientFactory.build(name="No Such Alias", category="pantry")
        async_db_session.add(ingredient)
        await async_db_session.commit()

        fake_id = uuid4()
        result = await IngredientService.delete_alias(async_db_session, ingredient.id, fake_id)

        assert result is False


@pytest.mark.asyncio
class TestMapIngredient:
    """Test the map_ingredient method."""

    async def test_maps_ingredient_and_creates_alias(self, async_db_session, async_test_user):
        """Test mapping an ingredient name and creating an alias."""
        common = CommonIngredientFactory.build(name="Common Flour", category="pantry")
        async_db_session.add(common)
        await async_db_session.flush()

        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe to Map")
        async_db_session.add(recipe)
        await async_db_session.flush()

        ri = RecipeIngredientFactory.build(
            recipe_id=recipe.id,
            ingredient_name="all-purpose flour",
            common_ingredient_id=None,
        )
        async_db_session.add(ri)
        await async_db_session.commit()

        count = await IngredientService.map_ingredient(
            async_db_session, "all-purpose flour", common.id
        )

        assert count == 1

        # Verify the alias was created by directly querying aliases table
        from sqlalchemy import select
        from app.models.ingredient import IngredientAlias
        alias_query = select(IngredientAlias).where(
            IngredientAlias.common_ingredient_id == common.id
        )
        alias_result = await async_db_session.execute(alias_query)
        aliases = [a.alias for a in alias_result.scalars().all()]
        assert "all-purpose flour" in aliases

    async def test_raises_for_missing_common_ingredient(self, async_db_session):
        """Test that ValueError is raised when common ingredient doesn't exist."""
        fake_id = uuid4()

        with pytest.raises(ValueError) as exc_info:
            await IngredientService.map_ingredient(async_db_session, "flour", fake_id)

        assert "Common ingredient not found" in str(exc_info.value)


@pytest.mark.asyncio
class TestCreateIngredientWithMapping:
    """Test the create_ingredient_with_mapping method."""

    async def test_creates_and_maps(self, async_db_session, async_test_user):
        """Test creating an ingredient with an initial mapping."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe for Mapping")
        async_db_session.add(recipe)
        await async_db_session.flush()

        ri = RecipeIngredientFactory.build(
            recipe_id=recipe.id,
            ingredient_name="brown sugar",
            common_ingredient_id=None,
        )
        async_db_session.add(ri)
        await async_db_session.commit()

        mapping_data = CreateMappingRequest(
            name="Brown Sugar",
            category="pantry",
            initial_alias="brown sugar",
        )

        result = await IngredientService.create_ingredient_with_mapping(
            async_db_session, mapping_data
        )

        assert result is not None
        assert result.name == "Brown Sugar"
        assert result.category == "pantry"

        # Verify alias was created by directly querying aliases table
        from sqlalchemy import select
        from app.models.ingredient import IngredientAlias
        alias_query = select(IngredientAlias).where(
            IngredientAlias.common_ingredient_id == result.id
        )
        alias_result = await async_db_session.execute(alias_query)
        aliases = alias_result.scalars().all()
        assert len(aliases) >= 1


@pytest.mark.asyncio
class TestMergeIngredients:
    """Test the merge_ingredients method."""

    async def test_merges_ingredients(self, async_db_session, async_test_user):
        """Test merging multiple ingredients into one."""
        target = CommonIngredientFactory.build(name="Target Ingredient", category="pantry")
        source = CommonIngredientFactory.build(name="Source Ingredient", category="pantry")
        async_db_session.add(target)
        async_db_session.add(source)
        await async_db_session.flush()

        source_alias = IngredientAliasFactory.build(common_ingredient_id=source.id, alias="source alias")
        async_db_session.add(source_alias)
        await async_db_session.flush()

        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Merge Test Recipe")
        async_db_session.add(recipe)
        await async_db_session.flush()

        ri = RecipeIngredientFactory.build(
            recipe_id=recipe.id,
            ingredient_name="source flour",
            common_ingredient_id=source.id,
        )
        async_db_session.add(ri)
        await async_db_session.commit()

        count = await IngredientService.merge_ingredients(
            async_db_session, [source.id], target.id
        )

        assert count == 1

        # Verify source is deleted
        source_check = await IngredientService.get_ingredient_by_id(async_db_session, source.id)
        assert source_check is None

    async def test_raises_for_missing_target(self, async_db_session):
        """Test that ValueError is raised when target doesn't exist."""
        source = CommonIngredientFactory.build(name="Source Only", category="pantry")
        async_db_session.add(source)
        await async_db_session.commit()

        fake_id = uuid4()

        with pytest.raises(ValueError) as exc_info:
            await IngredientService.merge_ingredients(
                async_db_session, [source.id], fake_id
            )

        assert "Target ingredient not found" in str(exc_info.value)

    async def test_raises_for_self_merge(self, async_db_session):
        """Test that ValueError is raised when trying to merge into self."""
        ingredient = CommonIngredientFactory.build(name="Self Merge", category="pantry")
        async_db_session.add(ingredient)
        await async_db_session.commit()

        with pytest.raises(ValueError) as exc_info:
            await IngredientService.merge_ingredients(
                async_db_session, [ingredient.id], ingredient.id
            )

        assert "Cannot merge ingredient into itself" in str(exc_info.value)


@pytest.mark.asyncio
class TestGetUnmappedIngredients:
    """Test the get_unmapped_ingredients method."""

    async def test_returns_unmapped_ingredients(self, async_db_session, async_test_user):
        """Test getting list of unmapped ingredient names."""
        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe with Unmapped")
        async_db_session.add(recipe)
        await async_db_session.flush()

        ri = RecipeIngredientFactory.build(
            recipe_id=recipe.id,
            ingredient_name="unmapped ingredient",
            common_ingredient_id=None,
        )
        async_db_session.add(ri)
        await async_db_session.commit()

        result = await IngredientService.get_unmapped_ingredients(async_db_session)

        names = [r["ingredient_name"] for r in result]
        assert "unmapped ingredient" in names

    async def test_excludes_mapped_ingredients(self, async_db_session, async_test_user):
        """Test that mapped ingredients are excluded."""
        common = CommonIngredientFactory.build(name="Common Mapped", category="pantry")
        async_db_session.add(common)
        await async_db_session.flush()

        recipe = RecipeFactory.build(owner_id=async_test_user.id, name="Recipe with Mapped")
        async_db_session.add(recipe)
        await async_db_session.flush()

        ri = RecipeIngredientFactory.build(
            recipe_id=recipe.id,
            ingredient_name="mapped ingredient",
            common_ingredient_id=common.id,
        )
        async_db_session.add(ri)
        await async_db_session.commit()

        result = await IngredientService.get_unmapped_ingredients(async_db_session)

        names = [r["ingredient_name"] for r in result]
        assert "mapped ingredient" not in names
