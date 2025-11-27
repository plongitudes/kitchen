import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  parseLocalDate,
  formatLocalDate,
  getDayName,
  isToday,
} from '../../../utils/dateUtils';

describe('dateUtils', () => {
  describe('parseLocalDate', () => {
    it('parses YYYY-MM-DD as local date, not UTC', () => {
      const date = parseLocalDate('2024-03-15');

      // The key test: should be March 15, not March 14 (which happens with UTC interpretation)
      expect(date.getDate()).toBe(15);
      expect(date.getMonth()).toBe(2); // March is 0-indexed
      expect(date.getFullYear()).toBe(2024);
    });

    it('returns null for null input', () => {
      expect(parseLocalDate(null)).toBe(null);
    });

    it('returns null for undefined input', () => {
      expect(parseLocalDate(undefined)).toBe(null);
    });

    it('returns null for empty string', () => {
      expect(parseLocalDate('')).toBe(null);
    });

    it('handles ISO datetime strings with T by using native parser', () => {
      const date = parseLocalDate('2024-03-15T12:30:00Z');

      // Should use native Date parser for datetime strings
      expect(date).toBeInstanceOf(Date);
      expect(date.getFullYear()).toBe(2024);
    });

    it('parses dates at year boundaries correctly', () => {
      const newYearsEve = parseLocalDate('2024-12-31');
      expect(newYearsEve.getDate()).toBe(31);
      expect(newYearsEve.getMonth()).toBe(11); // December

      const newYearsDay = parseLocalDate('2025-01-01');
      expect(newYearsDay.getDate()).toBe(1);
      expect(newYearsDay.getMonth()).toBe(0); // January
    });

    it('returns null for malformed date strings', () => {
      expect(parseLocalDate('not-a-date')).toBe(null);
      expect(parseLocalDate('2024')).toBe(null);
      expect(parseLocalDate('abc-def-ghi')).toBe(null);
    });
  });

  describe('formatLocalDate', () => {
    it('formats date with default options (short month, day, year)', () => {
      const result = formatLocalDate('2024-03-15');

      // Default format: "Mar 15, 2024"
      expect(result).toContain('Mar');
      expect(result).toContain('15');
      expect(result).toContain('2024');
    });

    it('formats date with custom options', () => {
      const result = formatLocalDate('2024-03-15', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      });

      // Should include Friday and March
      expect(result).toContain('Friday');
      expect(result).toContain('March');
      expect(result).toContain('15');
    });

    it('returns empty string for null input', () => {
      expect(formatLocalDate(null)).toBe('');
    });

    it('returns empty string for empty string input', () => {
      expect(formatLocalDate('')).toBe('');
    });

    it('can format without year', () => {
      const result = formatLocalDate('2024-03-15', {
        month: 'short',
        day: 'numeric',
        year: undefined,
      });

      expect(result).toContain('Mar');
      expect(result).toContain('15');
      // Year might or might not be present depending on locale defaults
    });
  });

  describe('getDayName', () => {
    it('returns correct day name for a known date', () => {
      // March 15, 2024 is a Friday
      expect(getDayName('2024-03-15')).toBe('Friday');
    });

    it('returns correct day names for all days of week', () => {
      // Week of March 10-16, 2024
      expect(getDayName('2024-03-10')).toBe('Sunday');
      expect(getDayName('2024-03-11')).toBe('Monday');
      expect(getDayName('2024-03-12')).toBe('Tuesday');
      expect(getDayName('2024-03-13')).toBe('Wednesday');
      expect(getDayName('2024-03-14')).toBe('Thursday');
      expect(getDayName('2024-03-15')).toBe('Friday');
      expect(getDayName('2024-03-16')).toBe('Saturday');
    });

    it('returns empty string for null input', () => {
      expect(getDayName(null)).toBe('');
    });

    it('returns empty string for empty string input', () => {
      expect(getDayName('')).toBe('');
    });
  });

  describe('isToday', () => {
    beforeEach(() => {
      // Mock Date to control "today"
      vi.useFakeTimers();
      vi.setSystemTime(new Date(2024, 2, 15)); // March 15, 2024
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('returns true for today\'s date', () => {
      expect(isToday('2024-03-15')).toBe(true);
    });

    it('returns false for yesterday', () => {
      expect(isToday('2024-03-14')).toBe(false);
    });

    it('returns false for tomorrow', () => {
      expect(isToday('2024-03-16')).toBe(false);
    });

    it('returns false for a different month', () => {
      expect(isToday('2024-04-15')).toBe(false);
    });

    it('returns false for a different year', () => {
      expect(isToday('2023-03-15')).toBe(false);
    });

    it('returns false for null input', () => {
      expect(isToday(null)).toBe(false);
    });

    it('returns false for empty string', () => {
      expect(isToday('')).toBe(false);
    });
  });
});
