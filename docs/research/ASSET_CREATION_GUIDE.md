# System 7 Asset Creation Guide

Quick reference for creating pixel-perfect SVG assets for the System 7 UI.

## Testing Your Assets

1. **Start the dev server:**
   ```bash
   cd frontend && npm run dev
   ```

2. **Navigate to:** `http://localhost:5173/system7-demo`

3. **See your assets in action** as you create them!

## Asset Priorities

### Phase 1: MVP (Start Here!) ⭐
Create these first to see components working:

1. **Window Components**
   - `window/titlebar-active.svg` (2×19px)
   - `window/titlebar-inactive.svg` (2×19px)
   - `window/closebox-normal.svg` (13×13px)
   - `window/border-*.svg` (9 files for 9-slice border)

2. **Buttons**
   - `button/default-normal-*.svg` (9 files for primary button)
   - `button/regular-normal-*.svg` (9 files for regular button)

### Phase 2: Form Controls
- Checkbox (4 states)
- Radio button (4 states)  
- Text input (9-slice, 3 states)

### Phase 3: Everything Else
- Scrollbars
- Menus
- Dropdown
- Progress bar

## Quick Start: Title Bar

The easiest asset to start with:

### titlebar-active.svg (2×19px)
```svg
<svg width="2" height="19" xmlns="http://www.w3.org/2000/svg">
  <!-- Alternating 1px black/white horizontal stripes -->
  <rect x="0" y="0" width="2" height="1" fill="#000000"/>
  <rect x="0" y="1" width="2" height="1" fill="#FFFFFF"/>
  <rect x="0" y="2" width="2" height="1" fill="#000000"/>
  <rect x="0" y="3" width="2" height="1" fill="#FFFFFF"/>
  <!-- ... repeat to y="18" -->
</svg>
```

This 2px-wide pattern will repeat horizontally across the title bar!

## 9-Slice Example: Button Corner

For a button with 6px corners and 3px border:

### button-default-normal-tl.svg (6×6px top-left)
```svg
<svg width="6" height="6" xmlns="http://www.w3.org/2000/svg">
  <!-- White background -->
  <rect x="0" y="0" width="6" height="6" fill="#FFFFFF"/>
  
  <!-- 3px black border (top and left only for corner) -->
  <rect x="0" y="0" width="6" height="3" fill="#000000"/>
  <rect x="0" y="0" width="3" height="6" fill="#000000"/>
  
  <!-- Pixel-approximated 4px radius in the corner -->
  <!-- (adjust these to create smooth rounded appearance) -->
</svg>
```

## Using Your Assets in Code

Once you create an asset, update the component:

### Before (Fallback CSS):
```css
background: var(--s7-black);
```

### After (Your SVG):
```css
background-image: url('/assets/system7/window/titlebar-active.svg');
background-repeat: repeat-x;
image-rendering: pixelated;
```

## File Locations

Save all SVGs here:
```
frontend/public/assets/system7/
├── window/
├── button/
├── form/
├── scrollbar/
├── menu/
├── dropdown/
└── progress/
```

## Tips

1. **Keep it simple** - System 7 is deliberately minimalist
2. **Use exact hex colors** from the palette (see System7.css)
3. **Test at different viewport sizes** - Assets scale with `--s7-pixel`
4. **Save as plain SVG** - No fancy effects, gradients, or filters
5. **Check PLACEHOLDER.md files** in each directory for full specs

## Reference Screenshots

See authentic System 7 UI in:
```
docs/research/system7-screenshots/
```

Look at these for inspiration:
- `desktop.png` - Window chrome, buttons
- `file-manager.png` - Scrollbars, checkboxes
- `confirmation-modal.png` - Dialog buttons

## Full Specifications

Complete pixel-by-pixel specs for every component:
```
docs/research/pixel-art-requirements.md
```

## Questions?

Check the component source code - each has TODO comments showing where
SVG assets will be used once created!

---

**Ready to start?** Create titlebar-active.svg and titlebar-inactive.svg first,
then reload /system7-demo to see them in action! 🎨
