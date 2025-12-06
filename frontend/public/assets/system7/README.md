# System 7 UI Assets

This directory contains pixel-perfect SVG assets for the System 7 UI components.

## Directory Structure

```
system7/
├── window/          # Window borders, title bars, close box
├── button/          # Default and regular buttons (9-slice)
├── form/            # Checkboxes, radio buttons, text inputs
├── scrollbar/       # Scrollbar tracks, thumbs, arrows
├── menu/            # Menu bars, menu items, separators
├── dropdown/        # Dropdown/combobox buttons
└── progress/        # Progress bar tracks and fills
```

## Asset Naming Convention

All assets follow this pattern:
`{component}-{variant}-{state}-{slice}.svg`

Examples:
- `button-default-normal-tl.svg` - Default button, normal state, top-left corner
- `window-border-tr.svg` - Window border top-right corner
- `checkbox-checked.svg` - Checked checkbox
- `titlebar-active.svg` - Active window title bar pattern

## 9-Slice Components

Components that use 9-slice scaling have 9 separate files:
- `{name}-{state}-tl.svg` - Top-left corner
- `{name}-{state}-t.svg` - Top edge (repeats horizontally)
- `{name}-{state}-tr.svg` - Top-right corner
- `{name}-{state}-l.svg` - Left edge (repeats vertically)
- `{name}-{state}-c.svg` - Center (repeats both directions)
- `{name}-{state}-r.svg` - Right edge (repeats vertically)
- `{name}-{state}-bl.svg` - Bottom-left corner
- `{name}-{state}-b.svg` - Bottom edge (repeats horizontally)
- `{name}-{state}-br.svg` - Bottom-right corner

## Color Palette

All assets use the authentic System 7 grayscale palette:

- `#000000` - Black (borders, text, active elements)
- `#FFFFFF` - White (backgrounds, inverted text)
- `#DDDDDD` - Light gray (window chrome, buttons)
- `#888888` - Medium gray (shadows, disabled states)
- `#F0F0F0` - Very light gray (hover states)
- `#EEEEEE` - Menu bar background

## Image Rendering

All SVG assets must be rendered with crisp edges to maintain pixel-perfect appearance:

```css
img, svg {
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  image-rendering: -moz-crisp-edges;
  image-rendering: -webkit-crisp-edges;
}
```

## Reference

See `/docs/research/pixel-art-requirements.md` for complete specifications and `/docs/research/system7-screenshots/` for authentic System 7 reference images.
