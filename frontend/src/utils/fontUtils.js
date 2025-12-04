/**
 * Font utility functions
 * Shared helpers for font management across the application
 */

/**
 * Generate a unique key for a custom font based on its name
 * @param {string} fontName - The display name of the font
 * @returns {string} - A URL-safe key for the font (e.g., "custom-my-font")
 */
export const getCustomFontKey = (fontName) => {
  return `custom-${fontName.toLowerCase().replace(/\s+/g, '-')}`;
};
