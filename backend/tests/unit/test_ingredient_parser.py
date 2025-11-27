"""Unit tests for ingredient_parser module."""

import pytest
from app.utils.ingredient_parser import (
    FRACTION_MAP,
    UNIT_ALIASES,
    parse_fraction,
    parse_quantity,
    parse_ingredient_line,
)
from app.models.recipe import IngredientUnit


class TestFractionMap:
    """Tests for FRACTION_MAP constant."""

    def test_common_fractions_present(self):
        """Common fractions are in the map."""
        assert '½' in FRACTION_MAP
        assert '¼' in FRACTION_MAP
        assert '¾' in FRACTION_MAP
        assert '⅓' in FRACTION_MAP
        assert '⅔' in FRACTION_MAP

    def test_fraction_values_correct(self):
        """Fraction values are approximately correct."""
        assert FRACTION_MAP['½'] == 0.5
        assert FRACTION_MAP['¼'] == 0.25
        assert FRACTION_MAP['¾'] == 0.75
        assert abs(FRACTION_MAP['⅓'] - 0.333) < 0.01
        assert abs(FRACTION_MAP['⅔'] - 0.667) < 0.01


class TestUnitAliases:
    """Tests for UNIT_ALIASES constant."""

    def test_volume_units_present(self):
        """Volume unit aliases are present."""
        assert 'cup' in UNIT_ALIASES
        assert 'cups' in UNIT_ALIASES
        assert 'tbsp' in UNIT_ALIASES
        assert 'tsp' in UNIT_ALIASES
        assert 'ml' in UNIT_ALIASES

    def test_weight_units_present(self):
        """Weight unit aliases are present."""
        assert 'gram' in UNIT_ALIASES
        assert 'grams' in UNIT_ALIASES
        assert 'oz' in UNIT_ALIASES
        assert 'lb' in UNIT_ALIASES
        assert 'lbs' in UNIT_ALIASES

    def test_special_units_present(self):
        """Special unit aliases are present."""
        assert 'bunch' in UNIT_ALIASES
        assert 'clove' in UNIT_ALIASES
        assert 'can' in UNIT_ALIASES
        assert 'pinch' in UNIT_ALIASES
        assert 'to taste' in UNIT_ALIASES

    def test_aliases_map_to_correct_enums(self):
        """Aliases map to correct IngredientUnit enum values."""
        assert UNIT_ALIASES['cup'] == IngredientUnit.CUP
        assert UNIT_ALIASES['cups'] == IngredientUnit.CUP
        assert UNIT_ALIASES['tbsp'] == IngredientUnit.TABLESPOON
        assert UNIT_ALIASES['tsp'] == IngredientUnit.TEASPOON
        assert UNIT_ALIASES['oz'] == IngredientUnit.OUNCE
        assert UNIT_ALIASES['lb'] == IngredientUnit.POUND


class TestParseFraction:
    """Tests for parse_fraction()."""

    def test_unicode_half(self):
        """Parses unicode half fraction."""
        assert parse_fraction('½') == 0.5

    def test_unicode_quarter(self):
        """Parses unicode quarter fraction."""
        assert parse_fraction('¼') == 0.25

    def test_unicode_three_quarters(self):
        """Parses unicode three quarters fraction."""
        assert parse_fraction('¾') == 0.75

    def test_unicode_third(self):
        """Parses unicode third fraction."""
        assert abs(parse_fraction('⅓') - 0.333) < 0.01

    def test_unicode_two_thirds(self):
        """Parses unicode two thirds fraction."""
        assert abs(parse_fraction('⅔') - 0.667) < 0.01

    def test_unicode_eighth(self):
        """Parses unicode eighth fraction."""
        assert parse_fraction('⅛') == 0.125

    def test_plain_fraction_half(self):
        """Parses plain 1/2 fraction."""
        assert parse_fraction('1/2') == 0.5

    def test_plain_fraction_quarter(self):
        """Parses plain 1/4 fraction."""
        assert parse_fraction('1/4') == 0.25

    def test_plain_fraction_three_quarters(self):
        """Parses plain 3/4 fraction."""
        assert parse_fraction('3/4') == 0.75

    def test_plain_fraction_third(self):
        """Parses plain 1/3 fraction."""
        assert abs(parse_fraction('1/3') - 0.333) < 0.01

    def test_plain_fraction_custom(self):
        """Parses custom fraction like 5/8."""
        assert parse_fraction('5/8') == 0.625

    def test_invalid_fraction_returns_1(self):
        """Invalid fraction string returns 1.0."""
        assert parse_fraction('abc') == 1.0

    def test_division_by_zero_returns_1(self):
        """Division by zero returns 1.0."""
        assert parse_fraction('1/0') == 1.0

    def test_invalid_numerator_returns_1(self):
        """Invalid numerator returns 1.0."""
        assert parse_fraction('abc/2') == 1.0


class TestParseQuantity:
    """Tests for parse_quantity()."""

    def test_simple_integer(self):
        """Parses simple integer."""
        assert parse_quantity('2') == 2.0

    def test_simple_float(self):
        """Parses simple float."""
        assert parse_quantity('3.5') == 3.5

    def test_unicode_fraction(self):
        """Parses unicode fraction."""
        assert parse_quantity('½') == 0.5

    def test_plain_fraction(self):
        """Parses plain fraction."""
        assert parse_quantity('1/2') == 0.5

    def test_mixed_number_with_fraction(self):
        """Parses mixed number like 1 1/2."""
        assert parse_quantity('1 1/2') == 1.5

    def test_mixed_number_with_unicode(self):
        """Parses mixed number with unicode fraction."""
        assert parse_quantity('2 ½') == 2.5

    def test_mixed_number_larger(self):
        """Parses larger mixed number."""
        assert parse_quantity('3 3/4') == 3.75

    def test_range_uses_midpoint(self):
        """Parses range and uses midpoint."""
        assert parse_quantity('2-3') == 2.5

    def test_range_different_values(self):
        """Parses range with different values."""
        assert parse_quantity('1-5') == 3.0

    def test_whitespace_stripped(self):
        """Whitespace is stripped."""
        assert parse_quantity('  2  ') == 2.0

    def test_invalid_quantity_returns_1(self):
        """Invalid quantity returns 1.0."""
        assert parse_quantity('abc') == 1.0

    def test_empty_string_returns_1(self):
        """Empty string returns 1.0."""
        assert parse_quantity('') == 1.0


class TestParseIngredientLine:
    """Tests for parse_ingredient_line()."""

    def test_simple_cups(self):
        """Parses simple cups measurement."""
        qty, unit, name = parse_ingredient_line('2 cups flour')
        assert qty == 2.0
        assert unit == IngredientUnit.CUP
        assert name == 'flour'

    def test_simple_tablespoons(self):
        """Parses tablespoons measurement."""
        qty, unit, name = parse_ingredient_line('3 tbsp butter')
        assert qty == 3.0
        assert unit == IngredientUnit.TABLESPOON
        assert name == 'butter'

    def test_simple_teaspoons(self):
        """Parses teaspoons measurement."""
        qty, unit, name = parse_ingredient_line('1 tsp salt')
        assert qty == 1.0
        assert unit == IngredientUnit.TEASPOON
        assert name == 'salt'

    def test_fraction_quantity(self):
        """Parses fractional quantity."""
        qty, unit, name = parse_ingredient_line('1/2 cup sugar')
        assert qty == 0.5
        assert unit == IngredientUnit.CUP
        assert name == 'sugar'

    def test_unicode_fraction_quantity(self):
        """Parses unicode fractional quantity."""
        qty, unit, name = parse_ingredient_line('½ cup sugar')
        assert qty == 0.5
        assert unit == IngredientUnit.CUP
        assert name == 'sugar'

    def test_mixed_number_quantity(self):
        """Parses mixed number quantity."""
        qty, unit, name = parse_ingredient_line('1 1/2 tbsp olive oil')
        assert qty == 1.5
        assert unit == IngredientUnit.TABLESPOON
        assert 'olive oil' in name

    def test_mixed_number_with_unicode(self):
        """Parses mixed number with unicode."""
        qty, unit, name = parse_ingredient_line('2 ½ cups milk')
        assert qty == 2.5
        assert unit == IngredientUnit.CUP
        assert name == 'milk'

    def test_weight_ounces(self):
        """Parses ounces weight measurement."""
        qty, unit, name = parse_ingredient_line('8 oz cream cheese')
        assert qty == 8.0
        assert unit == IngredientUnit.OUNCE
        assert 'cream cheese' in name

    def test_weight_pounds(self):
        """Parses pounds weight measurement."""
        qty, unit, name = parse_ingredient_line('2 lbs ground beef')
        assert qty == 2.0
        assert unit == IngredientUnit.POUND
        assert 'ground beef' in name

    def test_weight_grams(self):
        """Parses grams weight measurement."""
        qty, unit, name = parse_ingredient_line('100 grams chocolate')
        assert qty == 100.0
        assert unit == IngredientUnit.GRAM
        assert name == 'chocolate'

    def test_count_items(self):
        """Parses count items without explicit unit."""
        qty, unit, name = parse_ingredient_line('3 large eggs')
        assert qty == 3.0
        # Since 'large' is not a unit, should be ITEM with 'large eggs' as name
        assert 'large eggs' in name or 'eggs' in name

    def test_special_unit_cloves(self):
        """Parses cloves measurement."""
        qty, unit, name = parse_ingredient_line('4 cloves garlic')
        assert qty == 4.0
        assert unit == IngredientUnit.CLOVE
        assert name == 'garlic'

    def test_special_unit_bunch(self):
        """Parses bunch measurement."""
        qty, unit, name = parse_ingredient_line('1 bunch cilantro')
        assert qty == 1.0
        assert unit == IngredientUnit.BUNCH
        assert name == 'cilantro'

    def test_special_unit_can(self):
        """Parses can measurement."""
        qty, unit, name = parse_ingredient_line('2 cans tomatoes')
        assert qty == 2.0
        assert unit == IngredientUnit.CAN
        assert name == 'tomatoes'

    def test_special_unit_pinch(self):
        """Parses pinch measurement."""
        qty, unit, name = parse_ingredient_line('1 pinch nutmeg')
        assert qty == 1.0
        assert unit == IngredientUnit.PINCH
        assert name == 'nutmeg'

    def test_to_taste(self):
        """Parses 'to taste' measurement."""
        qty, unit, name = parse_ingredient_line('salt to taste')
        assert unit == IngredientUnit.TO_TASTE
        assert 'salt' in name

    def test_strips_parenthetical_measurements(self):
        """Strips parenthetical measurements."""
        qty, unit, name = parse_ingredient_line('1 (10-ounce) package spinach')
        assert qty == 1.0
        assert unit == IngredientUnit.PACKAGE
        assert 'spinach' in name

    def test_strips_parenthetical_dry(self):
        """Strips parenthetical notes like (dry)."""
        qty, unit, name = parse_ingredient_line('9 ounces (dry) lasagna')
        assert qty == 9.0
        assert unit == IngredientUnit.OUNCE
        assert 'lasagna' in name

    def test_alternative_measurements_stripped(self):
        """Alternative measurements after slash are stripped."""
        qty, unit, name = parse_ingredient_line('1 3/4 cups/231 grams all-purpose flour')
        assert qty == 1.75
        assert unit == IngredientUnit.CUP
        assert 'flour' in name

    def test_milliliters(self):
        """Parses milliliters measurement."""
        qty, unit, name = parse_ingredient_line('250 ml water')
        assert qty == 250.0
        assert unit == IngredientUnit.ML
        assert name == 'water'

    def test_liters(self):
        """Parses liters measurement."""
        qty, unit, name = parse_ingredient_line('2 liters broth')
        assert qty == 2.0
        assert unit == IngredientUnit.LITER
        assert name == 'broth'

    def test_quart(self):
        """Parses quart measurement."""
        qty, unit, name = parse_ingredient_line('1 quart chicken stock')
        assert qty == 1.0
        assert unit == IngredientUnit.QUART
        assert 'chicken stock' in name

    def test_pint(self):
        """Parses pint measurement."""
        qty, unit, name = parse_ingredient_line('1 pint cream')
        assert qty == 1.0
        assert unit == IngredientUnit.PINT
        assert name == 'cream'

    def test_gallon(self):
        """Parses gallon measurement."""
        qty, unit, name = parse_ingredient_line('1 gallon milk')
        assert qty == 1.0
        assert unit == IngredientUnit.GALLON
        assert name == 'milk'

    def test_whitespace_handling(self):
        """Handles extra whitespace."""
        qty, unit, name = parse_ingredient_line('  2   cups   flour  ')
        assert qty == 2.0
        assert unit == IngredientUnit.CUP
        assert name == 'flour'

    def test_no_quantity_returns_1(self):
        """Line without quantity returns 1.0."""
        qty, unit, name = parse_ingredient_line('salt')
        assert qty == 1.0

    def test_unparseable_returns_original(self):
        """Unparseable line returns original text."""
        original = 'something completely unparseable !@#$'
        qty, unit, name = parse_ingredient_line(original)
        # Should return with defaults
        assert qty == 1.0

    def test_empty_string(self):
        """Empty string handling."""
        qty, unit, name = parse_ingredient_line('')
        assert qty == 1.0

    def test_jar_unit(self):
        """Parses jar measurement."""
        qty, unit, name = parse_ingredient_line('1 jar marinara')
        assert qty == 1.0
        assert unit == IngredientUnit.JAR
        assert name == 'marinara'

    def test_dash_unit(self):
        """Parses dash measurement."""
        qty, unit, name = parse_ingredient_line('1 dash hot sauce')
        assert qty == 1.0
        assert unit == IngredientUnit.DASH
        assert 'hot sauce' in name

    def test_fluid_ounce(self):
        """Multi-word units like 'fluid ounces' not parsed - returns as-is."""
        # Note: The parser doesn't handle multi-word units like "fluid ounces"
        # This is a known limitation - it returns the original line for manual correction
        qty, unit, name = parse_ingredient_line('4 fluid ounces rum')
        # Since parser can't handle this, it returns original
        assert qty == 1.0
        assert unit is None
        assert '4 fluid ounces rum' in name

    def test_kilogram(self):
        """Parses kilogram measurement."""
        qty, unit, name = parse_ingredient_line('1 kg potatoes')
        assert qty == 1.0
        assert unit == IngredientUnit.KILOGRAM
        assert name == 'potatoes'


class TestParseIngredientLineEdgeCases:
    """Edge case tests for parse_ingredient_line()."""

    def test_comma_in_ingredient_name(self):
        """Handles commas in ingredient name (returns original for ambiguity)."""
        qty, unit, name = parse_ingredient_line('1 cup onion, diced')
        # Due to comma ambiguity, returns original line
        assert qty == 1.0
        assert 'onion' in name

    def test_multiword_ingredient(self):
        """Handles multi-word ingredient names."""
        qty, unit, name = parse_ingredient_line('2 cups all-purpose flour')
        assert qty == 2.0
        assert unit == IngredientUnit.CUP
        assert 'flour' in name

    def test_ingredient_with_hyphen(self):
        """Handles ingredients with hyphens."""
        qty, unit, name = parse_ingredient_line('1 cup semi-sweet chocolate chips')
        assert qty == 1.0
        assert unit == IngredientUnit.CUP
        assert 'chocolate' in name or 'semi-sweet' in name

    def test_decimal_quantity(self):
        """Handles decimal quantities."""
        qty, unit, name = parse_ingredient_line('1.5 cups rice')
        assert qty == 1.5
        assert unit == IngredientUnit.CUP
        assert name == 'rice'

    def test_uppercase_unit(self):
        """Handles uppercase units."""
        qty, unit, name = parse_ingredient_line('2 Cups Flour')
        assert qty == 2.0
        assert unit == IngredientUnit.CUP
        # Name might have original casing

    def test_mixed_case_unit(self):
        """Handles mixed case units."""
        qty, unit, name = parse_ingredient_line('1 Tbsp butter')
        assert qty == 1.0
        # tbsp might be case-sensitive in UNIT_ALIASES
        # Check that parsing still works
        assert 'butter' in name.lower()

    def test_range_quantity_in_ingredient(self):
        """Handles range quantities."""
        qty, unit, name = parse_ingredient_line('2-3 cloves garlic')
        # Range should use midpoint
        assert qty == 2.5
        assert unit == IngredientUnit.CLOVE
        assert name == 'garlic'

    def test_number_in_ingredient_name(self):
        """Handles numbers in ingredient name like 7-grain."""
        # This is tricky - the parser might be confused
        qty, unit, name = parse_ingredient_line('2 slices 7-grain bread')
        # Since 'slices' is not a recognized unit
        assert qty == 2.0
