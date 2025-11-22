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


def _get_unit_value(unit) -> str:
    """Extract string value from unit, handling both enum and string types."""
    if unit is None:
        return ""
    if hasattr(unit, 'value'):
        return unit.value
    return str(unit)


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
                source_recipe_details=json.dumps(item_data.get("source_recipe_details", [])),
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
        # Collect recipe contribution details (preserve original units from each recipe)
        source_recipe_details = [
            {
                "recipe_id": str(ing.recipe_id),
                "quantity": ing.quantity,
                "unit": _get_unit_value(ing.unit),
            }
            for ing in ingredients
            if ing.quantity is not None
        ]

        # Check if all ingredients use the same unit (case-insensitive)
        # If so, preserve that unit instead of converting to canonical
        units_with_quantities = [
            (_get_unit_value(ing.unit), ing.quantity)
            for ing in ingredients
            if ing.unit and ing.quantity is not None
        ]

        if units_with_quantities:
            unique_units = set(u.lower().strip() for u, _ in units_with_quantities)
            if len(unique_units) == 1:
                # All same unit - preserve it, just sum quantities
                preserved_unit = units_with_quantities[0][0]  # Already converted to string
                total_quantity = sum(q for _, q in units_with_quantities)

                return [
                    {
                        "ingredient_name": ingredient_name,
                        "total_quantity": total_quantity,
                        "unit": preserved_unit,
                        "source_recipe_details": source_recipe_details,
                    }
                ]

        # Mixed units or no units - use Pint conversion to canonical units
        # Separate by dimensionality
        volume_quantities = []
        weight_quantities = []
        count_quantities = []

        for ing in ingredients:
            # Skip ingredients with no quantity
            if ing.quantity is None:
                continue

            # Handle missing unit (treat as count)
            if not ing.unit:
                count_quantities.append(
                    {
                        "quantity": ing.quantity,
                        "unit": "",  # No unit
                    }
                )
                continue

            unit_value = _get_unit_value(ing.unit)
            unit = unit_value.lower().strip()
            quantity = ing.quantity

            # Handle non-convertible units
            if unit in GroceryService.NON_CONVERTIBLE_UNITS:
                count_quantities.append(
                    {
                        "quantity": quantity,
                        "unit": unit_value,  # Use converted value
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
                            "unit": unit_value,
                        }
                    )
            except (DimensionalityError, Exception):
                # Can't parse or convert - treat as count
                count_quantities.append(
                    {
                        "quantity": quantity,
                        "unit": unit_value,
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
                    "source_recipe_details": source_recipe_details,
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
                    "source_recipe_details": source_recipe_details,
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
                        "source_recipe_details": source_recipe_details,
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
                    "source_recipe_details": source_recipe_details,
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

    @staticmethod
    async def enrich_items_with_recipe_names(
        db: AsyncSession,
        grocery_list: GroceryList,
    ) -> None:
        """Enrich grocery list items with recipe names."""
        import json
        from uuid import UUID

        # Collect all unique recipe IDs
        recipe_ids = set()
        for item in grocery_list.items:
            if item.source_recipe_ids:
                ids = json.loads(item.source_recipe_ids) if isinstance(item.source_recipe_ids, str) else item.source_recipe_ids
                recipe_ids.update(UUID(rid) for rid in ids)

        if not recipe_ids:
            return

        # Fetch all recipes in one query
        recipe_query = select(Recipe).where(Recipe.id.in_(recipe_ids))
        result = await db.execute(recipe_query)
        recipes = result.scalars().all()
        recipe_map = {str(r.id): r.name for r in recipes}

        # Add recipe names and display quantities to each item
        for item in grocery_list.items:
            if item.source_recipe_ids:
                ids = json.loads(item.source_recipe_ids) if isinstance(item.source_recipe_ids, str) else item.source_recipe_ids
                item.source_recipe_names = [recipe_map.get(rid, "Unknown Recipe") for rid in ids]

            # Enrich source_recipe_details with recipe names
            if item.source_recipe_details:
                details = json.loads(item.source_recipe_details) if isinstance(item.source_recipe_details, str) else item.source_recipe_details
                for detail in details:
                    detail["recipe_name"] = recipe_map.get(detail["recipe_id"], "Unknown Recipe")
                # Re-serialize back to JSON (will be parsed by Pydantic validator in schema)
                item.source_recipe_details = json.dumps(details)

            # Add display-friendly quantities
            display_data = GroceryService._get_display_quantities(
                item.total_quantity, item.unit
            )
            item.display_quantity = display_data["display"]
            item.metric_equivalent = display_data["metric"]
            item.imperial_equivalent = display_data["imperial"]

    @staticmethod
    def _decimal_to_fraction(decimal: float, tolerance: float = 0.01) -> tuple:
        """Convert decimal to nearest common fraction.

        Returns (whole, numerator, denominator) tuple.
        """
        from fractions import Fraction

        # Common cooking fractions
        common_fractions = [
            (1, 8), (1, 6), (1, 4), (1, 3), (1, 2),
            (2, 3), (3, 4), (5, 6), (7, 8)
        ]

        whole = int(decimal)
        remainder = decimal - whole

        if remainder < tolerance:
            return (whole, 0, 1)
        if remainder > (1 - tolerance):
            return (whole + 1, 0, 1)

        # Find closest common fraction
        best_match = None
        best_diff = float('inf')

        for num, denom in common_fractions:
            frac_val = num / denom
            diff = abs(remainder - frac_val)
            if diff < best_diff:
                best_diff = diff
                best_match = (num, denom)

        if best_diff < tolerance:
            return (whole, best_match[0], best_match[1])

        # Fallback to Fraction library for uncommon fractions
        frac = Fraction(remainder).limit_denominator(8)
        return (whole, frac.numerator, frac.denominator)

    @staticmethod
    def _format_quantity(whole: int, num: int, denom: int) -> str:
        """Format quantity with unicode fractions."""
        # Unicode fraction characters
        fractions_map = {
            (1, 8): "⅛", (1, 6): "⅙", (1, 4): "¼", (1, 3): "⅓", (1, 2): "½",
            (2, 3): "⅔", (3, 4): "¾", (5, 6): "⅚", (7, 8): "⅞",
            (1, 5): "⅕", (2, 5): "⅖", (3, 5): "⅗", (4, 5): "⅘"
        }

        if num == 0:
            return str(whole) if whole > 0 else "0"

        frac_str = fractions_map.get((num, denom), f"{num}/{denom}")

        if whole > 0:
            return f"{whole} {frac_str}"
        return frac_str

    @staticmethod
    def _get_display_quantities(quantity: float, unit: str) -> dict:
        """Generate display-friendly quantity representations.

        Returns dict with 'display', 'metric', and 'imperial' keys.
        """
        if not unit:
            # No unit items - no buffer, no conversions, just show count
            return {
                "display": str(int(quantity)) if quantity == int(quantity) else f"{quantity:.1f}",
                "metric": None,
                "imperial": None
            }

        unit_lower = unit.lower().strip()

        # Recipe amount (exact, with fractions for display)
        recipe_whole, recipe_num, recipe_denom = GroceryService._decimal_to_fraction(quantity)
        recipe_str = GroceryService._format_quantity(recipe_whole, recipe_num, recipe_denom)

        # Generate metric and imperial equivalents for shopping amount
        # Convert to grocery units FIRST, then round up
        import math
        metric_str = None
        imperial_str = None

        try:
            # Try Pint conversion for common units (use exact quantity, not rounded)
            pint_qty = ureg.Quantity(quantity, unit_lower)

            # Determine if it's metric or imperial
            if pint_qty.dimensionality == ureg.liter.dimensionality:
                # Volume - convert to grocery units (fl oz / ml)
                metric_qty = pint_qty.to("milliliter")
                imperial_qty = pint_qty.to("fluid_ounce")

                # Metric: use decimals, round to reasonable precision
                ml_val = metric_qty.magnitude
                if ml_val < 1000:
                    # Round to nearest 5ml for small quantities
                    metric_str = f"{int(math.ceil(ml_val / 5) * 5)}ml"
                else:
                    # Use liters for large quantities
                    l_val = metric_qty.to('liter').magnitude
                    metric_str = f"{math.ceil(l_val * 10) / 10:.1f}L"

                # Imperial: fluid ounces (round up to whole numbers)
                fl_oz = int(math.ceil(imperial_qty.magnitude))
                imperial_str = f"{fl_oz} fl oz"

            elif pint_qty.dimensionality == ureg.gram.dimensionality:
                # Weight - convert to grocery units (oz/lbs / g/kg)
                metric_qty = pint_qty.to("gram")
                imperial_qty = pint_qty.to("ounce")

                # Metric: use decimals, round to reasonable precision
                g_val = metric_qty.magnitude
                if g_val < 1000:
                    # Round to nearest 5g for quantities under 1kg
                    metric_str = f"{int(math.ceil(g_val / 5) * 5)}g"
                else:
                    # Use kg for large quantities
                    kg_val = metric_qty.to('kilogram').magnitude
                    metric_str = f"{math.ceil(kg_val * 10) / 10:.1f}kg"

                # Imperial: oz or lbs depending on size
                oz_val = imperial_qty.magnitude
                if oz_val >= 16:
                    # Convert to pounds for large quantities
                    lbs = math.ceil(oz_val / 16)
                    imperial_str = f"{lbs} lbs"
                else:
                    # Use ounces for smaller quantities (round up)
                    imperial_str = f"{int(math.ceil(oz_val))} oz"
        except Exception:
            # If conversion fails, use original unit (only set metric, leave imperial None)
            # This prevents duplicate display like "1 bunch / 1 bunch"
            rounded_qty = int(math.ceil(quantity))
            metric_str = f"{rounded_qty} {unit}"
            imperial_str = None

        return {
            "display": f"{recipe_str} {unit}",  # Recipe amount (exact)
            "metric": metric_str,  # Shopping amount in metric
            "imperial": imperial_str  # Shopping amount in imperial
        }
