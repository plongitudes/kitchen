"""Utility functions for parsing ingredient strings from recipe imports."""
import re
from typing import Optional, Tuple

from app.models.recipe import IngredientUnit


# Common fraction unicode characters and their decimal values
FRACTION_MAP = {
    '¼': 0.25,
    '½': 0.5,
    '¾': 0.75,
    '⅓': 0.333,
    '⅔': 0.667,
    '⅕': 0.2,
    '⅖': 0.4,
    '⅗': 0.6,
    '⅘': 0.8,
    '⅙': 0.167,
    '⅚': 0.833,
    '⅛': 0.125,
    '⅜': 0.375,
    '⅝': 0.625,
    '⅞': 0.875,
}

# Map common unit names to our enum values
UNIT_ALIASES = {
    # Volume
    'cups': IngredientUnit.CUP,
    'cup': IngredientUnit.CUP,
    'c': IngredientUnit.CUP,
    'tbsp': IngredientUnit.TABLESPOON,
    'tablespoons': IngredientUnit.TABLESPOON,
    'tablespoon': IngredientUnit.TABLESPOON,
    'tbs': IngredientUnit.TABLESPOON,
    'T': IngredientUnit.TABLESPOON,
    'tsp': IngredientUnit.TEASPOON,
    'teaspoons': IngredientUnit.TEASPOON,
    'teaspoon': IngredientUnit.TEASPOON,
    't': IngredientUnit.TEASPOON,
    'fl oz': IngredientUnit.FLUID_OUNCE,
    'fluid ounce': IngredientUnit.FLUID_OUNCE,
    'fluid ounces': IngredientUnit.FLUID_OUNCE,
    'pint': IngredientUnit.PINT,
    'pints': IngredientUnit.PINT,
    'pt': IngredientUnit.PINT,
    'quart': IngredientUnit.QUART,
    'quarts': IngredientUnit.QUART,
    'qt': IngredientUnit.QUART,
    'gallon': IngredientUnit.GALLON,
    'gallons': IngredientUnit.GALLON,
    'gal': IngredientUnit.GALLON,
    'ml': IngredientUnit.ML,
    'milliliter': IngredientUnit.ML,
    'milliliters': IngredientUnit.ML,
    'liter': IngredientUnit.LITER,
    'liters': IngredientUnit.LITER,
    'l': IngredientUnit.LITER,

    # Weight
    'gram': IngredientUnit.GRAM,
    'grams': IngredientUnit.GRAM,
    'g': IngredientUnit.GRAM,
    'kilogram': IngredientUnit.KILOGRAM,
    'kilograms': IngredientUnit.KILOGRAM,
    'kg': IngredientUnit.KILOGRAM,
    'ounce': IngredientUnit.OUNCE,
    'ounces': IngredientUnit.OUNCE,
    'oz': IngredientUnit.OUNCE,
    'pound': IngredientUnit.POUND,
    'pounds': IngredientUnit.POUND,
    'lb': IngredientUnit.POUND,
    'lbs': IngredientUnit.POUND,

    # Count
    'count': IngredientUnit.COUNT,
    'whole': IngredientUnit.WHOLE,
    'item': IngredientUnit.ITEM,
    'items': IngredientUnit.ITEM,

    # Special
    'bunch': IngredientUnit.BUNCH,
    'bunches': IngredientUnit.BUNCH,
    'clove': IngredientUnit.CLOVE,
    'cloves': IngredientUnit.CLOVE,
    'can': IngredientUnit.CAN,
    'cans': IngredientUnit.CAN,
    'jar': IngredientUnit.JAR,
    'jars': IngredientUnit.JAR,
    'package': IngredientUnit.PACKAGE,
    'packages': IngredientUnit.PACKAGE,
    'pinch': IngredientUnit.PINCH,
    'pinches': IngredientUnit.PINCH,
    'dash': IngredientUnit.DASH,
    'dashes': IngredientUnit.DASH,
    'to taste': IngredientUnit.TO_TASTE,
}


def parse_fraction(fraction_str: str) -> float:
    """Convert fraction string to decimal.

    Handles:
    - Unicode fractions: ½, ¼, ¾, etc.
    - Plain fractions: 1/2, 3/4, etc.
    - Mixed numbers: 1 1/2, 2 3/4, etc.
    """
    # Check unicode fractions first
    for char, value in FRACTION_MAP.items():
        if char in fraction_str:
            return value

    # Handle plain fraction like "1/2"
    if '/' in fraction_str:
        parts = fraction_str.split('/')
        if len(parts) == 2:
            try:
                return float(parts[0]) / float(parts[1])
            except (ValueError, ZeroDivisionError):
                return 1.0

    return 1.0


def parse_quantity(quantity_str: str) -> float:
    """Parse quantity string to float.

    Handles:
    - Simple numbers: "2", "3.5"
    - Fractions: "1/2", "¾"
    - Mixed numbers: "1 1/2", "2 ¾"
    - Ranges: "2-3" (uses midpoint)
    """
    quantity_str = quantity_str.strip()

    # Handle ranges like "2-3 cups" - use midpoint
    if '-' in quantity_str:
        parts = quantity_str.split('-')
        if len(parts) == 2:
            try:
                low = float(parts[0])
                high = float(parts[1])
                return (low + high) / 2
            except ValueError:
                pass

    # Handle mixed numbers like "1 1/2"
    if ' ' in quantity_str:
        parts = quantity_str.split()
        try:
            whole = float(parts[0])
            if len(parts) > 1:
                fraction = parse_fraction(parts[1])
                return whole + fraction
        except ValueError:
            pass

    # Handle standalone fractions
    if '/' in quantity_str or any(char in quantity_str for char in FRACTION_MAP):
        return parse_fraction(quantity_str)

    # Simple number
    try:
        return float(quantity_str)
    except ValueError:
        return 1.0


def parse_ingredient_line(line: str) -> Tuple[Optional[float], Optional[IngredientUnit], str]:
    """Parse an ingredient line into quantity, unit, and name.

    Implements left-to-right parsing with context-aware slash handling:
    - Slashes in "number zone" (before first unit) = fractions
    - Slashes after a unit = alternative measurements (ignored)
    - Parenthetical measurements like "(10-ounce)" are stripped before parsing
    - If parse is ambiguous, returns full original line for user correction

    Args:
        line: Ingredient string like "2 cups flour" or "1 large onion, diced"

    Returns:
        Tuple of (quantity, unit, ingredient_name)
        If parsing fails or is ambiguous, returns (1.0, IngredientUnit.ITEM, original_line)

    Examples:
        "2 cups flour" -> (2.0, IngredientUnit.CUP, "flour")
        "1 1/2 tbsp olive oil" -> (1.5, IngredientUnit.TABLESPOON, "olive oil")
        "1 3/4 cups/231 grams flour" -> (1.75, IngredientUnit.CUP, "flour")
        "1 (10-ounce) package spinach" -> (1.0, IngredientUnit.PACKAGE, "frozen chopped spinach")
        "3 large eggs" -> (3.0, IngredientUnit.COUNT, "large eggs")
        "salt to taste" -> (1.0, IngredientUnit.TO_TASTE, "salt")
    """
    original_line = line.strip()

    # Step 0: Strip parenthetical measurements like "(10-ounce)" or "(dry)"
    # Pattern: (NUMBER UNIT) or (ADJECTIVE) at the start of the line after initial number
    # Example: "1 (10-ounce) package" -> "1 package"
    # Example: "9 ounces (dry) lasagna" -> "9 ounces lasagna"
    line = re.sub(r'\([^)]*\)', '', line).strip()
    # Clean up any double spaces left behind
    line = re.sub(r'\s+', ' ', line)

    # Step 1: Check for alternative measurements and strip them
    # Strategy: Find slashes that have a unit word immediately before them
    # These are "alternative measurement slashes", not "fraction slashes"
    # Example: "1 3/4 cups/231 grams all-purpose flour" - the slash after "cups" is the alternative
    ingredient_suffix = ""  # Text after alternative measurement (the actual ingredient name)
    if '/' in original_line:
        # Find all slashes and check context around each one
        slash_positions = [i for i, char in enumerate(original_line) if char == '/']

        for slash_pos in slash_positions:
            # Get the word before the slash
            before_slash = original_line[:slash_pos].strip()
            after_slash = original_line[slash_pos + 1:].strip()

            # Check if there's a unit word immediately before this slash
            before_words = before_slash.lower().split()
            if before_words:
                last_word_before = before_words[-1]
                # Check if last word before slash is a unit
                is_unit_before = (last_word_before in UNIT_ALIASES or
                                  last_word_before.rstrip('s') in UNIT_ALIASES)

                if is_unit_before and after_slash and after_slash[0].isdigit():
                    # This slash comes after a unit and before a number
                    # This is an alternative measurement separator
                    # Keep everything before this slash for parsing
                    line = before_slash

                    # Extract the ingredient name from after the alternative measurement
                    # Pattern: "231 grams all-purpose flour" -> want "all-purpose flour"
                    alt_parts = after_slash.split(None, 2)  # Split on whitespace, max 3 parts
                    if len(alt_parts) >= 3:
                        # Have: number, unit, ingredient_name
                        ingredient_suffix = alt_parts[2]
                    elif len(alt_parts) == 2:
                        # Check if second part is a unit or ingredient
                        second_word = alt_parts[1].lower()
                        if second_word not in UNIT_ALIASES and second_word.rstrip('s') not in UNIT_ALIASES:
                            # It's probably an ingredient
                            ingredient_suffix = alt_parts[1]

                    break

    # Step 2: Standard parsing with regex
    # Pattern: optional quantity + optional unit + optional ingredient name
    # Matches: "2 cups flour", "1½ cups sugar", "2-3 tablespoons butter", "1 3/4 cups"
    pattern = r'^([\d\s\-\/¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞\.]+)?\s*([a-zA-Z\s]+?)(?:\s+(.+))?$'

    match = re.match(pattern, line.strip())

    if not match:
        # No quantity/unit found, treat whole line as ingredient name with no unit
        return (1.0, None, original_line)

    quantity_str, unit_str, ingredient_name = match.groups()

    # Parse quantity
    quantity = 1.0
    if quantity_str:
        quantity = parse_quantity(quantity_str)

    # Parse unit
    unit = None
    unit_str_clean = unit_str.strip().lower() if unit_str else ""

    # Check for "to taste" special case
    if 'to taste' in line.lower():
        unit = IngredientUnit.TO_TASTE
        # Extract the ingredient name before "to taste"
        ingredient_name = line.lower().replace('to taste', '').strip()
        # Remove any remaining quantity/unit text
        ingredient_name = re.sub(r'^[\d\s\-\/¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞\.]+', '', ingredient_name).strip()
    elif unit_str_clean in UNIT_ALIASES:
        unit = UNIT_ALIASES[unit_str_clean]
    else:
        # If unit not recognized, include it in ingredient name
        if ingredient_name:
            ingredient_name = f"{unit_str.strip()} {ingredient_name}"
        else:
            ingredient_name = unit_str.strip() if unit_str else ""
        unit = IngredientUnit.ITEM

    # If no ingredient name was captured from the main parse, use the suffix we extracted
    # from after the alternative measurement
    if not ingredient_name or not ingredient_name.strip():
        if ingredient_suffix:
            ingredient_name = ingredient_suffix
        else:
            # No ingredient found anywhere
            ingredient_name = ""

    # Clean up ingredient name (remove trailing commas, notes in parentheses, etc.)
    ingredient_name = ingredient_name.strip()

    # Remove notes in parentheses at the end
    ingredient_name = re.sub(r'\s*\([^)]*\)\s*$', '', ingredient_name)

    # Remove trailing commas and extra notes
    if ',' in ingredient_name:
        ingredient_name = ingredient_name.split(',')[0].strip()

    # Step 3: Detect ambiguous/incomplete parses
    # If the parse seems uncertain, return full original line for user correction
    is_ambiguous = False

    # Check 1: Original line had a comma (indicates additional info we stripped)
    # This is ambiguous because the actual ingredient might be after the comma
    if ',' in original_line:
        is_ambiguous = True

    # Check 2: Ingredient name is too short (likely incomplete parse)
    if ingredient_name and len(ingredient_name.strip()) < 3:
        is_ambiguous = True

    # Check 3: Ingredient name contains numbers or measurement words (bad parse)
    if ingredient_name:
        ingredient_lower = ingredient_name.lower()
        # Check for numbers in ingredient name (excluding common cases like "7-grain")
        if re.search(r'\b\d+\s+(ounce|gram|cup|tablespoon|teaspoon)', ingredient_lower):
            is_ambiguous = True

    # Check 4: Unit is ITEM and ingredient name looks like it has a real unit
    if unit == IngredientUnit.ITEM and ingredient_name:
        ingredient_lower = ingredient_name.lower()
        # Check if any real unit word appears in ingredient name
        real_units = ['package', 'jar', 'can', 'bunch', 'clove', 'cup', 'ounce', 'gram',
                      'tablespoon', 'teaspoon', 'pound', 'liter']
        if any(f' {unit_word}' in f' {ingredient_lower}' or
               ingredient_lower.startswith(f'{unit_word} ')
               for unit_word in real_units):
            is_ambiguous = True

    # If ambiguous, return full original line for manual correction with no unit
    if is_ambiguous:
        return (1.0, None, original_line)

    return (quantity, unit, ingredient_name)
