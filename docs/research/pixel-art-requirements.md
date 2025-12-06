PART 1: Asset Specification for System 7 UI
Based on authentic System 7 (analyzing classic screenshots), here's your complete pixel art shopping list:
Window Components
1. Window Border (9-slice)
Dimensions: 16×16px total grid
Corner size: 2×2px (fixed)
Edge size: Variable width/height
Create 9 separate images:
- corner-tl.svg (2×2px) - top-left black corner
- edge-top.svg (1×2px) - repeats horizontally
- corner-tr.svg (2×2px) - top-right black corner  
- edge-left.svg (2×1px) - repeats vertically
- center.svg (1×1px) - transparent or window bg color
- edge-right.svg (2×1px) - repeats vertically
- corner-bl.svg (2×2px) - bottom-left + shadow start
- edge-bottom.svg (1×2px) - repeats horizontally + shadow
- corner-br.svg (2×2px) - bottom-right + shadow corner
Colors: #000000 (border), rgba(0,0,0,0.3) (shadow)
2. Title Bar - Active
Dimensions: Variable width × 19px height
Pattern: Horizontal stripes (repeating)
- titlebar-active.svg (2×19px)
  - Row 1 (1px): Black (#000000)
  - Row 2 (1px): White (#FFFFFF)
  - Repeat for full 19px height
Background: Create seamless 2px-wide pattern
3. Title Bar - Inactive  
Dimensions: Variable width × 19px height
Pattern: Gray stripes
- titlebar-inactive.svg (2×19px)
  - Row 1 (1px): Dark gray (#888888)
  - Row 2 (1px): Light gray (#DDDDDD)
  - Repeat for full 19px height
4. Close Box (Title Bar Button)
Dimensions: 13×13px
States needed:
- closebox-normal.svg: Small centered square with black border
- closebox-hover.svg: Inverted (black bg, white square)
- closebox-pressed.svg: Inverted
Colors: #000000, #FFFFFF
---
Buttons
5. Default/Primary Button (9-slice rounded)
Dimensions: Variable, minimum 20px height
States needed:
button-default-{state}-{slice}.svg where:
- state: normal, hover, pressed, disabled
- slice: tl, t, tr, l, c, r, bl, b, br
Normal state:
- Border: 3px thick black (#000000)
- Background: White (#FFFFFF)
- Rounded corners: 4px radius (approximate with pixels)
Pressed state:
- Border: 3px thick black
- Background: Black (#000000) - inverted!
Disabled state:
- Border: 3px thick gray (#888888)
- Background: Light gray (#DDDDDD)
Corner size: 6×6px
Edge size: 1px wide/tall (repeatable)
Center: Variable
6. Regular Button (9-slice rounded)
Same as Default but:
- Border: 1px thick instead of 3px
- Corner size: 4×4px
---
Form Controls
7. Checkbox
Dimensions: 12×12px
States needed:
- checkbox-unchecked.svg: White square, 1px black border
- checkbox-checked.svg: White square, 1px black border, black X inside
- checkbox-unchecked-disabled.svg: Light gray (#DDDDDD), gray border
- checkbox-checked-disabled.svg: Light gray, gray border, gray X
Colors: #000000, #FFFFFF, #888888, #DDDDDD
8. Radio Button
Dimensions: 12×12px (circular approximation in pixels)
States needed:
- radio-unselected.svg: White circle (pixel-approximated), black border
- radio-selected.svg: White circle, black border, black dot inside
- radio-unselected-disabled.svg: Gray circle
- radio-selected-disabled.svg: Gray circle with gray dot
Pixel circle pattern (12×12):
  ##    (row 1-2: 2px at positions 5-6)
 ####   (row 3-4: 4px at positions 4-7)
 ####   (row 5-8: 4px at positions 3-8)
 ####   (row 9-10: 4px at positions 4-7)
  ##    (row 11-12: 2px at positions 5-6)
9. Text Input (9-slice)
Dimensions: Variable width × 20px height (minimum)
States needed:
input-{state}-{slice}.svg where:
- state: normal, focused, disabled
- slice: tl, t, tr, l, c, r, bl, b, br
Normal:
- Border: 1px black
- Background: White (#FFFFFF)
- Inset shadow: Top-left corner has 1px dark gray (#888888)
Focused:
- Same but thicker border (2px) or highlight
Corner size: 2×2px
Square corners (no rounding)
---
Scrollbar
10. Scrollbar Track
Dimensions: 16px wide × variable height
- scrollbar-track-vertical.svg (16×1px, repeats)
- scrollbar-track-horizontal.svg (1×16px, repeats)
Pattern: Textured gray (#DDDDDD)
Border: 1px black on edges
11. Scrollbar Thumb
Dimensions: 16×16px minimum (variable length)
States needed:
- scrollbar-thumb-{direction}-{slice}.svg
  - direction: vertical, horizontal
  - slice: top, middle, bottom (or left, middle, right)
Normal:
- White background (#FFFFFF)
- 1px black border
- Optional: Gripper dots in center
Corner size: 16×16px for ends
Middle: 16×1px (repeatable)
12. Scrollbar Arrows
Dimensions: 16×16px each
Arrows needed:
- scrollbar-arrow-up-{state}.svg (states: normal, pressed)
- scrollbar-arrow-down-{state}.svg
- scrollbar-arrow-left-{state}.svg
- scrollbar-arrow-right-{state}.svg
Design:
- Gray background (#DDDDDD)
- 1px black border
- Black triangle pointing in direction (3-5px triangle)
- Pressed state: Inverted (black bg, white triangle)
---
Menu Components
13. Menu Bar Background
Dimensions: Variable width × 20px height
- menubar-bg.svg (1×20px, repeats horizontally)
Solid light gray (#EEEEEE)
Bottom border: 1px black
14. Menu Item (Dropdown)
Dimensions: Variable width × 18px height
States needed:
- menuitem-normal.svg: Transparent/white background
- menuitem-hover.svg: Black background (#000000)
Text color changes via CSS, not in SVG
15. Menu Separator
Dimensions: Variable width × 1px height
- separator.svg (1×1px, stretches)
Color: Medium gray (#888888)
---
Dropdown / Combobox
16. Dropdown Button
Dimensions: 20×20px
States needed:
- dropdown-button-{state}.svg (normal, pressed)
Design:
- Gray background (#DDDDDD)
- 1px black border
- Downward triangle (5×3px centered)
- Pressed: Inverted
---
Progress Bar
17. Progress Track
Dimensions: Variable width × 12px height
- progress-track.svg (9-slice or simple stretch)
Border: 1px black
Background: White with inset shadow
18. Progress Fill
Dimensions: Variable width × 10px height (fits inside track)
- progress-fill.svg (1×10px, repeats)
Pattern: Diagonal stripes (barber pole style)
Colors: Black and white alternating 45° diagonal
---
Icons (Optional, for completeness)
19. System Icons
Dimensions: 32×32px each (standard System 7 icon size)
Commonly needed:
- folder.svg: Classic manila folder
- document.svg: White page with corner fold
- application.svg: Diamond/gem shape
- trash-empty.svg: Wire trash can
- trash-full.svg: Wire trash can with paper
These are nice-to-have for authentic feel
---
Color Palette Reference
:root {
  /* System 7 Grayscale */
  --s7-black: #000000;
  --s7-white: #FFFFFF;
  --s7-gray: #DDDDDD;        /* Window chrome, buttons */
  --s7-dark-gray: #888888;    /* Shadows, disabled text */
  --s7-light-gray: #F0F0F0;   /* Backgrounds, hover states */
  --s7-menu-gray: #EEEEEE;    /* Menu bar */
  
  /* Accent (rare usage) */
  --s7-blue: #0000FF;         /* Selected text background */
  --s7-highlight: #000080;    /* Dark blue for selections */
}
---
File Organization
Suggest this structure:
frontend/public/assets/system7/
├── window/
│   ├── border-tl.svg
│   ├── border-t.svg
│   ├── border-tr.svg
│   └── ... (9 total)
│   ├── titlebar-active.svg
│   ├── titlebar-inactive.svg
│   └── closebox-{state}.svg
├── button/
│   ├── default-{state}-{slice}.svg (36 files total)
│   └── regular-{state}-{slice}.svg (36 files total)
├── form/
│   ├── checkbox-{state}.svg (4 files)
│   ├── radio-{state}.svg (4 files)
│   └── input-{state}-{slice}.svg (27 files)
├── scrollbar/
│   ├── track-{direction}.svg
│   ├── thumb-{direction}-{slice}.svg
│   └── arrow-{direction}-{state}.svg
├── menu/
│   ├── menubar-bg.svg
│   ├── menuitem-{state}.svg
│   └── separator.svg
├── dropdown/
│   └── button-{state}.svg
└── progress/
    ├── track.svg
    └── fill.svg
---
Priority Order (Start Here)
Phase 1 - Minimum Viable:
1. Window border (9-slice)
2. Title bar active/inactive
3. Regular button (all 4 states, 9-slice)
4. Default button (all 4 states, 9-slice)
Phase 2 - Forms:
5. Checkbox (4 states)
6. Radio button (4 states)
7. Text input (3 states, 9-slice)
Phase 3 - Chrome:
8. Scrollbar (all components)
9. Menu components
10. Dropdown
Phase 4 - Polish:
11. Progress bar
12. Icons (if desired)
