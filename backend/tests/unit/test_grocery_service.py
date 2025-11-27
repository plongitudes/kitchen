"""
Unit tests for grocery service business logic.

Tests cover:
- _aggregate_with_pint() recipe details collection
- _get_display_quantities() unit display logic
- _decimal_to_fraction() conversion logic
- _format_quantity() formatting
- _get_unit_value() helper
- Edge cases for non-convertible units
- Recipe contribution tracking
"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from enum import Enum
from app.services.grocery_service import GroceryService, _get_unit_value
from app.models.recipe import RecipeIngredient, IngredientUnit


class TestGetUnitValue:
    """Test the _get_unit_value() helper function."""

    def test_returns_empty_for_none(self):
        """Returns empty string for None input."""
        assert _get_unit_value(None) == ""

    def test_returns_value_for_enum(self):
        """Returns .value for enum types."""
        assert _get_unit_value(IngredientUnit.CUP) == "cup"
        assert _get_unit_value(IngredientUnit.TABLESPOON) == "tablespoon"
        assert _get_unit_value(IngredientUnit.TEASPOON) == "teaspoon"

    def test_returns_string_for_string(self):
        """Returns string as-is for string input."""
        assert _get_unit_value("cup") == "cup"
        assert _get_unit_value("tablespoon") == "tablespoon"

    def test_returns_str_for_other_types(self):
        """Calls str() on other types."""
        assert _get_unit_value(123) == "123"


class TestDecimalToFraction:
    """Test the _decimal_to_fraction() static method."""

    def test_whole_number(self):
        """Converts whole numbers correctly."""
        whole, num, denom = GroceryService._decimal_to_fraction(3.0)
        assert whole == 3
        assert num == 0

    def test_half(self):
        """Converts 0.5 to 1/2."""
        whole, num, denom = GroceryService._decimal_to_fraction(0.5)
        assert whole == 0
        assert num == 1
        assert denom == 2

    def test_quarter(self):
        """Converts 0.25 to 1/4."""
        whole, num, denom = GroceryService._decimal_to_fraction(0.25)
        assert whole == 0
        assert num == 1
        assert denom == 4

    def test_three_quarters(self):
        """Converts 0.75 to 3/4."""
        whole, num, denom = GroceryService._decimal_to_fraction(0.75)
        assert whole == 0
        assert num == 3
        assert denom == 4

    def test_one_third(self):
        """Converts ~0.333 to 1/3."""
        whole, num, denom = GroceryService._decimal_to_fraction(0.333)
        assert whole == 0
        assert num == 1
        assert denom == 3

    def test_two_thirds(self):
        """Converts ~0.667 to 2/3."""
        whole, num, denom = GroceryService._decimal_to_fraction(0.667)
        assert whole == 0
        assert num == 2
        assert denom == 3

    def test_one_eighth(self):
        """Converts 0.125 to 1/8."""
        whole, num, denom = GroceryService._decimal_to_fraction(0.125)
        assert whole == 0
        assert num == 1
        assert denom == 8

    def test_mixed_number_one_and_half(self):
        """Converts 1.5 to 1 1/2."""
        whole, num, denom = GroceryService._decimal_to_fraction(1.5)
        assert whole == 1
        assert num == 1
        assert denom == 2

    def test_mixed_number_two_and_quarter(self):
        """Converts 2.25 to 2 1/4."""
        whole, num, denom = GroceryService._decimal_to_fraction(2.25)
        assert whole == 2
        assert num == 1
        assert denom == 4

    def test_very_small_remainder_rounds_down(self):
        """Very small remainders round to whole number."""
        whole, num, denom = GroceryService._decimal_to_fraction(2.001)
        assert whole == 2
        assert num == 0

    def test_very_large_remainder_rounds_up(self):
        """Remainders very close to 1 round up."""
        whole, num, denom = GroceryService._decimal_to_fraction(2.999)
        assert whole == 3
        assert num == 0

    def test_zero(self):
        """Handles zero correctly."""
        whole, num, denom = GroceryService._decimal_to_fraction(0.0)
        assert whole == 0
        assert num == 0


class TestFormatQuantity:
    """Test the _format_quantity() static method."""

    def test_whole_number_only(self):
        """Formats whole number without fraction."""
        assert GroceryService._format_quantity(3, 0, 1) == "3"

    def test_zero(self):
        """Formats zero correctly."""
        assert GroceryService._format_quantity(0, 0, 1) == "0"

    def test_fraction_only_half(self):
        """Formats 1/2 with unicode."""
        result = GroceryService._format_quantity(0, 1, 2)
        assert result == "½"

    def test_fraction_only_quarter(self):
        """Formats 1/4 with unicode."""
        result = GroceryService._format_quantity(0, 1, 4)
        assert result == "¼"

    def test_fraction_only_three_quarters(self):
        """Formats 3/4 with unicode."""
        result = GroceryService._format_quantity(0, 3, 4)
        assert result == "¾"

    def test_fraction_only_third(self):
        """Formats 1/3 with unicode."""
        result = GroceryService._format_quantity(0, 1, 3)
        assert result == "⅓"

    def test_fraction_only_two_thirds(self):
        """Formats 2/3 with unicode."""
        result = GroceryService._format_quantity(0, 2, 3)
        assert result == "⅔"

    def test_mixed_number(self):
        """Formats mixed number with unicode fraction."""
        result = GroceryService._format_quantity(1, 1, 2)
        assert result == "1 ½"

    def test_mixed_number_three_quarters(self):
        """Formats 2 3/4 correctly."""
        result = GroceryService._format_quantity(2, 3, 4)
        assert result == "2 ¾"

    def test_uncommon_fraction_uses_slash(self):
        """Falls back to slash notation for uncommon fractions."""
        result = GroceryService._format_quantity(0, 5, 7)
        assert result == "5/7"

    def test_mixed_uncommon_fraction(self):
        """Mixed number with uncommon fraction."""
        result = GroceryService._format_quantity(3, 5, 7)
        assert result == "3 5/7"


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

    def test_large_volume_uses_liters(self):
        """Test large volume quantities use liters."""
        # 5 liters (5000ml) should display as L
        result = GroceryService._get_display_quantities(5.0, "liter")
        assert "L" in result["metric"]

    def test_large_weight_uses_kilograms(self):
        """Test large weight quantities use kg."""
        # 2 kg should display as kg
        result = GroceryService._get_display_quantities(2.0, "kilogram")
        assert "kg" in result["metric"]

    def test_small_volume_uses_milliliters(self):
        """Test small volume quantities use ml."""
        result = GroceryService._get_display_quantities(2.0, "tablespoon")
        # Should show ml for metric
        assert result["metric"] is not None
        assert "ml" in result["metric"]

    def test_small_weight_uses_grams(self):
        """Test small weight quantities use grams."""
        result = GroceryService._get_display_quantities(4.0, "ounce")
        # Should show g for metric
        assert result["metric"] is not None
        assert "g" in result["metric"]

    def test_large_ounces_converts_to_pounds(self):
        """Test large ounce quantities convert to pounds."""
        # 32 oz = 2 lbs
        result = GroceryService._get_display_quantities(32.0, "ounce")
        assert "lbs" in result["imperial"]

    def test_teaspoon_display(self):
        """Test teaspoon display quantities."""
        result = GroceryService._get_display_quantities(2.0, "teaspoon")
        assert result["display"] == "2 teaspoon"
        assert result["metric"] is not None
        assert result["imperial"] is not None

    def test_decimal_no_unit(self):
        """Test decimal quantity with no unit."""
        result = GroceryService._get_display_quantities(3.5, "")
        assert result["display"] == "3.5"
        assert result["metric"] is None
        assert result["imperial"] is None


class TestAggregateWithPintEdgeCases:
    """Additional edge cases for _aggregate_with_pint()."""

    def test_weight_aggregation(self):
        """Test aggregation of weight units."""
        recipe_id1 = uuid4()
        recipe_id2 = uuid4()

        ing1 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id1,
            ingredient_name="Flour",
            quantity=100.0,
            unit="gram",
            order=1,
        )

        ing2 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id2,
            ingredient_name="Flour",
            quantity=4.0,
            unit="ounce",
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing1, ing2],
            ingredient_name="Flour",
        )

        # Should convert to canonical weight (gram)
        assert result[0]["unit"] == "gram"
        # 100g + ~113g (4oz) ≈ 213g
        assert result[0]["total_quantity"] > 200

    def test_mixed_dimensionalities_separate_results(self):
        """Test that mixed dimensionalities produce separate results."""
        recipe_id1 = uuid4()
        recipe_id2 = uuid4()
        recipe_id3 = uuid4()

        # Volume
        ing1 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id1,
            ingredient_name="Chicken",
            quantity=1.0,
            unit="cup",
            order=1,
        )

        # Weight
        ing2 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id2,
            ingredient_name="Chicken",
            quantity=8.0,
            unit="ounce",
            order=1,
        )

        # Count
        ing3 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id3,
            ingredient_name="Chicken",
            quantity=2.0,
            unit="whole",
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing1, ing2, ing3],
            ingredient_name="Chicken",
        )

        # Should have 3 separate results (volume, weight, count)
        assert len(result) == 3

    def test_empty_ingredients_list(self):
        """Test handling of empty ingredients list."""
        result = GroceryService._aggregate_with_pint(
            ingredients=[],
            ingredient_name="Nothing",
        )

        # Should return default item with 0 quantity
        assert len(result) == 1
        assert result[0]["total_quantity"] == 0
        assert result[0]["unit"] == "item"

    def test_all_none_quantities(self):
        """Test when all ingredients have None quantities."""
        recipe_id = uuid4()

        ing = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id,
            ingredient_name="Salt",
            quantity=None,
            unit="to taste",
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing],
            ingredient_name="Salt",
        )

        # Should return default with empty details
        assert len(result) == 1
        assert result[0]["source_recipe_details"] == []

    def test_clove_unit_aggregation(self):
        """Test 'clove' as non-convertible unit aggregates correctly."""
        recipe_id1 = uuid4()
        recipe_id2 = uuid4()

        ing1 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id1,
            ingredient_name="Garlic",
            quantity=3.0,
            unit="clove",
            order=1,
        )

        ing2 = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id2,
            ingredient_name="Garlic",
            quantity=2.0,
            unit="clove",
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing1, ing2],
            ingredient_name="Garlic",
        )

        # Should preserve unit and sum quantities
        assert result[0]["unit"] == "clove"
        assert result[0]["total_quantity"] == 5.0

    def test_pinch_unit_aggregation(self):
        """Test 'pinch' as non-convertible unit."""
        recipe_id = uuid4()

        ing = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id,
            ingredient_name="Nutmeg",
            quantity=2.0,
            unit="pinch",
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing],
            ingredient_name="Nutmeg",
        )

        assert result[0]["unit"] == "pinch"
        assert result[0]["total_quantity"] == 2.0

    def test_enum_unit_handled(self):
        """Test that enum unit values are handled properly."""
        recipe_id = uuid4()

        ing = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id,
            ingredient_name="Water",
            quantity=2.0,
            unit=IngredientUnit.CUP,  # Enum instead of string
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing],
            ingredient_name="Water",
        )

        # Should handle enum and preserve/convert appropriately
        assert result[0]["total_quantity"] == 2.0
        details = result[0]["source_recipe_details"]
        assert details[0]["unit"] == "cup"  # Converted from enum

    def test_unknown_unit_treated_as_count(self):
        """Test that unknown units are treated as count."""
        recipe_id = uuid4()

        ing = RecipeIngredient(
            id=uuid4(),
            recipe_id=recipe_id,
            ingredient_name="Mystery",
            quantity=5.0,
            unit="foobar",  # Unknown unit
            order=1,
        )

        result = GroceryService._aggregate_with_pint(
            ingredients=[ing],
            ingredient_name="Mystery",
        )

        # Should keep the unit as-is (count category)
        assert result[0]["unit"] == "foobar"
        assert result[0]["total_quantity"] == 5.0
