"""
Service layer for recipe business logic.

Handles recipe CRUD, retirement validation, and template usage checking.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete, exists
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from recipe_scrapers import scrape_me, scrape_html, WebsiteNotImplementedError

from app.models.recipe import (
    Recipe,
    RecipeIngredient,
    RecipeInstruction,
    RecipePrepStep,
    PrepStepIngredient,
)
from app.models.ingredient import CommonIngredient, IngredientAlias
from app.models.schedule import WeekDayAssignment
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    RecipeIngredientCreate,
    RecipeIngredientUpdate,
    RecipeInstructionCreate,
    RecipeInstructionUpdate,
    RecipePrepStepCreate,
    RecipePrepStepUpdate,
    RecipePrepStepResponse,
    RecipeImportPreviewResponse,
    RecipeImportPreviewIngredient,
    RecipeImportPreviewInstruction,
)
from app.utils.ingredient_parser import parse_ingredient_line

logger = logging.getLogger(__name__)


class RecipeService:
    """Service layer for recipe business logic."""

    # ========================================================================
    # Ingredient Normalization Helper
    # ========================================================================

    @staticmethod
    async def find_common_ingredient(
        db: AsyncSession,
        ingredient_name: str,
    ) -> Optional[UUID]:
        """
        Find matching common ingredient ID for an ingredient name.

        Searches aliases (case-insensitive) and returns the common_ingredient_id if found.
        Returns None if no match.
        """
        # Search for alias match (case-insensitive)
        query = select(IngredientAlias).where(IngredientAlias.alias.ilike(ingredient_name.strip()))
        result = await db.execute(query)
        alias = result.scalar_one_or_none()

        if alias:
            return alias.common_ingredient_id

        # Also check if it matches a common ingredient name directly
        query = select(CommonIngredient).where(CommonIngredient.name.ilike(ingredient_name.strip()))
        result = await db.execute(query)
        common_ing = result.scalar_one_or_none()

        if common_ing:
            return common_ing.id

        return None

    # ========================================================================
    # Recipe Methods
    # ========================================================================

    @staticmethod
    async def get_recipes(
        db: AsyncSession,
        owner_id: Optional[UUID] = None,
        include_retired: bool = False,
        recipe_type: Optional[str] = None,
    ) -> List[Recipe]:
        """Get list of recipes with optional filtering."""
        query = select(Recipe).options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.prep_step_links),
            selectinload(Recipe.instructions),
            selectinload(Recipe.prep_steps).selectinload(RecipePrepStep.ingredient_links),
        )

        # Filter by owner
        if owner_id:
            query = query.where(Recipe.owner_id == owner_id)

        # Filter by recipe type
        if recipe_type:
            query = query.where(Recipe.recipe_type == recipe_type)

        # Exclude retired by default
        if not include_retired:
            query = query.where(Recipe.retired_at.is_(None))

        query = query.order_by(Recipe.name)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_recipe_by_id(
        db: AsyncSession,
        recipe_id: UUID,
    ) -> Optional[Recipe]:
        """Get a single recipe by ID with ingredients, instructions, and prep steps."""
        query = (
            select(Recipe)
            .where(Recipe.id == recipe_id)
            .options(
                selectinload(Recipe.ingredients).selectinload(RecipeIngredient.prep_step_links),
                selectinload(Recipe.instructions),
                selectinload(Recipe.prep_steps).selectinload(RecipePrepStep.ingredient_links),
            )
        )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_recipe(
        db: AsyncSession,
        recipe_data: RecipeCreate,
        owner_id: UUID,
    ) -> Recipe:
        """Create a new recipe with ingredients and instructions."""
        # Create recipe
        recipe = Recipe(
            owner_id=owner_id,
            name=recipe_data.name,
            index_name=recipe_data.index_name,
            recipe_type=recipe_data.recipe_type,
            description=recipe_data.description,
            prep_time_minutes=recipe_data.prep_time_minutes,
            cook_time_minutes=recipe_data.cook_time_minutes,
            prep_notes=recipe_data.prep_notes,
            postmortem_notes=recipe_data.postmortem_notes,
            source_url=recipe_data.source_url,
        )

        db.add(recipe)
        await db.flush()  # Get recipe.id

        # Create ingredients with prep step support
        if recipe_data.ingredients:
            # Initialize empty prep step cache (new recipe has no prep steps yet)
            prep_step_map: dict[str, RecipePrepStep] = {}

            for ing_data in recipe_data.ingredients:
                # Use create_ingredient to handle prep_step_description
                await RecipeService.create_ingredient(
                    db=db,
                    recipe_id=recipe.id,
                    ingredient_data=ing_data,
                    prep_step_map=prep_step_map,
                )

        # Create instructions
        if recipe_data.instructions:
            for inst_data in recipe_data.instructions:
                instruction = RecipeInstruction(
                    recipe_id=recipe.id,
                    step_number=inst_data.step_number,
                    description=inst_data.description,
                    duration_minutes=inst_data.duration_minutes,
                )
                db.add(instruction)

        await db.flush()  # Ensure ingredients have IDs

        # Create prep steps with ingredient links (legacy direct prep_steps API)
        if recipe_data.prep_steps:
            # Query ingredients we just created to build order -> id mapping
            ing_query = select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe.id)
            ing_result = await db.execute(ing_query)
            created_ingredients = ing_result.scalars().all()

            ingredient_by_order = {}
            for ing in created_ingredients:
                ingredient_by_order[ing.order] = ing.id

            for prep_data in recipe_data.prep_steps:
                prep_step = RecipePrepStep(
                    recipe_id=recipe.id,
                    description=prep_data.description,
                    order=prep_data.order,
                )
                db.add(prep_step)
                await db.flush()  # Get prep_step.id

                # Link to ingredients - support both ingredient_orders and ingredient_ids
                ingredient_ids_to_link = []
                if prep_data.ingredient_orders:
                    # Map order values to actual ingredient IDs
                    for order in prep_data.ingredient_orders:
                        if order in ingredient_by_order:
                            ingredient_ids_to_link.append(ingredient_by_order[order])
                elif prep_data.ingredient_ids:
                    ingredient_ids_to_link = prep_data.ingredient_ids

                for ing_id in ingredient_ids_to_link:
                    link = PrepStepIngredient(
                        prep_step_id=prep_step.id,
                        recipe_ingredient_id=ing_id,
                    )
                    db.add(link)

        await db.commit()
        await db.refresh(recipe)

        # Load relationships for response
        recipe = await RecipeService.get_recipe_by_id(db=db, recipe_id=recipe.id)
        return recipe

    @staticmethod
    async def update_recipe(
        db: AsyncSession,
        recipe_id: UUID,
        recipe_data: RecipeUpdate,
    ) -> Recipe:
        """Update a recipe."""
        recipe = await RecipeService.get_recipe_by_id(db=db, recipe_id=recipe_id)

        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )

        # Update fields
        if recipe_data.name is not None:
            recipe.name = recipe_data.name
        if hasattr(recipe_data, "index_name") and recipe_data.index_name is not None:
            recipe.index_name = recipe_data.index_name
        if recipe_data.recipe_type is not None:
            recipe.recipe_type = recipe_data.recipe_type
        if recipe_data.prep_time_minutes is not None:
            recipe.prep_time_minutes = recipe_data.prep_time_minutes
        if recipe_data.cook_time_minutes is not None:
            recipe.cook_time_minutes = recipe_data.cook_time_minutes
        if recipe_data.prep_notes is not None:
            recipe.prep_notes = recipe_data.prep_notes
        if recipe_data.postmortem_notes is not None:
            recipe.postmortem_notes = recipe_data.postmortem_notes
        if recipe_data.source_url is not None:
            recipe.source_url = recipe_data.source_url
        if recipe_data.owner_id is not None:
            recipe.owner_id = recipe_data.owner_id

        # Handle ingredients replacement if provided
        if recipe_data.ingredients is not None:
            # Delete existing ingredients (cascade deletes prep step links)
            for ingredient in recipe.ingredients:
                await db.delete(ingredient)
            await db.flush()

            # Clean up orphaned prep steps (those with no ingredient links)
            # Using NOT EXISTS is more efficient than LEFT JOIN for this pattern
            orphaned_prep_steps_query = select(RecipePrepStep).where(
                RecipePrepStep.recipe_id == recipe.id,
                ~exists(
                    select(1)
                    .where(PrepStepIngredient.prep_step_id == RecipePrepStep.id)
                    .correlate(RecipePrepStep)
                ),
            )
            orphaned_result = await db.execute(orphaned_prep_steps_query)
            orphaned_prep_steps = orphaned_result.scalars().all()
            for orphan in orphaned_prep_steps:
                await db.delete(orphan)
            await db.flush()

            # Fetch existing prep steps once to avoid N+1 queries
            existing_prep_steps_query = select(RecipePrepStep).where(
                RecipePrepStep.recipe_id == recipe.id
            )
            existing_prep_steps_result = await db.execute(existing_prep_steps_query)
            prep_step_map = {
                step.description: step for step in existing_prep_steps_result.scalars().all()
            }

            # Add new ingredients with prep step support
            for ing_data in recipe_data.ingredients:
                await RecipeService.create_ingredient(
                    db=db,
                    recipe_id=recipe.id,
                    ingredient_data=ing_data,
                    prep_step_map=prep_step_map,
                )

        # Handle instructions replacement if provided
        if recipe_data.instructions is not None:
            # Delete existing instructions
            for instruction in recipe.instructions:
                await db.delete(instruction)
            await db.flush()

            # Add new instructions
            for inst_data in recipe_data.instructions:
                instruction = RecipeInstruction(
                    recipe_id=recipe.id,
                    step_number=inst_data.step_number,
                    description=inst_data.description,
                    duration_minutes=inst_data.duration_minutes,
                )
                db.add(instruction)

        # Handle prep steps replacement if provided (legacy direct prep_steps API)
        if recipe_data.prep_steps is not None:
            # Delete existing prep steps and links
            for prep_step in recipe.prep_steps:
                await db.delete(prep_step)
            await db.flush()

            # Query ingredients to build order -> id mapping (for ingredient_orders)
            ing_query = select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe.id)
            ing_result = await db.execute(ing_query)
            created_ingredients = ing_result.scalars().all()

            ingredient_by_order = {}
            for ing in created_ingredients:
                ingredient_by_order[ing.order] = ing.id

            # Create new prep steps with ingredient links
            for prep_data in recipe_data.prep_steps:
                prep_step = RecipePrepStep(
                    recipe_id=recipe.id,
                    description=prep_data.description,
                    order=prep_data.order,
                )
                db.add(prep_step)
                await db.flush()  # Get prep_step.id

                # Link to ingredients - support both ingredient_orders and ingredient_ids
                ingredient_ids_to_link = []
                if prep_data.ingredient_orders:
                    # Map order values to actual ingredient IDs
                    for order in prep_data.ingredient_orders:
                        if order in ingredient_by_order:
                            ingredient_ids_to_link.append(ingredient_by_order[order])
                elif prep_data.ingredient_ids:
                    ingredient_ids_to_link = prep_data.ingredient_ids

                for ing_id in ingredient_ids_to_link:
                    link = PrepStepIngredient(
                        prep_step_id=prep_step.id,
                        recipe_ingredient_id=ing_id,
                    )
                    db.add(link)

        await db.commit()
        await db.refresh(recipe)

        # Reload with relationships if any nested data was updated
        if (
            recipe_data.ingredients is not None
            or recipe_data.instructions is not None
            or recipe_data.prep_steps is not None
        ):
            recipe = await RecipeService.get_recipe_by_id(db=db, recipe_id=recipe.id)

        return recipe

    @staticmethod
    async def delete_recipe(
        db: AsyncSession,
        recipe_id: UUID,
    ) -> Recipe:
        """Soft delete (retire) a recipe with validation."""
        recipe = await RecipeService.get_recipe_by_id(db=db, recipe_id=recipe_id)

        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )

        if recipe.retired_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recipe is already retired",
            )

        # Check if recipe is used in any active week templates
        templates_using_recipe = await RecipeService.check_recipe_usage(
            db=db,
            recipe_id=recipe_id,
        )

        if templates_using_recipe:
            template_names = [t["name"] for t in templates_using_recipe]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot retire recipe - it is used in active week templates: {', '.join(template_names)}",
            )

        # Soft delete
        recipe.retired_at = datetime.utcnow()

        await db.commit()
        await db.refresh(recipe)

        return recipe

    @staticmethod
    async def restore_recipe(
        db: AsyncSession,
        recipe_id: UUID,
    ) -> Recipe:
        """Restore a retired recipe."""
        recipe = await RecipeService.get_recipe_by_id(db=db, recipe_id=recipe_id)

        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )

        if not recipe.retired_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recipe is not retired",
            )

        recipe.retired_at = None

        await db.commit()
        await db.refresh(recipe)

        return recipe

    @staticmethod
    async def check_recipe_usage(
        db: AsyncSession,
        recipe_id: UUID,
    ) -> List[dict]:
        """Check which active week templates use this recipe."""
        from app.models.schedule import WeekTemplate

        # Find all assignments using this recipe in non-retired templates
        query = (
            select(WeekTemplate)
            .join(WeekDayAssignment)
            .where(
                and_(
                    WeekDayAssignment.recipe_id == recipe_id,
                    WeekTemplate.retired_at.is_(None),
                )
            )
            .distinct()
        )

        result = await db.execute(query)
        templates = result.scalars().all()

        return [
            {
                "template_id": str(template.id),
                "name": template.name,
            }
            for template in templates
        ]

    # ========================================================================
    # Ingredient Methods
    # ========================================================================

    @staticmethod
    async def get_ingredients(
        db: AsyncSession,
        recipe_id: UUID,
    ) -> List[RecipeIngredient]:
        """Get all ingredients for a recipe."""
        query = (
            select(RecipeIngredient)
            .where(RecipeIngredient.recipe_id == recipe_id)
            .order_by(RecipeIngredient.order)
        )

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_ingredient(
        db: AsyncSession,
        recipe_id: UUID,
        ingredient_data: RecipeIngredientCreate,
        prep_step_map: dict[str, RecipePrepStep],
    ) -> RecipeIngredient:
        """Add an ingredient to a recipe.

        Args:
            db: Database session
            recipe_id: ID of the recipe
            ingredient_data: Ingredient data to create
            prep_step_map: Cache of existing prep steps by description.
                          Will be updated with any newly created prep steps
                          to prevent duplicates.

        Returns:
            Created RecipeIngredient instance
        """
        # Verify recipe exists
        recipe = await RecipeService.get_recipe_by_id(db=db, recipe_id=recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )

        # Try to find matching common ingredient
        common_ingredient_id = await RecipeService.find_common_ingredient(
            db, ingredient_data.ingredient_name
        )

        ingredient = RecipeIngredient(
            recipe_id=recipe_id,
            ingredient_name=ingredient_data.ingredient_name,
            quantity=ingredient_data.quantity,
            unit=ingredient_data.unit,
            order=ingredient_data.order,
            common_ingredient_id=common_ingredient_id,  # Auto-matched or None
            prep_note=ingredient_data.prep_note,
            is_indexed=ingredient_data.is_indexed,
        )

        db.add(ingredient)
        await db.flush()  # Get ingredient.id before linking prep steps

        # Handle prep step linking
        if ingredient_data.prep_step_id:
            # Link to existing prep step
            link = PrepStepIngredient(
                prep_step_id=ingredient_data.prep_step_id,
                recipe_ingredient_id=ingredient.id,
            )
            db.add(link)
        elif ingredient_data.prep_step_description:
            # Check if prep step already exists in our cache
            description = ingredient_data.prep_step_description.strip()

            if description in prep_step_map:
                # Reuse existing prep step from cache
                prep_step_id = prep_step_map[description].id
            else:
                # Create new prep step
                next_order = len(prep_step_map)
                new_prep_step = RecipePrepStep(
                    recipe_id=recipe_id,
                    description=description,
                    order=next_order,
                )
                db.add(new_prep_step)
                await db.flush()
                prep_step_id = new_prep_step.id

                # Add to cache for subsequent ingredients
                prep_step_map[description] = new_prep_step

            # Link ingredient to prep step (whether new or existing)
            link = PrepStepIngredient(
                prep_step_id=prep_step_id,
                recipe_ingredient_id=ingredient.id,
            )
            db.add(link)

        await db.commit()
        await db.refresh(ingredient)

        return ingredient

    @staticmethod
    async def add_ingredient(
        db: AsyncSession,
        recipe_id: UUID,
        ingredient_data: RecipeIngredientCreate,
    ) -> RecipeIngredient:
        """Alias for create_ingredient for API compatibility."""
        # Fetch existing prep steps for this recipe
        existing_prep_steps_query = select(RecipePrepStep).where(
            RecipePrepStep.recipe_id == recipe_id
        )
        existing_prep_steps_result = await db.execute(existing_prep_steps_query)
        prep_step_map = {
            step.description: step for step in existing_prep_steps_result.scalars().all()
        }

        return await RecipeService.create_ingredient(db, recipe_id, ingredient_data, prep_step_map)

    @staticmethod
    async def update_ingredient(
        db: AsyncSession,
        ingredient_id: UUID,
        ingredient_data: RecipeIngredientUpdate,
    ) -> RecipeIngredient:
        """Update a recipe ingredient."""
        query = select(RecipeIngredient).where(RecipeIngredient.id == ingredient_id)
        result = await db.execute(query)
        ingredient = result.scalar_one_or_none()

        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingredient not found",
            )

        # Track prep steps to potentially clean up
        old_prep_step_ids = []

        # Update fields
        if ingredient_data.ingredient_name is not None:
            ingredient.ingredient_name = ingredient_data.ingredient_name
        if ingredient_data.quantity is not None:
            ingredient.quantity = ingredient_data.quantity
        if ingredient_data.unit is not None:
            ingredient.unit = ingredient_data.unit
        if ingredient_data.order is not None:
            ingredient.order = ingredient_data.order
        if ingredient_data.prep_note is not None:
            ingredient.prep_note = ingredient_data.prep_note
        if hasattr(ingredient_data, "is_indexed") and ingredient_data.is_indexed is not None:
            ingredient.is_indexed = ingredient_data.is_indexed

        # Handle prep step linking/unlinking
        if hasattr(ingredient_data, "prep_step_id"):
            # Get current prep step links
            current_links_query = select(PrepStepIngredient).where(
                PrepStepIngredient.recipe_ingredient_id == ingredient_id
            )
            current_links_result = await db.execute(current_links_query)
            current_links = current_links_result.scalars().all()
            old_prep_step_ids = [link.prep_step_id for link in current_links]

            # Remove all existing links
            for link in current_links:
                await db.delete(link)

            # Add new link if provided
            if ingredient_data.prep_step_id is not None:
                new_link = PrepStepIngredient(
                    prep_step_id=ingredient_data.prep_step_id,
                    recipe_ingredient_id=ingredient_id,
                )
                db.add(new_link)
        elif (
            hasattr(ingredient_data, "prep_step_description")
            and ingredient_data.prep_step_description
        ):
            # Create new prep step and link
            # Get current links to remove
            current_links_query = select(PrepStepIngredient).where(
                PrepStepIngredient.recipe_ingredient_id == ingredient_id
            )
            current_links_result = await db.execute(current_links_query)
            current_links = current_links_result.scalars().all()
            old_prep_step_ids = [link.prep_step_id for link in current_links]

            # Remove existing links
            for link in current_links:
                await db.delete(link)

            # Get recipe_id from ingredient
            recipe_id = ingredient.recipe_id

            # Get next order number
            prep_steps_query = select(RecipePrepStep).where(RecipePrepStep.recipe_id == recipe_id)
            existing_prep_steps = await db.execute(prep_steps_query)
            next_order = len(existing_prep_steps.scalars().all())

            # Create new prep step
            new_prep_step = RecipePrepStep(
                recipe_id=recipe_id,
                description=ingredient_data.prep_step_description,
                order=next_order,
            )
            db.add(new_prep_step)
            await db.flush()

            # Link to new prep step
            new_link = PrepStepIngredient(
                prep_step_id=new_prep_step.id,
                recipe_ingredient_id=ingredient_id,
            )
            db.add(new_link)

        await db.flush()

        # Clean up orphaned prep steps (prep steps with no linked ingredients)
        for old_prep_step_id in old_prep_step_ids:
            # Check if this prep step still has any links
            links_check = select(PrepStepIngredient).where(
                PrepStepIngredient.prep_step_id == old_prep_step_id
            )
            remaining_links = await db.execute(links_check)
            if remaining_links.scalars().first() is None:
                # No more links - delete the orphaned prep step
                prep_step_query = select(RecipePrepStep).where(
                    RecipePrepStep.id == old_prep_step_id
                )
                prep_step_result = await db.execute(prep_step_query)
                prep_step = prep_step_result.scalar_one_or_none()
                if prep_step:
                    await db.delete(prep_step)

        await db.commit()
        await db.refresh(ingredient)

        return ingredient

    @staticmethod
    async def delete_ingredient(
        db: AsyncSession,
        ingredient_id: UUID,
    ) -> None:
        """Delete a recipe ingredient."""
        query = select(RecipeIngredient).where(RecipeIngredient.id == ingredient_id)
        result = await db.execute(query)
        ingredient = result.scalar_one_or_none()

        if not ingredient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingredient not found",
            )

        await db.delete(ingredient)
        await db.commit()

    # ========================================================================
    # Instruction Methods
    # ========================================================================

    @staticmethod
    async def get_instructions(
        db: AsyncSession,
        recipe_id: UUID,
    ) -> List[RecipeInstruction]:
        """Get all instructions for a recipe."""
        query = (
            select(RecipeInstruction)
            .where(RecipeInstruction.recipe_id == recipe_id)
            .order_by(RecipeInstruction.step_number)
        )

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_instruction(
        db: AsyncSession,
        recipe_id: UUID,
        instruction_data: RecipeInstructionCreate,
    ) -> RecipeInstruction:
        """Add an instruction to a recipe."""
        # Verify recipe exists
        recipe = await RecipeService.get_recipe_by_id(db=db, recipe_id=recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )

        instruction = RecipeInstruction(
            recipe_id=recipe_id,
            step_number=instruction_data.step_number,
            description=instruction_data.description,
            duration_minutes=instruction_data.duration_minutes,
        )

        db.add(instruction)
        await db.commit()
        await db.refresh(instruction)

        return instruction

    @staticmethod
    async def update_instruction(
        db: AsyncSession,
        instruction_id: UUID,
        instruction_data: RecipeInstructionUpdate,
    ) -> RecipeInstruction:
        """Update a recipe instruction."""
        query = select(RecipeInstruction).where(RecipeInstruction.id == instruction_id)
        result = await db.execute(query)
        instruction = result.scalar_one_or_none()

        if not instruction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instruction not found",
            )

        # Update fields
        if instruction_data.step_number is not None:
            instruction.step_number = instruction_data.step_number
        if instruction_data.description is not None:
            instruction.description = instruction_data.description
        if instruction_data.duration_minutes is not None:
            instruction.duration_minutes = instruction_data.duration_minutes

        await db.commit()
        await db.refresh(instruction)

        return instruction

    @staticmethod
    async def delete_instruction(
        db: AsyncSession,
        instruction_id: UUID,
    ) -> None:
        """Delete a recipe instruction."""
        query = select(RecipeInstruction).where(RecipeInstruction.id == instruction_id)
        result = await db.execute(query)
        instruction = result.scalar_one_or_none()

        if not instruction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instruction not found",
            )

        await db.delete(instruction)
        await db.commit()

    # ========================================================================
    # Prep Step Methods
    # ========================================================================

    @staticmethod
    async def get_prep_steps(
        db: AsyncSession,
        recipe_id: UUID,
    ) -> List[RecipePrepStep]:
        """Get all prep steps for a recipe."""
        query = (
            select(RecipePrepStep)
            .where(RecipePrepStep.recipe_id == recipe_id)
            .options(selectinload(RecipePrepStep.ingredient_links))
            .order_by(RecipePrepStep.order)
        )

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_prep_step(
        db: AsyncSession,
        recipe_id: UUID,
        prep_step_data: RecipePrepStepCreate,
    ) -> RecipePrepStep:
        """Add a prep step to a recipe."""
        # Verify recipe exists
        recipe = await RecipeService.get_recipe_by_id(db=db, recipe_id=recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )

        prep_step = RecipePrepStep(
            recipe_id=recipe_id,
            description=prep_step_data.description,
            order=prep_step_data.order,
        )

        db.add(prep_step)
        await db.flush()

        # Build ingredient ID set for validation
        ingredient_ids_set = {ing.id for ing in recipe.ingredients}

        # Link to ingredients
        ingredient_ids_to_link = []
        if prep_step_data.ingredient_orders:
            ingredient_by_order = {ing.order: ing.id for ing in recipe.ingredients}
            for order in prep_step_data.ingredient_orders:
                if order in ingredient_by_order:
                    ingredient_ids_to_link.append(ingredient_by_order[order])
        elif prep_step_data.ingredient_ids:
            ingredient_ids_to_link = [
                ing_id for ing_id in prep_step_data.ingredient_ids if ing_id in ingredient_ids_set
            ]

        for ing_id in ingredient_ids_to_link:
            link = PrepStepIngredient(
                prep_step_id=prep_step.id,
                recipe_ingredient_id=ing_id,
            )
            db.add(link)

        await db.commit()

        # Reload with relationships
        query = (
            select(RecipePrepStep)
            .where(RecipePrepStep.id == prep_step.id)
            .options(selectinload(RecipePrepStep.ingredient_links))
        )
        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def update_prep_step(
        db: AsyncSession,
        prep_step_id: UUID,
        prep_step_data: RecipePrepStepUpdate,
    ) -> RecipePrepStep:
        """Update a recipe prep step."""
        query = (
            select(RecipePrepStep)
            .where(RecipePrepStep.id == prep_step_id)
            .options(selectinload(RecipePrepStep.ingredient_links))
        )
        result = await db.execute(query)
        prep_step = result.scalar_one_or_none()

        if not prep_step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prep step not found",
            )

        # Update fields
        if prep_step_data.description is not None:
            prep_step.description = prep_step_data.description
        if prep_step_data.order is not None:
            prep_step.order = prep_step_data.order

        # Update ingredient links if provided
        if prep_step_data.ingredient_ids is not None:
            # Delete existing links using bulk delete
            await db.execute(
                delete(PrepStepIngredient).where(PrepStepIngredient.prep_step_id == prep_step.id)
            )
            await db.flush()

            # Get recipe to validate ingredient IDs
            recipe = await RecipeService.get_recipe_by_id(db=db, recipe_id=prep_step.recipe_id)
            ingredient_ids_set = {ing.id for ing in recipe.ingredients}

            # Add new links
            for ing_id in prep_step_data.ingredient_ids:
                if ing_id in ingredient_ids_set:
                    link = PrepStepIngredient(
                        prep_step_id=prep_step.id,
                        recipe_ingredient_id=ing_id,
                    )
                    db.add(link)

        await db.commit()

        # Refresh the prep_step object to get fresh relationship data
        await db.refresh(prep_step, ["ingredient_links"])
        return prep_step

    @staticmethod
    async def delete_prep_step(
        db: AsyncSession,
        prep_step_id: UUID,
    ) -> None:
        """Delete a recipe prep step."""
        query = select(RecipePrepStep).where(RecipePrepStep.id == prep_step_id)
        result = await db.execute(query)
        prep_step = result.scalar_one_or_none()

        if not prep_step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prep step not found",
            )

        await db.delete(prep_step)
        await db.commit()

    # ========================================================================
    # Recipe Import Methods
    # ========================================================================

    @staticmethod
    async def import_recipe_preview(url: str) -> RecipeImportPreviewResponse:
        """Import and preview recipe from URL without saving to database.

        Attempts to scrape from 551 supported sites first, then falls back to
        generic schema.org parsing for unsupported sites.

        Args:
            url: The URL to scrape the recipe from

        Returns:
            RecipeImportPreviewResponse with scraped data

        Raises:
            HTTPException: If website not supported or scraping fails
        """
        scraper = None
        used_fallback = False

        try:
            # Try supported sites first
            scraper = scrape_me(url)
        except WebsiteNotImplementedError:
            # Fallback to generic schema.org parsing for unsupported sites
            logger.info(f"Site not in supported list, trying schema.org fallback for {url}")
            try:
                scraper = scrape_html(None, url, online=True, supported_only=False)
                used_fallback = True
            except Exception as fallback_error:
                logger.error(f"Fallback scraping failed for {url}: {fallback_error}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This website is not supported and does not have valid schema.org recipe markup",
                )

        try:
            # Parse ingredients
            ingredients = []
            for idx, ingredient_line in enumerate(scraper.ingredients()):
                quantity, unit, ingredient_name = parse_ingredient_line(ingredient_line)
                ingredients.append(
                    RecipeImportPreviewIngredient(
                        ingredient_name=ingredient_name,
                        quantity=quantity,
                        unit=unit,
                    )
                )

            # Parse instructions
            instructions = []
            instruction_list = scraper.instructions_list()
            if not instruction_list:
                # Fallback to single instruction string if list not available
                instruction_text = scraper.instructions()
                if instruction_text:
                    # Split by newlines or numbers
                    import re

                    steps = re.split(r"\n+|\d+\.\s*", instruction_text)
                    instruction_list = [s.strip() for s in steps if s.strip()]

            for idx, step in enumerate(instruction_list, 1):
                instructions.append(
                    RecipeImportPreviewInstruction(
                        step_number=idx,
                        description=step.strip(),
                    )
                )

            # Extract times (recipe-scrapers returns minutes as int or None)
            prep_time = None
            try:
                prep_time = scraper.prep_time()
            except (AttributeError, NotImplementedError):
                logger.debug(f"Prep time method not available for {url}")
            except Exception as e:
                logger.warning(f"Failed to extract prep time from {url}: {e}")

            cook_time = None
            try:
                cook_time = scraper.cook_time()
            except (AttributeError, NotImplementedError):
                logger.debug(f"Cook time method not available for {url}")
            except Exception as e:
                logger.warning(f"Failed to extract cook time from {url}: {e}")

            # Get description if available
            description = None
            try:
                desc = scraper.description()
                # Only use description if it's not empty
                if desc and desc.strip():
                    description = desc.strip()
            except (AttributeError, NotImplementedError):
                # Method not available for this scraper
                logger.debug(f"Description method not available for {url}")
            except Exception as e:
                # Other error accessing description
                logger.warning(f"Failed to extract description from {url}: {e}")

            return RecipeImportPreviewResponse(
                name=scraper.title(),
                recipe_type="dinner",  # Default
                description=description,
                prep_time_minutes=prep_time,
                cook_time_minutes=cook_time,
                source_url=url,
                ingredients=ingredients,
                instructions=instructions,
            )

        except Exception as e:
            logger.error(f"Failed to parse recipe from {url}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse recipe: {str(e)}",
            )

    @staticmethod
    async def reimport_recipe(
        db: AsyncSession,
        recipe_id: UUID,
    ) -> Recipe:
        """Re-import recipe from its source URL, updating existing data.

        Args:
            db: Database session
            recipe_id: ID of recipe to re-import

        Returns:
            Updated Recipe object

        Raises:
            HTTPException: If recipe not found, no source_url, or scraping fails
        """
        # Get existing recipe
        recipe = await RecipeService.get_recipe_by_id(db=db, recipe_id=recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )

        if not recipe.source_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recipe has no source URL to re-import from",
            )

        # Scrape fresh data
        preview = await RecipeService.import_recipe_preview(recipe.source_url)

        # Update recipe fields (preserve user edits to postmortem_notes and owner_id)
        recipe.name = preview.name
        recipe.description = preview.description
        recipe.prep_time_minutes = preview.prep_time_minutes
        recipe.cook_time_minutes = preview.cook_time_minutes
        # Note: Don't update recipe_type - user may have customized it

        # Delete existing ingredients and instructions
        for ingredient in recipe.ingredients:
            await db.delete(ingredient)
        for instruction in recipe.instructions:
            await db.delete(instruction)

        await db.flush()

        # Add new ingredients
        for idx, ing_data in enumerate(preview.ingredients):
            ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_name=ing_data.ingredient_name,
                quantity=ing_data.quantity,
                unit=ing_data.unit,
                order=idx,
            )
            db.add(ingredient)

        # Add new instructions
        for inst_data in preview.instructions:
            instruction = RecipeInstruction(
                recipe_id=recipe.id,
                step_number=inst_data.step_number,
                description=inst_data.description,
            )
            db.add(instruction)

        await db.commit()
        await db.refresh(recipe)

        # Reload with relationships
        recipe = await RecipeService.get_recipe_by_id(db=db, recipe_id=recipe.id)
        return recipe

    # ========================================================================
    # Recipe Index
    # ========================================================================

    @staticmethod
    async def get_recipe_index(
        db: AsyncSession,
        include_retired: bool = False,
    ) -> dict[str, list[dict]]:
        """
        Build unified recipe index mixing recipes and ingredients alphabetically.

        Returns a dictionary organized by first letter (A-Z) with entries for:
        - Ingredients (with their associated recipes)
        - Standalone recipes (those not appearing under any ingredient)

        Args:
            db: Database session
            include_retired: Whether to include retired recipes

        Returns:
            Dictionary with letter keys (A-Z) and lists of index entries
        """
        from collections import defaultdict

        # Query all recipes with indexed ingredients
        query = select(Recipe).options(
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.common_ingredient)
        )

        if not include_retired:
            query = query.where(Recipe.retired_at.is_(None))

        result = await db.execute(query)
        recipes = result.scalars().all()

        # Build two structures:
        # 1. Recipes grouped by ingredient
        ingredient_to_recipes = defaultdict(list)
        # 2. Track which recipes have indexed ingredients
        recipes_with_indexed_ingredients = set()

        for recipe in recipes:
            for ingredient in recipe.ingredients:
                if ingredient.is_indexed:
                    recipes_with_indexed_ingredients.add(recipe.id)

                    # Use common_ingredient.name if available, otherwise raw ingredient_name
                    ingredient_key = (
                        ingredient.common_ingredient.name
                        if ingredient.common_ingredient
                        else ingredient.ingredient_name
                    )

                    ingredient_to_recipes[ingredient_key].append(
                        {
                            "id": str(recipe.id),
                            "name": recipe.name,
                        }
                    )

        # Build the unified index
        all_entries = []

        # Add ingredient entries
        for ingredient_name, recipe_refs in ingredient_to_recipes.items():
            all_entries.append(
                {
                    "type": "ingredient",
                    "name": ingredient_name,
                    "recipes": recipe_refs,
                }
            )

        # Add standalone recipe entries (those without indexed ingredients)
        for recipe in recipes:
            if recipe.id not in recipes_with_indexed_ingredients:
                all_entries.append(
                    {
                        "type": "recipe",
                        "name": recipe.name,
                        "id": str(recipe.id),
                        "indexed_ingredients": [],
                    }
                )

        # Sort all entries alphabetically by name
        all_entries.sort(key=lambda x: x["name"].lower())

        # Group by first letter
        index_by_letter = defaultdict(list)
        for entry in all_entries:
            first_letter = entry["name"][0].upper()
            # Only include A-Z, put numbers/symbols under '#'
            if not first_letter.isalpha():
                first_letter = "#"
            index_by_letter[first_letter].append(entry)

        return dict(index_by_letter)
