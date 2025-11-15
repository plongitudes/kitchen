"""
Service for grocery list generation and ingredient aggregation.

Uses Pint library for intelligent unit-aware conversions.
"""

from typing import List, Dict, Optional
from uuid import UUID
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
import json
from pint import UnitRegistry, DimensionalityError

from app.models.meal_plan import MealPlanInstance, GroceryList, GroceryListItem
from app.models.schedule import WeekTemplate, WeekDayAssignment
from app.models.recipe import Recipe, RecipeIngredient


# Initialize Pint unit registry
ureg = UnitRegistry()


class GroceryService:
    """Service layer for grocery list business logic."""

    # Canonical units for conversion
    CANONICAL_VOLUME = "cup"
    CANONICAL_WEIGHT = "gram"

    # Units that should not be converted (counts, special)
    NON_CONVERTIBLE_UNITS = {
        "bunch",
        "clove",
        "cloves",
        "to taste",
        "pinch",
        "dash",
        "whole",
        "piece",
        "pieces",
        "item",
        "items",
        "each",
    }

    @staticmethod
    async def generate_grocery_list(
        db: AsyncSession,
        instance_id: UUID,
        shopping_date: date,
    ) -> GroceryList:
        """
        Generate a grocery list for a specific shopping day.

        The list covers meals from the day AFTER shopping through the next shopping day.
        """
        # Get the meal plan instance
        instance = await GroceryService._get_instance_with_week(db, instance_id)

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal plan instance not found",
            )

        # Find all recipes needed for this shopping period
        recipes_needed = await GroceryService._find_recipes_for_shopping_period(
            db=db,
            instance=instance,
            shopping_date=shopping_date,
        )

        # Aggregate ingredients with Pint
        aggregated_items = await GroceryService._aggregate_ingredients(
            db=db,
            recipe_ids=recipes_needed,
        )

        # Check if grocery list already exists for this date
        existing_list = await GroceryService._get_existing_list(
            db=db,
            instance_id=instance_id,
            shopping_date=shopping_date,
        )

        if existing_list:
            # Delete old items
            for item in existing_list.items:
                await db.delete(item)
            grocery_list = existing_list
        else:
            # Create new grocery list
            grocery_list = GroceryList(
                meal_plan_instance_id=instance_id,
                shopping_date=shopping_date,
            )
            db.add(grocery_list)

        await db.flush()  # Get grocery_list.id

        # Create grocery list items
        for item_data in aggregated_items:
            item = GroceryListItem(
                grocery_list_id=grocery_list.id,
                ingredient_name=item_data["ingredient_name"],
                total_quantity=item_data["total_quantity"],
                unit=item_data["unit"],
                source_recipe_ids=json.dumps(item_data["source_recipe_ids"]),
            )
            db.add(item)

        await db.commit()
        await db.refresh(grocery_list)

        # Load items for response
        grocery_list = await GroceryService.get_grocery_list_by_id(
            db=db,
            grocery_list_id=grocery_list.id,
        )

        return grocery_list

    @staticmethod
    async def _get_instance_with_week(
        db: AsyncSession,
        instance_id: UUID,
    ) -> Optional[MealPlanInstance]:
        """Get instance with week and assignments loaded."""
        query = (
            select(MealPlanInstance)
            .where(MealPlanInstance.id == instance_id)
            .options(
                selectinload(MealPlanInstance.week_template).selectinload(
                    WeekTemplate.day_assignments
                )
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def _find_recipes_for_shopping_period(
        db: AsyncSession,
        instance: MealPlanInstance,
        shopping_date: date,
    ) -> List[UUID]:
        """
        Find all recipes needed between shopping_date+1 and next shopping day.

        Shopping day itself is excluded from the list.
        """
        template = instance.week_template
        start_date = instance.instance_start_date

        # Get all assignments, sorted by day
        assignments = sorted(
            template.day_assignments,
            key=lambda a: (a.day_of_week, a.order),
        )

        # Find all "shop" actions
        shopping_days = [
            start_date + timedelta(days=a.day_of_week)
            for a in assignments
            if a.action.lower() == "shop"
        ]

        if not shopping_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No shopping days found in this week template",
            )

        # Find the next shopping day after shopping_date
        future_shopping_days = [d for d in shopping_days if d > shopping_date]

        if future_shopping_days:
            next_shopping_date = min(future_shopping_days)
        else:
            # Wrap to next week - assume weekly shopping
            # TODO: Handle multi-week instances properly
            next_shopping_date = shopping_date + timedelta(days=7)

        # Get all cook assignments between shopping_date+1 and next_shopping_date (inclusive)
        start_coverage = shopping_date + timedelta(days=1)
        end_coverage = next_shopping_date

        recipe_ids = []
        for assignment in assignments:
            assignment_date = start_date + timedelta(days=assignment.day_of_week)

            if (
                assignment.action.lower() == "cook"
                and assignment.recipe_id
                and start_coverage <= assignment_date <= end_coverage
            ):
                recipe_ids.append(assignment.recipe_id)

        return recipe_ids

    @staticmethod
    async def _aggregate_ingredients(
        db: AsyncSession,
        recipe_ids: List[UUID],
    ) -> List[Dict]:
        """
        Aggregate ingredients across recipes with Pint unit conversion.

        Returns list of dicts with: ingredient_name, total_quantity, unit, source_recipe_ids
        """
        if not recipe_ids:
            return []

        # Fetch all ingredients for these recipes
        query = select(RecipeIngredient).where(
            RecipeIngredient.recipe_id.in_(recipe_ids)
        )
        result = await db.execute(query)
        all_ingredients = result.scalars().all()

        # Group by common_ingredient_id (if available) or ingredient name (case-insensitive)
        ingredient_groups = {}
        for ing in all_ingredients:
            # If ingredient has a common_ingredient_id, group by that
            # Otherwise, fall back to grouping by lowercase ingredient name
            if ing.common_ingredient_id:
                group_key = f"common:{ing.common_ingredient_id}"
            else:
                group_key = f"unmapped:{ing.ingredient_name.lower().strip()}"

            if group_key not in ingredient_groups:
                ingredient_groups[group_key] = []
            ingredient_groups[group_key].append(ing)

        # Aggregate each group with Pint
        aggregated = []
        for name_key, ingredients in ingredient_groups.items():
            # Use the original case from the first ingredient
            display_name = ingredients[0].ingredient_name

            # Track source recipes
            source_recipe_ids = list(set(str(ing.recipe_id) for ing in ingredients))

            # Attempt to aggregate with Pint
            aggregated_result = GroceryService._aggregate_with_pint(
                ingredients=ingredients,
                ingredient_name=display_name,
            )

            for item in aggregated_result:
                item["source_recipe_ids"] = source_recipe_ids
                aggregated.append(item)

        return aggregated

    @staticmethod
    def _aggregate_with_pint(
        ingredients: List[RecipeIngredient],
        ingredient_name: str,
    ) -> List[Dict]:
        """
        Aggregate ingredients using Pint for unit conversion.

        Returns list of dicts (may be multiple if different dimensionalities).
        """
        # Separate by dimensionality
        volume_quantities = []
        weight_quantities = []
        count_quantities = []

        for ing in ingredients:
            unit = ing.unit.lower().strip()
            quantity = ing.quantity

            # Handle non-convertible units
            if unit in GroceryService.NON_CONVERTIBLE_UNITS:
                count_quantities.append(
                    {
                        "quantity": quantity,
                        "unit": ing.unit,  # Preserve original case
                    }
                )
                continue

            # Try to parse as Pint quantity
            try:
                pint_qty = ureg.Quantity(quantity, unit)

                # Check dimensionality
                if pint_qty.dimensionality == ureg.liter.dimensionality:
                    volume_quantities.append(pint_qty)
                elif pint_qty.dimensionality == ureg.gram.dimensionality:
                    weight_quantities.append(pint_qty)
                else:
                    # Unknown dimensionality - treat as count
                    count_quantities.append(
                        {
                            "quantity": quantity,
                            "unit": ing.unit,
                        }
                    )
            except (DimensionalityError, Exception):
                # Can't parse or convert - treat as count
                count_quantities.append(
                    {
                        "quantity": quantity,
                        "unit": ing.unit,
                    }
                )

        # Aggregate each dimensionality
        results = []

        # Volume
        if volume_quantities:
            total_volume = sum(volume_quantities)
            canonical_volume = total_volume.to(GroceryService.CANONICAL_VOLUME)
            results.append(
                {
                    "ingredient_name": ingredient_name,
                    "total_quantity": round(canonical_volume.magnitude, 3),
                    "unit": GroceryService.CANONICAL_VOLUME,
                }
            )

        # Weight
        if weight_quantities:
            total_weight = sum(weight_quantities)
            canonical_weight = total_weight.to(GroceryService.CANONICAL_WEIGHT)
            results.append(
                {
                    "ingredient_name": ingredient_name,
                    "total_quantity": round(canonical_weight.magnitude, 3),
                    "unit": GroceryService.CANONICAL_WEIGHT,
                }
            )

        # Counts - group by unit
        if count_quantities:
            count_by_unit = {}
            for item in count_quantities:
                unit = item["unit"]
                if unit not in count_by_unit:
                    count_by_unit[unit] = 0
                count_by_unit[unit] += item["quantity"]

            for unit, total in count_by_unit.items():
                results.append(
                    {
                        "ingredient_name": ingredient_name,
                        "total_quantity": round(total, 3),
                        "unit": unit,
                    }
                )

        return (
            results
            if results
            else [
                {
                    "ingredient_name": ingredient_name,
                    "total_quantity": 0,
                    "unit": "item",
                }
            ]
        )

    @staticmethod
    async def _get_existing_list(
        db: AsyncSession,
        instance_id: UUID,
        shopping_date: date,
    ) -> Optional[GroceryList]:
        """Check if a grocery list already exists for this date."""
        query = (
            select(GroceryList)
            .where(
                and_(
                    GroceryList.meal_plan_instance_id == instance_id,
                    GroceryList.shopping_date == shopping_date,
                )
            )
            .options(selectinload(GroceryList.items))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_grocery_lists(
        db: AsyncSession,
        instance_id: Optional[UUID] = None,
    ) -> List[GroceryList]:
        """Get all grocery lists, optionally filtered by instance."""
        query = select(GroceryList).options(selectinload(GroceryList.items))

        if instance_id:
            query = query.where(GroceryList.meal_plan_instance_id == instance_id)

        query = query.order_by(GroceryList.shopping_date.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_grocery_list_by_id(
        db: AsyncSession,
        grocery_list_id: UUID,
    ) -> Optional[GroceryList]:
        """Get a specific grocery list by ID with items."""
        query = (
            select(GroceryList)
            .where(GroceryList.id == grocery_list_id)
            .options(selectinload(GroceryList.items))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
