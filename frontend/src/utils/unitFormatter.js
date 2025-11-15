/**
 * Utility for formatting grocery list quantities and units.
 * Handles fractions, pluralization, and abbreviations for better readability.
 */

// Unicode fraction characters
const FRACTIONS = {
  0.125: '⅛',
  0.25: '¼',
  0.333: '⅓',
  0.375: '⅜',
  0.5: '½',
  0.625: '⅝',
  0.666: '⅔',
  0.667: '⅔',
  0.75: '¾',
  0.875: '⅞',
};

// Unit abbreviations and plural forms
const UNIT_CONFIG = {
  // Volume
  cup: { abbr: 'cup', plural: 'cups', short: false },
  tablespoon: { abbr: 'tbsp', plural: 'tbsp', short: true },
  teaspoon: { abbr: 'tsp', plural: 'tsp', short: true },
  fluid_ounce: { abbr: 'fl oz', plural: 'fl oz', short: true },
  pint: { abbr: 'pint', plural: 'pints', short: false },
  quart: { abbr: 'quart', plural: 'quarts', short: false },
  gallon: { abbr: 'gallon', plural: 'gallons', short: false },
  ml: { abbr: 'ml', plural: 'ml', short: true },
  liter: { abbr: 'L', plural: 'L', short: true },

  // Weight
  gram: { abbr: 'g', plural: 'g', short: true },
  kilogram: { abbr: 'kg', plural: 'kg', short: true },
  ounce: { abbr: 'oz', plural: 'oz', short: true },
  pound: { abbr: 'lb', plural: 'lbs', short: true },

  // Count
  count: { abbr: '', plural: '', short: true },
  whole: { abbr: 'whole', plural: 'whole', short: false },
  item: { abbr: 'item', plural: 'items', short: false },

  // Special
  bunch: { abbr: 'bunch', plural: 'bunches', short: false },
  clove: { abbr: 'clove', plural: 'cloves', short: false },
  can: { abbr: 'can', plural: 'cans', short: false },
  pinch: { abbr: 'pinch', plural: 'pinches', short: false },
  dash: { abbr: 'dash', plural: 'dashes', short: false },
  to_taste: { abbr: 'to taste', plural: 'to taste', short: false },
};

/**
 * Convert decimal to mixed fraction if it's close to a common fraction.
 * Returns null if no good fraction match.
 */
function decimalToFraction(decimal, tolerance = 0.02) {
  // Check for exact or near matches to common fractions
  for (const [value, symbol] of Object.entries(FRACTIONS)) {
    if (Math.abs(decimal - parseFloat(value)) < tolerance) {
      return symbol;
    }
  }
  return null;
}

/**
 * Format a quantity as a mixed number with fractions where appropriate.
 * Examples:
 *   0.5 → "½"
 *   1.5 → "1½"
 *   2.333 → "2⅓"
 *   2.7 → "2.7" (no good fraction)
 */
function formatQuantity(quantity) {
  if (quantity === 0) return '0';
  if (quantity < 0) return quantity.toString();

  const wholePart = Math.floor(quantity);
  const decimalPart = quantity - wholePart;

  // If it's a whole number, return it
  if (decimalPart < 0.01) {
    return wholePart.toString();
  }

  // Try to find a fraction for the decimal part
  const fraction = decimalToFraction(decimalPart);

  if (fraction) {
    // We have a good fraction match
    if (wholePart === 0) {
      return fraction;
    } else {
      return `${wholePart}${fraction}`;
    }
  } else {
    // No good fraction - use decimal, but round to 1 decimal place
    const rounded = Math.round(quantity * 10) / 10;
    return rounded.toString();
  }
}

/**
 * Get the appropriate unit form (abbreviated and pluralized).
 */
function formatUnit(unit, quantity) {
  const config = UNIT_CONFIG[unit] || { abbr: unit, plural: `${unit}s`, short: false };

  // For abbreviated units, don't pluralize
  if (config.short) {
    return config.abbr;
  }

  // For full words, pluralize if quantity > 1
  // Note: "1½ cups" is plural, but "1 cup" is singular
  const needsPlural = quantity > 1;
  return needsPlural ? config.plural : config.abbr;
}

/**
 * Format a grocery list item quantity and unit.
 *
 * Examples:
 *   (2.5, "cup") → "2½ cups"
 *   (0.333, "teaspoon") → "⅓ tsp"
 *   (1, "tablespoon") → "1 tbsp"
 *   (3, "bunch") → "3 bunches"
 *   (150, "gram") → "150 g"
 */
export function formatGroceryItem(quantity, unit) {
  const formattedQty = formatQuantity(quantity);
  const formattedUnit = formatUnit(unit, quantity);

  if (!formattedUnit) {
    return formattedQty;
  }

  return `${formattedQty} ${formattedUnit}`;
}

/**
 * Export individual functions for testing or specific use cases.
 */
export { formatQuantity, formatUnit, decimalToFraction };
