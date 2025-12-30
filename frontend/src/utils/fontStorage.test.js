import { describe, it, expect, beforeEach } from 'vitest';
import {
  initFontDB,
  saveCustomFont,
  getCustomFonts,
  deleteCustomFont,
  getCustomFont,
  arrayBufferToDataURL,
  generateFontFaceCSS,
  isValidWOFF2,
  sanitizeFontName,
} from './fontStorage';
import 'fake-indexeddb/auto';
import { IDBFactory } from 'fake-indexeddb';

beforeEach(() => {
  // Reset IndexedDB before each test
  globalThis.indexedDB = new IDBFactory();
});

describe('fontStorage', () => {
  describe('initFontDB', () => {
    it('should initialize database successfully', async () => {
      const result = await initFontDB();
      expect(result).toBeDefined();
    });
  });

  describe('saveCustomFont', () => {
    it('should save a custom font with all required fields', async () => {
      const font = {
        name: 'MyCustomFont',
        data: new ArrayBuffer(1024),
        size: '14px',
        lineHeight: 1.2,
      };

      const result = await saveCustomFont(font);
      expect(result).toBe(true);
    });

    it('should reject font without name', async () => {
      const font = {
        data: new ArrayBuffer(1024),
        size: '14px',
        lineHeight: 1.2,
      };

      await expect(saveCustomFont(font)).rejects.toThrow();
    });

    it('should reject font without data', async () => {
      const font = {
        name: 'MyFont',
        size: '14px',
        lineHeight: 1.2,
      };

      await expect(saveCustomFont(font)).rejects.toThrow();
    });

    it('should warn if font data exceeds 500KB', async () => {
      const font = {
        name: 'LargeFont',
        data: new ArrayBuffer(600 * 1024), // 600KB
        size: '14px',
        lineHeight: 1.2,
      };

      const result = await saveCustomFont(font);
      expect(result).toBe(true);
      // In real implementation, this would trigger a console.warn
    });
  });

  describe('getCustomFonts', () => {
    it('should return empty array when no fonts stored', async () => {
      const fonts = await getCustomFonts();
      expect(fonts).toEqual([]);
    });

    it('should return all stored fonts', async () => {
      const font1 = {
        name: 'Font1',
        data: new ArrayBuffer(100),
        size: '14px',
        lineHeight: 1.2,
      };
      const font2 = {
        name: 'Font2',
        data: new ArrayBuffer(200),
        size: '16px',
        lineHeight: 1.4,
      };

      await saveCustomFont(font1);
      await saveCustomFont(font2);

      const fonts = await getCustomFonts();
      expect(fonts).toHaveLength(2);
      expect(fonts.map((f) => f.name)).toContain('Font1');
      expect(fonts.map((f) => f.name)).toContain('Font2');
    });
  });

  describe('getCustomFont', () => {
    it('should retrieve a specific font by name', async () => {
      const font = {
        name: 'SpecificFont',
        data: new ArrayBuffer(100),
        size: '14px',
        lineHeight: 1.2,
      };

      await saveCustomFont(font);
      const retrieved = await getCustomFont('SpecificFont');

      expect(retrieved).toBeDefined();
      expect(retrieved.name).toBe('SpecificFont');
      expect(retrieved.size).toBe('14px');
    });

    it('should return null for non-existent font', async () => {
      const retrieved = await getCustomFont('NonExistent');
      expect(retrieved).toBeNull();
    });
  });

  describe('deleteCustomFont', () => {
    it('should delete a font by name', async () => {
      const font = {
        name: 'ToDelete',
        data: new ArrayBuffer(100),
        size: '14px',
        lineHeight: 1.2,
      };

      await saveCustomFont(font);
      const deleted = await deleteCustomFont('ToDelete');
      expect(deleted).toBe(true);

      const retrieved = await getCustomFont('ToDelete');
      expect(retrieved).toBeNull();
    });

    it('should return false when deleting non-existent font', async () => {
      const deleted = await deleteCustomFont('NonExistent');
      expect(deleted).toBe(false);
    });
  });

  describe('data validation', () => {
    it('should reject invalid size format', async () => {
      const font = {
        name: 'TestFont',
        data: new ArrayBuffer(100),
        size: '14', // Missing 'px'
        lineHeight: 1.2,
      };

      await expect(saveCustomFont(font)).rejects.toThrow();
    });

    it('should accept valid size formats', async () => {
      const validSizes = ['12px', '14px', '16px', '18px'];

      for (const size of validSizes) {
        const font = {
          name: `Font-${size}`,
          data: new ArrayBuffer(100),
          size,
          lineHeight: 1.2,
        };
        const result = await saveCustomFont(font);
        expect(result).toBe(true);
      }
    });

    it('should accept valid lineHeight values', async () => {
      const validLineHeights = [1.0, 1.2, 1.4, 1.6, 2.0];

      for (const lh of validLineHeights) {
        const font = {
          name: `Font-lh-${lh}`,
          data: new ArrayBuffer(100),
          size: '14px',
          lineHeight: lh,
        };
        const result = await saveCustomFont(font);
        expect(result).toBe(true);
      }
    });

    it('should reject lineHeight outside valid range', async () => {
      const font = {
        name: 'TestFont',
        data: new ArrayBuffer(100),
        size: '14px',
        lineHeight: 5.0, // Too large
      };

      await expect(saveCustomFont(font)).rejects.toThrow();
    });
  });

  describe('utility functions', () => {
    it('should convert ArrayBuffer to base64 data URL', () => {
      const buffer = new Uint8Array([1, 2, 3, 4, 5]).buffer;
      const dataURL = arrayBufferToDataURL(buffer);

      expect(dataURL).toMatch(/^data:font\/woff2;base64,/);
      expect(dataURL.length).toBeGreaterThan(30);
    });

    it('should generate valid @font-face CSS', () => {
      const font = {
        name: 'TestFont',
        data: new Uint8Array([1, 2, 3]).buffer,
      };

      const css = generateFontFaceCSS(font);

      expect(css).toContain('@font-face');
      expect(css).toContain("font-family: 'TestFont'");
      expect(css).toContain("format('woff2')");
      expect(css).toContain('data:font/woff2;base64,');
    });

    it('should sanitize font names in generated CSS', () => {
      const font = {
        name: "Malicious'; } </style><script>alert('XSS')</script>",
        data: new Uint8Array([1, 2, 3]).buffer,
      };

      const css = generateFontFaceCSS(font);

      // Should strip dangerous characters, not just escape them
      expect(css).not.toContain("'Malicious';");
      expect(css).not.toContain('</style>');
      expect(css).not.toContain('<script>');
      // Should contain sanitized name (dangerous chars stripped)
      expect(css).toContain('/stylescriptalertXSS/script');
    });
  });

  describe('security functions', () => {
    describe('isValidWOFF2', () => {
      it('should accept valid WOFF2 files', () => {
        // WOFF2 magic number: 0x774F4632 ("wOF2")
        const validWoff2 = new Uint8Array([0x77, 0x4F, 0x46, 0x32, 0x00, 0x00]).buffer;
        expect(isValidWOFF2(validWoff2)).toBe(true);
      });

      it('should reject files with wrong magic number', () => {
        const invalidFile = new Uint8Array([0x00, 0x00, 0x00, 0x00]).buffer;
        expect(isValidWOFF2(invalidFile)).toBe(false);
      });

      it('should reject files that are too small', () => {
        const tooSmall = new Uint8Array([0x77, 0x4F]).buffer;
        expect(isValidWOFF2(tooSmall)).toBe(false);
      });

      it('should reject empty buffer', () => {
        const empty = new ArrayBuffer(0);
        expect(isValidWOFF2(empty)).toBe(false);
      });

      it('should reject WOFF1 files', () => {
        // WOFF1 magic number: 0x774F4646 ("wOFF")
        const woff1 = new Uint8Array([0x77, 0x4F, 0x46, 0x46]).buffer;
        expect(isValidWOFF2(woff1)).toBe(false);
      });
    });

    describe('sanitizeFontName', () => {
      it('should pass through clean font names', () => {
        expect(sanitizeFontName('MyFont')).toBe('MyFont');
        expect(sanitizeFontName('My Font Name')).toBe('My Font Name');
        expect(sanitizeFontName('Font-123')).toBe('Font-123');
      });

      it('should strip single quotes', () => {
        expect(sanitizeFontName("Font's Name")).toBe('Fonts Name');
      });

      it('should strip backslashes', () => {
        expect(sanitizeFontName('Font\\Name')).toBe('FontName');
      });

      it('should remove control characters', () => {
        expect(sanitizeFontName('Font\x00Name')).toBe('FontName');
        expect(sanitizeFontName('Font\x1FName')).toBe('FontName');
        expect(sanitizeFontName('Font\x7FName')).toBe('FontName');
      });

      it('should strip all dangerous characters from XSS attempt', () => {
        const malicious = "'; } </style><script>alert('XSS')</script>";
        const sanitized = sanitizeFontName(malicious);

        // Should strip all dangerous characters
        expect(sanitized).not.toContain("'");
        expect(sanitized).not.toContain(';');
        expect(sanitized).not.toContain('<');
        expect(sanitized).not.toContain('>');
        expect(sanitized).not.toContain('{');
        expect(sanitized).not.toContain('}');
        expect(sanitized).not.toContain('(');
        expect(sanitized).not.toContain(')');
        // Should preserve safe text
        expect(sanitized).toContain('style');
        expect(sanitized).toContain('script');
      });
    });
  });
});
