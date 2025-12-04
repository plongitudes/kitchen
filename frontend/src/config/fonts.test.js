import { describe, it, expect } from 'vitest';
import { AVAILABLE_FONTS, DEFAULT_FONT } from './fonts';

describe('Font Configuration', () => {
  it('should have a default font', () => {
    expect(DEFAULT_FONT).toBe('silkscreen');
  });

  it('should include all required Google Fonts', () => {
    const expectedFonts = [
      'silkscreen',
      'pixelifySans',
      'jersey10',
      'tiny5',
      'vt323',
      'pressStart2p',
    ];

    expectedFonts.forEach(fontKey => {
      expect(AVAILABLE_FONTS[fontKey]).toBeDefined();
    });
  });

  it('should not include removed fonts', () => {
    expect(AVAILABLE_FONTS.micro5).toBeUndefined();
    expect(AVAILABLE_FONTS.dotGothic16).toBeUndefined();
    expect(AVAILABLE_FONTS.shareTechMono).toBeUndefined();
    expect(AVAILABLE_FONTS.ibmPlexMono).toBeUndefined();
    expect(AVAILABLE_FONTS.courierPrime).toBeUndefined();
  });

  it('should have all required properties for each font', () => {
    Object.entries(AVAILABLE_FONTS).forEach(([key, font]) => {
      expect(font.name).toBeDefined();
      expect(font.family).toBeDefined();
      expect(font.googleFonts).toBeDefined();
      expect(font.size).toBeDefined();
      expect(font.lineHeight).toBeDefined();
      expect(font.description).toBeDefined();
    });
  });

  it('should have valid CSS font-family strings', () => {
    Object.entries(AVAILABLE_FONTS).forEach(([key, font]) => {
      expect(font.family).toContain("'");
      expect(font.family).toMatch(/^'[^']+'/);
    });
  });

  it('should have valid size values', () => {
    Object.entries(AVAILABLE_FONTS).forEach(([key, font]) => {
      expect(font.size).toMatch(/^\d+px$/);
    });
  });

  it('should have numeric lineHeight values', () => {
    Object.entries(AVAILABLE_FONTS).forEach(([key, font]) => {
      const lineHeight = parseFloat(font.lineHeight);
      expect(lineHeight).toBeGreaterThan(0);
      expect(lineHeight).toBeLessThan(3);
    });
  });

  it('should have unique Google Fonts URLs', () => {
    const urls = Object.values(AVAILABLE_FONTS).map(f => f.googleFonts);
    const uniqueUrls = new Set(urls);
    expect(uniqueUrls.size).toBe(urls.length);
  });
});
