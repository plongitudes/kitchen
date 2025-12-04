/**
 * System 7 UI Font Configuration
 * 
 * Defines available pixel fonts for the UI with their optimal rendering settings.
 */

export const AVAILABLE_FONTS = {
  silkscreen: {
    name: 'Silkscreen',
    family: "'Silkscreen', 'Courier New', Monaco, monospace",
    googleFonts: 'family=Silkscreen:wght@400;700',
    size: '13px',
    lineHeight: '1.4',
    description: 'Clean, readable pixel font',
    sizeRange: { min: 10, max: 20, default: 13 },
    lineHeightRange: { min: 1.0, max: 2.0, default: 1.4 },
  },
  pixelifySans: {
    name: 'Pixelify Sans',
    family: "'Pixelify Sans', monospace",
    googleFonts: 'family=Pixelify+Sans:wght@400;700',
    size: '14px',
    lineHeight: '1.3',
    description: 'Modern pixel font with variable weight',
    sizeRange: { min: 10, max: 20, default: 14 },
    lineHeightRange: { min: 1.0, max: 2.0, default: 1.3 },
  },
  jersey10: {
    name: 'Jersey 10',
    family: "'Jersey 10', monospace",
    googleFonts: 'family=Jersey+10',
    size: '16px',
    lineHeight: '1.2',
    description: 'Sporty pixel font',
    sizeRange: { min: 12, max: 24, default: 16 },
    lineHeightRange: { min: 1.0, max: 2.0, default: 1.2 },
  },
  tiny5: {
    name: 'Tiny5',
    family: "'Tiny5', monospace",
    googleFonts: 'family=Tiny5',
    size: '16px',
    lineHeight: '1.3',
    description: 'Ultra-compact 5px pixel font',
    sizeRange: { min: 12, max: 24, default: 16 },
    lineHeightRange: { min: 1.0, max: 2.0, default: 1.3 },
  },
  vt323: {
    name: 'VT323',
    family: "'VT323', monospace",
    googleFonts: 'family=VT323',
    size: '18px',
    lineHeight: '1.3',
    description: 'Terminal/VT220 style monospace font',
    sizeRange: { min: 14, max: 28, default: 18 },
    lineHeightRange: { min: 1.0, max: 2.0, default: 1.3 },
  },
  pressStart2p: {
    name: 'Press Start 2P',
    family: "'Press Start 2P', monospace",
    googleFonts: 'family=Press+Start+2P',
    size: '16px',
    lineHeight: '1.5',
    description: '8-bit gaming font from 1980s arcades',
    sizeRange: { min: 8, max: 20, default: 16 },
    lineHeightRange: { min: 1.0, max: 2.0, default: 1.5 },
  },
};

export const DEFAULT_FONT = 'silkscreen';
