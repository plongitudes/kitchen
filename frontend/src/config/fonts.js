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
  },
  pixelifySans: {
    name: 'Pixelify Sans',
    family: "'Pixelify Sans', monospace",
    googleFonts: 'family=Pixelify+Sans:wght@400;700',
    size: '14px',
    lineHeight: '1.3',
    description: 'Modern pixel font with variable weight',
  },
  jersey10: {
    name: 'Jersey 10',
    family: "'Jersey 10', monospace",
    googleFonts: 'family=Jersey+10',
    size: '16px',
    lineHeight: '1.2',
    description: 'Sporty pixel font',
  },
  tiny5: {
    name: 'Tiny5',
    family: "'Tiny5', monospace",
    googleFonts: 'family=Tiny5',
    size: '16px',
    lineHeight: '1.3',
    description: 'Ultra-compact 5px pixel font',
  },
  micro5: {
    name: 'Micro 5',
    family: "'Micro 5', monospace",
    googleFonts: 'family=Micro+5',
    size: '16px',
    lineHeight: '1.3',
    description: 'Micro-sized pixel font',
  },
};

export const DEFAULT_FONT = 'silkscreen';
