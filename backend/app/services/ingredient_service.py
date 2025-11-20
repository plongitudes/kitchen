"""Service layer for ingredient management operations."""

from sqlalchemy import select, func, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID

from app.models.ingredient import CommonIngredient, IngredientAlias
from app.models.recipe import RecipeIngredient, Recipe
from app.schemas.ingredient import (
    CommonIngredientCreate,
    CommonIngredientUpdate,
    CreateMappingRequest,
)


class IngredientService:
    """Service for managing common ingredients and mappings."""

    @staticmethod
    async def get_all_ingredients(
        db: AsyncSession,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[CommonIngredient]:
        """Get all common ingredients with optional filtering."""
        query = select(CommonIngredient).options(selectinload(CommonIngredient.aliases))

        # Apply filters
        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(func.lower(CommonIngredient.name).like(search_term))

        if category:
            query = query.where(CommonIngredient.category == category)

        query = query.order_by(CommonIngredient.name)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_ingredient_by_id(
        db: AsyncSession, ingredient_id: UUID
    ) -> Optional[CommonIngredient]:
        """Get a common ingredient by ID with aliases."""
        query = (
            select(CommonIngredient)
            .options(selectinload(CommonIngredient.aliases))
            .where(CommonIngredient.id == ingredient_id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_recipe_count(db: AsyncSession, ingredient_id: UUID) -> int:
        """Get count of recipes using this common ingredient."""
        query = (
            select(func.count(func.distinct(RecipeIngredient.recipe_id)))
            .where(RecipeIngredient.common_ingredient_id == ingredient_id)
        )
        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def get_recipes_for_ingredient(db: AsyncSession, ingredient_id: UUID) -> List[Recipe]:
        """Get list of active recipes using this common ingredient."""
        query = (
            select(Recipe)
            .join(RecipeIngredient)
            .where(RecipeIngredient.common_ingredient_id == ingredient_id)
            .where(Recipe.retired_at.is_(None))
            .distinct()
            .order_by(Recipe.name)
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_ingredient(
        db: AsyncSession, ingredient_data: CommonIngredientCreate
    ) -> CommonIngredient:
        """Create a new common ingredient."""
        ingredient = CommonIngredient(
            name=ingredient_data.name,
            category=ingredient_data.category,
        )
        db.add(ingredient)
        await db.commit()
        await db.refresh(ingredient)
        return ingredient

    @staticmethod
    async def update_ingredient(
        db: AsyncSession,
        ingredient_id: UUID,
        ingredient_data: CommonIngredientUpdate,
    ) -> Optional[CommonIngredient]:
        """Update a common ingredient."""
        ingredient = await IngredientService.get_ingredient_by_id(db, ingredient_id)
        if not ingredient:
            return None

        # Update fields if provided
        if ingredient_data.name is not None:
            ingredient.name = ingredient_data.name
        if ingredient_data.category is not None:
            ingredient.category = ingredient_data.category

        await db.commit()
        await db.refresh(ingredient)
        return ingredient

    @staticmethod
    async def delete_ingredient(
        db: AsyncSession, ingredient_id: UUID
    ) -> bool:
        """Delete a common ingredient if not in use."""
        # Check if ingredient is in use
        recipe_count = await IngredientService.get_recipe_count(db, ingredient_id)
        if recipe_count > 0:
            return False

        # Delete ingredient (aliases cascade)
        query = delete(CommonIngredient).where(CommonIngredient.id == ingredient_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def delete_alias(
        db: AsyncSession, ingredient_id: UUID, alias_id: UUID
    ) -> bool:
        """Delete an alias from a common ingredient."""
        # Verify the alias belongs to this ingredient
        query = select(IngredientAlias).where(
            IngredientAlias.id == alias_id,
            IngredientAlias.common_ingredient_id == ingredient_id
        )
        result = await db.execute(query)
        alias = result.scalar_one_or_none()

        if not alias:
            return False

        # Delete the alias
        delete_query = delete(IngredientAlias).where(IngredientAlias.id == alias_id)
        await db.execute(delete_query)
        await db.commit()
        return True

    @staticmethod
    async def get_unmapped_ingredients(db: AsyncSession) -> List[dict]:
        """Get list of recipe ingredients with no common_ingredient_id (from active recipes only)."""
        query = (
            select(
                RecipeIngredient.ingredient_name,
                func.count(func.distinct(RecipeIngredient.recipe_id)).label("recipe_count")
            )
            .join(Recipe, Recipe.id == RecipeIngredient.recipe_id)
            .where(RecipeIngredient.common_ingredient_id.is_(None))
            .where(Recipe.retired_at.is_(None))
            .group_by(func.lower(RecipeIngredient.ingredient_name), RecipeIngredient.ingredient_name)
            .order_by(func.count(func.distinct(RecipeIngredient.recipe_id)).desc())
        )
        result = await db.execute(query)
        rows = result.all()

        # Enrich with recipe lists
        unmapped_list = []
        for row in rows:
            # Get recipes for this unmapped ingredient
            recipes_query = (
                select(Recipe)
                .join(RecipeIngredient)
                .where(func.lower(RecipeIngredient.ingredient_name) == row.ingredient_name.lower())
                .where(RecipeIngredient.common_ingredient_id.is_(None))
                .where(Recipe.retired_at.is_(None))
                .distinct()
                .order_by(Recipe.name)
            )
            recipes_result = await db.execute(recipes_query)
            recipes = recipes_result.scalars().all()

            unmapped_list.append({
                "ingredient_name": row.ingredient_name,
                "recipe_count": row.recipe_count,
                "recipes": [{"id": r.id, "name": r.name} for r in recipes]
            })

        return unmapped_list

    @staticmethod
    async def get_recipes_for_unmapped_ingredient(
        db: AsyncSession, ingredient_name: str
    ) -> List[dict]:
        """Get recipes that use an unmapped ingredient (active recipes only)."""
        # First get distinct recipe IDs
        recipe_ids_query = (
            select(RecipeIngredient.recipe_id)
            .where(func.lower(RecipeIngredient.ingredient_name) == ingredient_name.lower())
            .where(RecipeIngredient.common_ingredient_id.is_(None))
            .distinct()
        )

        # Then get the recipe details (excluding retired recipes)
        query = (
            select(Recipe.id, Recipe.name, Recipe.source_url)
            .where(Recipe.id.in_(recipe_ids_query))
            .where(Recipe.retired_at.is_(None))
            .order_by(Recipe.name)
        )
        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "id": str(row.id),
                "name": row.name,
                "source_url": row.source_url,
            }
            for row in rows
        ]

    @staticmethod
    async def map_ingredient(
        db: AsyncSession,
        ingredient_name: str,
        common_ingredient_id: UUID,
    ) -> int:
        """Map an ingredient name to a common ingredient.

        Returns the number of recipe ingredients updated.
        """
        # Verify common ingredient exists
        common_ingredient = await IngredientService.get_ingredient_by_id(
            db, common_ingredient_id
        )
        if not common_ingredient:
            raise ValueError("Common ingredient not found")

        # Create alias if it doesn't exist
        alias_query = select(IngredientAlias).where(
            func.lower(IngredientAlias.alias) == ingredient_name.lower()
        )
        result = await db.execute(alias_query)
        existing_alias = result.scalar_one_or_none()

        if not existing_alias:
            alias = IngredientAlias(
                common_ingredient_id=common_ingredient_id,
                alias=ingredient_name,
            )
            db.add(alias)

        # Update all matching recipe ingredients (case-insensitive)
        update_query = (
            select(RecipeIngredient)
            .where(func.lower(RecipeIngredient.ingredient_name) == ingredient_name.lower())
        )
        result = await db.execute(update_query)
        recipe_ingredients = result.scalars().all()

        count = 0
        for recipe_ingredient in recipe_ingredients:
            recipe_ingredient.common_ingredient_id = common_ingredient_id
            count += 1

        await db.commit()
        return count

    @staticmethod
    async def create_ingredient_with_mapping(
        db: AsyncSession,
        mapping_data: CreateMappingRequest,
    ) -> CommonIngredient:
        """Create a new common ingredient and map an initial alias to it."""
        # Create the common ingredient
        ingredient = CommonIngredient(
            name=mapping_data.name,
            category=mapping_data.category,
        )
        db.add(ingredient)
        await db.flush()  # Get the ID

        # Create the alias
        alias = IngredientAlias(
            common_ingredient_id=ingredient.id,
            alias=mapping_data.initial_alias,
        )
        db.add(alias)

        # Update matching recipe ingredients
        update_query = (
            select(RecipeIngredient)
            .where(func.lower(RecipeIngredient.ingredient_name) == mapping_data.initial_alias.lower())
        )
        result = await db.execute(update_query)
        recipe_ingredients = result.scalars().all()

        for recipe_ingredient in recipe_ingredients:
            recipe_ingredient.common_ingredient_id = ingredient.id

        await db.commit()
        await db.refresh(ingredient)
        return ingredient

    @staticmethod
    async def auto_map_common_ingredients(
        db: AsyncSession,
        min_recipe_count: int = 2,
    ) -> dict:
        """Auto-create common ingredients for unmapped ingredients used in multiple recipes.

        Returns dict with counts of ingredients created and recipe ingredients updated.
        """
        # Get unmapped ingredients used in min_recipe_count or more recipes
        unmapped = await IngredientService.get_unmapped_ingredients(db)
        to_auto_map = [
            ing for ing in unmapped
            if ing["recipe_count"] >= min_recipe_count
        ]

        ingredients_created = 0
        recipe_ingredients_updated = 0

        for unmapped_ing in to_auto_map:
            # Create common ingredient with the exact name
            ingredient = CommonIngredient(
                name=unmapped_ing["ingredient_name"],
                category=None,  # No category - user can add later
            )
            db.add(ingredient)
            await db.flush()

            # Create alias
            alias = IngredientAlias(
                common_ingredient_id=ingredient.id,
                alias=unmapped_ing["ingredient_name"],
            )
            db.add(alias)

            # Update matching recipe ingredients (case-insensitive)
            update_query = (
                select(RecipeIngredient)
                .join(Recipe, Recipe.id == RecipeIngredient.recipe_id)
                .where(func.lower(RecipeIngredient.ingredient_name) == unmapped_ing["ingredient_name"].lower())
                .where(RecipeIngredient.common_ingredient_id.is_(None))
                .where(Recipe.retired_at.is_(None))
            )
            result = await db.execute(update_query)
            recipe_ingredients = result.scalars().all()

            for recipe_ingredient in recipe_ingredients:
                recipe_ingredient.common_ingredient_id = ingredient.id
                recipe_ingredients_updated += 1

            ingredients_created += 1

        await db.commit()

        return {
            "ingredients_created": ingredients_created,
            "recipe_ingredients_updated": recipe_ingredients_updated,
        }

    @staticmethod
    async def merge_ingredients(
        db: AsyncSession,
        source_ingredient_ids: List[UUID],
        target_ingredient_id: UUID,
    ) -> int:
        """Merge multiple common ingredients into a target ingredient.

        Returns the number of recipe ingredients updated.
        """
        # Verify target exists
        target = await IngredientService.get_ingredient_by_id(db, target_ingredient_id)
        if not target:
            raise ValueError("Target ingredient not found")

        # Verify all sources exist and aren't the target
        if target_ingredient_id in source_ingredient_ids:
            raise ValueError("Cannot merge ingredient into itself")

        count = 0
        for source_id in source_ingredient_ids:
            source = await IngredientService.get_ingredient_by_id(db, source_id)
            if not source:
                continue  # Skip non-existent sources

            # Move all aliases from source to target
            for alias in source.aliases:
                alias.common_ingredient_id = target_ingredient_id

            # Update all recipe ingredients using source
            update_query = (
                select(RecipeIngredient)
                .where(RecipeIngredient.common_ingredient_id == source_id)
            )
            result = await db.execute(update_query)
            recipe_ingredients = result.scalars().all()

            for recipe_ingredient in recipe_ingredients:
                recipe_ingredient.common_ingredient_id = target_ingredient_id
                count += 1

            # Delete the source ingredient (aliases already moved)
            await db.delete(source)

        await db.commit()
        return count
