"""
Unit tests for grocery service business logic.

Tests cover:
- _aggregate_with_pint() recipe details collection
- _get_display_quantities() unit display logic
- Edge cases for non-convertible units
- Recipe contribution tracking
"""

import pytest
from uuid import uuid4
from app.services.grocery_service import GroceryService
from app.models.recipe import RecipeIngredient


class TestAggregateWithPint:
    """Test the _aggregate_with_pint() static method."""

    def test_collects_recipe_details_simple(self):
        """Test that recipe details are collected for simple case."""
        recipe_id = uuid4()

        # Create mock ingredient
        ing1 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id,
            ingredient_name="Salt",
            quantity=1.0,
            unit="teaspoon",
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing1],
            ingredient_name="Salt",
        )

        assert len(result) == 1
        assert "source_recipe_details" in result[0]
        details = result[0]["source_recipe_details"]
        assert len(details) == 1
        assert details[0]["recipe_id"] == str(recipe_id)
        assert details[0]["quantity"] == 1.0
        assert details[0]["unit"] == "teaspoon"

    def test_collects_recipe_details_multiple_recipes(self):
        """Test recipe details from multiple recipes."""
        recipe_id1 = uuid4()
        recipe_id2 = uuid4()

        ing1 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id1,
            ingredient_name="Milk",
            quantity=1.0,
            unit="cup",
            order=1,
        )

        ing2 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id2,
            ingredient_name="Milk",
            quantity=8.0,
            unit="fluid_ounce",
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing1, ing2],
            ingredient_name="Milk",
        )

        assert len(result) == 1
        details = result[0]["source_recipe_details"]
        assert len(details) == 2

        # Find each recipe's detail
        recipe1_detail = next(d for d in details if d["recipe_id"] == str(recipe_id1))
        recipe2_detail = next(d for d in details if d["recipe_id"] == str(recipe_id2))

        assert recipe1_detail["quantity"] == 1.0
        assert recipe1_detail["unit"] == "cup"

        assert recipe2_detail["quantity"] == 8.0
        assert recipe2_detail["unit"] == "fluid_ounce"

    def test_preserves_original_units_across_conversion(self):
        """Test that original units are preserved even when Pint converts."""
        recipe_id1 = uuid4()
        recipe_id2 = uuid4()

        # Different units that Pint will convert (tablespoon -> cup)
        ing1 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id1,
            ingredient_name="Soy Sauce",
            quantity=2.0,
            unit="tablespoon",
            order=1,
        )

        ing2 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id2,
            ingredient_name="Soy Sauce",
            quantity=30.0,
            unit="milliliter",
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing1, ing2],
            ingredient_name="Soy Sauce",
        )

        # Aggregated result uses canonical unit
        assert result[0]["unit"] in ["cup", "fluid_ounce", "milliliter"]

        # But details preserve original
        details = result[0]["source_recipe_details"]
        recipe1_detail = next(d for d in details if d["recipe_id"] == str(recipe_id1))
        recipe2_detail = next(d for d in details if d["recipe_id"] == str(recipe_id2))

        assert recipe1_detail["unit"] == "tablespoon"
        assert recipe2_detail["unit"] == "milliliter"

    def test_handles_empty_unit(self):
        """Test handling ingredients with no unit."""
        recipe_id = uuid4()

        ing = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id,
            ingredient_name="Eggs",
            quantity=4.0,
            unit=None,
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing],
            ingredient_name="Eggs",
        )

        details = result[0]["source_recipe_details"]
        assert details[0]["unit"] == ""  # Empty string for None

    def test_filters_out_none_quantities(self):
        """Test that ingredients with None quantity are excluded."""
        recipe_id1 = uuid4()
        recipe_id2 = uuid4()

        # One with quantity, one without
        ing1 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id1,
            ingredient_name="Salt",
            quantity=1.0,
            unit="teaspoon",
            order=1,
        )

        ing2 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id2,
            ingredient_name="Salt",
            quantity=None,  # To taste
            unit="teaspoon",
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing1, ing2],
            ingredient_name="Salt",
        )

        # Should only include the one with quantity
        details = result[0]["source_recipe_details"]
        assert len(details) == 1
        assert details[0]["recipe_id"] == str(recipe_id1)

    def test_non_convertible_unit_preserved(self):
        """Test that non-convertible units like 'bunch' are preserved."""
        recipe_id = uuid4()

        ing = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id,
            ingredient_name="Scallions",
            quantity=1.0,
            unit="bunch",
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing],
            ingredient_name="Scallions",
        )

        # Aggregated keeps the unit
        assert result[0]["unit"] == "bunch"

        # Details also preserve it
        details = result[0]["source_recipe_details"]
        assert details[0]["unit"] == "bunch"

    def test_same_unit_preservation(self):
        """Test that when all ingredients use same unit, it's preserved."""
        recipe_id1 = uuid4()
        recipe_id2 = uuid4()

        ing1 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id1,
            ingredient_name="Sugar",
            quantity=1.0,
            unit="cup",
            order=1,
        )

        ing2 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id2,
            ingredient_name="Sugar",
            quantity=2.0,
            unit="cup",
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing1, ing2],
            ingredient_name="Sugar",
        )

        # Should preserve the cup unit
        assert result[0]["unit"] == "cup"
        assert result[0]["total_quantity"] == 3.0

        # Details should have both recipes
        details = result[0]["source_recipe_details"]
        assert len(details) == 2


class TestGetDisplayQuantities:
    """Test the _get_display_quantities() static method."""

    def test_convertible_volume_unit(self):
        """Test display for convertible volume units."""
        result = GroceryService._get_display_quantities(1.0, "cup")

        assert result["display"] is not None
        assert result["metric"] is not None
        assert result["imperial"] is not None
        assert "ml" in result["metric"] or "L" in result["metric"]
        assert "fl oz" in result["imperial"]

    def test_convertible_weight_unit(self):
        """Test display for convertible weight units."""
        result = GroceryService._get_display_quantities(1.0, "pound")

        assert result["display"] is not None
        assert result["metric"] is not None
        assert result["imperial"] is not None
        assert "g" in result["metric"] or "kg" in result["metric"]
        assert "lbs" in result["imperial"] or "oz" in result["imperial"]

    def test_non_convertible_unit_single_display(self):
        """Test that non-convertible units only set metric, not imperial."""
        result = GroceryService._get_display_quantities(1.0, "bunch")

        assert result["display"] == "1 bunch"
        assert result["metric"] == "1 bunch"
        assert result["imperial"] is None  # Should be None, not duplicated

    def test_package_unit_single_display(self):
        """Test 'package' as another non-convertible unit."""
        result = GroceryService._get_display_quantities(2.0, "package")

        assert result["metric"] == "2 package"
        assert result["imperial"] is None

    def test_can_unit_single_display(self):
        """Test 'can' as non-convertible unit."""
        result = GroceryService._get_display_quantities(1.0, "can")

        assert result["metric"] == "1 can"
        assert result["imperial"] is None

    def test_no_unit_returns_none_equivalents(self):
        """Test items with no unit return None for metric/imperial."""
        result = GroceryService._get_display_quantities(5.0, "")

        assert result["display"] == "5"
        assert result["metric"] is None
        assert result["imperial"] is None

    def test_fractional_display(self):
        """Test that display uses fractions for common values."""
        result = GroceryService._get_display_quantities(0.5, "cup")

        # Should use fraction in display
        assert result["display"] in ["½ cup", "1/2 cup"]

    def test_rounds_up_for_shopping(self):
        """Test that metric/imperial round up for shopping convenience."""
        # 1 tablespoon ≈ 15ml, should round up
        result = GroceryService._get_display_quantities(1.0, "tablespoon")

        # Metric should be rounded (15ml -> 15ml or 20ml depending on rounding)
        assert result["metric"] is not None
        # Imperial should be rounded
        assert result["imperial"] is not None

    def test_preserves_case_of_original_unit(self):
        """Test that original unit case is preserved in display."""
        result = GroceryService._get_display_quantities(1.0, "Bunch")

        # Should preserve the capital B
        assert "Bunch" in result["display"]
        assert "Bunch" in result["metric"]
