/**
 * Utility functions for handling date-only strings (YYYY-MM-DD format).
 *
 * Problem: JavaScript's Date constructor interprets "2024-03-15" as UTC midnight,
 * which causes day-of-week shifts when displayed in non-UTC timezones.
 *
 * Solution: Parse date-only strings as local dates by extracting components.
 */

const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

/**
 * Parse a date-only string (YYYY-MM-DD) as a local date.
 *
 * @param {string} dateString - Date in YYYY-MM-DD format
 * @returns {Date} Date object representing local midnight
 *
 * @example
 * // In PST timezone:
 * new Date("2024-03-15")           // → March 14, 2024 4:00 PM (WRONG - UTC interpreted)
 * parseLocalDate("2024-03-15")     // → March 15, 2024 12:00 AM (CORRECT - local)
 */
export function parseLocalDate(dateString) {
  if (!dateString) return null;

  // Handle ISO datetime strings (with T) - use native parser for these
  if (dateString.includes('T')) {
    return new Date(dateString);
  }

  // Parse YYYY-MM-DD as local date
  const [year, month, day] = dateString.split('-').map(Number);
  const date = new Date(year, month - 1, day);

  // Validate the result - invalid inputs create NaN dates
  if (isNaN(date.getTime())) return null;

  return date;
}

/**
 * Format a date-only string for display.
 *
 * @param {string} dateString - Date in YYYY-MM-DD format
 * @param {Intl.DateTimeFormatOptions} options - Formatting options
 * @returns {string} Formatted date string
 *
 * @example
 * formatLocalDate("2024-03-15")  // → "Mar 15, 2024"
 * formatLocalDate("2024-03-15", { weekday: 'long' })  // → "Friday, Mar 15, 2024"
 */
export function formatLocalDate(dateString, options = {}) {
  const date = parseLocalDate(dateString);
  if (!date) return '';

  const defaultOptions = { month: 'short', day: 'numeric', year: 'numeric' };
  return date.toLocaleDateString('en-US', { ...defaultOptions, ...options });
}

/**
 * Get the day name for a date-only string.
 *
 * @param {string} dateString - Date in YYYY-MM-DD format
 * @returns {string} Day name (e.g., "Monday")
 */
export function getDayName(dateString) {
  const date = parseLocalDate(dateString);
  if (!date) return '';

  return DAY_NAMES[date.getDay()];
}

/**
 * Check if a date-only string represents today.
 *
 * @param {string} dateString - Date in YYYY-MM-DD format
 * @returns {boolean} True if the date is today
 */
export function isToday(dateString) {
  const date = parseLocalDate(dateString);
  if (!date) return false;

  return new Date().toDateString() === date.toDateString();
}
