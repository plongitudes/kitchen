/**
 * Utility functions for ingredient unit selection and display.
 *
 * Maps backend enum values to user-friendly display labels and organizes
 * units into logical categories for autocomplete/select dropdowns.
 */

/**
 * Unit categories matching the backend IngredientUnit enum groups
 */
export const UNIT_CATEGORIES = {
  VOLUME: 'Volume',
  WEIGHT: 'Weight',
  COUNT: 'Count',
  SPECIAL: 'Special',
};

/**
 * Complete list of units with their display labels and categories.
 * Matches backend/app/models/recipe.py IngredientUnit enum
 */
export const UNITS_CONFIG = [
  // Volume
  { value: 'cup', label: 'Cup', category: UNIT_CATEGORIES.VOLUME },
  { value: 'tablespoon', label: 'Tablespoon', category: UNIT_CATEGORIES.VOLUME },
  { value: 'teaspoon', label: 'Teaspoon', category: UNIT_CATEGORIES.VOLUME },
  { value: 'fluid_ounce', label: 'Fluid Ounce', category: UNIT_CATEGORIES.VOLUME },
  { value: 'pint', label: 'Pint', category: UNIT_CATEGORIES.VOLUME },
  { value: 'quart', label: 'Quart', category: UNIT_CATEGORIES.VOLUME },
  { value: 'gallon', label: 'Gallon', category: UNIT_CATEGORIES.VOLUME },
  { value: 'ml', label: 'Milliliter', category: UNIT_CATEGORIES.VOLUME },
  { value: 'liter', label: 'Liter', category: UNIT_CATEGORIES.VOLUME },

  // Weight
  { value: 'gram', label: 'Gram', category: UNIT_CATEGORIES.WEIGHT },
  { value: 'kilogram', label: 'Kilogram', category: UNIT_CATEGORIES.WEIGHT },
  { value: 'ounce', label: 'Ounce', category: UNIT_CATEGORIES.WEIGHT },
  { value: 'pound', label: 'Pound', category: UNIT_CATEGORIES.WEIGHT },

  // Count
  { value: 'count', label: 'Count', category: UNIT_CATEGORIES.COUNT },
  { value: 'whole', label: 'Whole', category: UNIT_CATEGORIES.COUNT },
  { value: 'item', label: 'Item', category: UNIT_CATEGORIES.COUNT },

  // Special
  { value: 'bunch', label: 'Bunch', category: UNIT_CATEGORIES.SPECIAL },
  { value: 'clove', label: 'Clove', category: UNIT_CATEGORIES.SPECIAL },
  { value: 'can', label: 'Can', category: UNIT_CATEGORIES.SPECIAL },
  { value: 'jar', label: 'Jar', category: UNIT_CATEGORIES.SPECIAL },
  { value: 'package', label: 'Package', category: UNIT_CATEGORIES.SPECIAL },
  { value: 'pinch', label: 'Pinch', category: UNIT_CATEGORIES.SPECIAL },
  { value: 'dash', label: 'Dash', category: UNIT_CATEGORIES.SPECIAL },
  { value: 'to taste', label: 'To Taste', category: UNIT_CATEGORIES.SPECIAL },
];

/**
 * Get display label for a unit value
 * @param {string} value - Unit value from backend (e.g., "fluid_ounce", "to taste")
 * @returns {string} Display label (e.g., "Fluid Ounce", "To Taste")
 */
export function formatUnitLabel(value) {
  const unit = UNITS_CONFIG.find((u) => u.value === value);
  return unit ? unit.label : value;
}

/**
 * Get grouped and sorted units for display in dropdowns
 * @returns {Object} Units grouped by category, sorted alphabetically within each group
 *
 * Example return:
 * {
 *   Volume: [{value: 'cup', label: 'Cup'}, ...],
 *   Weight: [{value: 'gram', label: 'Gram'}, ...],
 *   ...
 * }
 */
export function getGroupedUnits() {
  const grouped = {};

  // Group by category
  UNITS_CONFIG.forEach((unit) => {
    if (!grouped[unit.category]) {
      grouped[unit.category] = [];
    }
    grouped[unit.category].push({
      value: unit.value,
      label: unit.label,
      category: unit.category,
    });
  });

  // Sort alphabetically within each group
  Object.keys(grouped).forEach((category) => {
    grouped[category].sort((a, b) => a.label.localeCompare(b.label));
  });

  return grouped;
}

/**
 * Get flat list of all units (for search purposes)
 * @returns {Array} All units with value, label, and category
 */
export function getAllUnits() {
  return UNITS_CONFIG.map((unit) => ({
    value: unit.value,
    label: unit.label,
    category: unit.category,
  }));
}

/**
 * Get category order for consistent display
 * @returns {Array} Ordered list of category names
 */
export function getCategoryOrder() {
  return [
    UNIT_CATEGORIES.VOLUME,
    UNIT_CATEGORIES.WEIGHT,
    UNIT_CATEGORIES.COUNT,
    UNIT_CATEGORIES.SPECIAL,
  ];
}
