# Roanes Kitchen - Color Palettes & Theming

## MVP Phase (Phase 1) - Gruvbox Dark/Light + Curated Palettes

### Primary Theme: Gruvbox
Gruvbox is a retro-inspired color scheme with warm earth tones. Available in both dark and light variants.

**Gruvbox Dark:**
- Background: `#282828`
- Foreground: `#ebdbb2`
- Primary Accent: `#b8bb26` (green)
- Secondary Accent: `#d65d0e` (orange)
- Error: `#fb4934` (red)
- Success: `#b8bb26` (green)

**Gruvbox Light:**
- Background: `#fbf1c7`
- Foreground: `#3c3836`
- Primary Accent: `#9d0006` (dark red)
- Secondary Accent: `#8f3f00` (dark orange)
- Error: `#cc241d` (red)
- Success: `#79740e` (dark green)

### Supplementary Palettes (Phase 2+)

From digitalsynopsis.com color combinations:

#### 2. Embers (Dark) - Warm, Moody Dark Theme
Used for dark mode refinement and alternative dark theme option.
- Deep charcoal backgrounds with warm amber/copper accents
- Good for cozy, intimate feel

#### 4. Velvet (Dark) - Rich, Luxurious Dark Theme
Used for premium dark mode option.
- Deep purples and dark magentas with gold accents
- Alternative sophisticated dark theme

#### 17. Kiwi (Light) - Fresh, Bright Light Theme
Used for light mode refinement.
- Bright greens and citrusy yellows with white backgrounds
- Fresh, energetic feel for light mode

#### 37. Popsicle (Light) - Playful, Vibrant Light Theme
Used for playful light mode option.
- Pastel ice cream colors (pinks, blues, yellows) with light backgrounds
- Fun, approachable feel for light mode

## Implementation Strategy

### MVP (Phase 1)
- Gruvbox Dark as default dark theme
- Gruvbox Light as default light theme
- Simple toggle in settings between the two
- Used across all UI components via CSS variables or Tailwind theme config

### Phase 2
- Theme selection dropdown with options:
  - Gruvbox Dark (default)
  - Gruvbox Light (default)
  - Embers (new dark option)
  - Velvet (new dark option)
  - Kiwi (new light option)
  - Popsicle (new light option)
- Migration to centralized theme system (CSS variables or Tailwind config)

### Phase IV+
- Full TVA aesthetic with custom retro 70s/80s color palette
- Geometric patterns and angular design elements
- Retrotype typography

## Accessibility Notes

- All color combinations should meet WCAG AA contrast standards (minimum 4.5:1 for text)
- Gruvbox is designed specifically for accessibility and readability
- Test all palettes with color blindness simulations before Phase 2 launch
- Ensure non-color-dependent indicators (patterns, icons, text labels)

## Technical Implementation

Recommend storing theme configuration in:
- **Frontend:** Tailwind CSS theme config with CSS custom properties (variables)
- **Backend:** User preference in database (theme preference per user)
- **Storage:** Theme choice persisted in localStorage + user profile

Example Tailwind config structure:
```javascript
theme: {
  extend: {
    colors: {
      // Gruvbox Dark
      'gruvbox-dark': {
        'bg': '#282828',
        'fg': '#ebdbb2',
        'accent-primary': '#b8bb26',
        'accent-secondary': '#d65d0e',
      },
      // Gruvbox Light
      'gruvbox-light': {
        'bg': '#fbf1c7',
        'fg': '#3c3836',
        'accent-primary': '#9d0006',
        'accent-secondary': '#8f3f00',
      },
      // Embers, Velvet, Kiwi, Popsicle (Phase 2+)
    }
  }
}
```

## Notes for Developer

- Gruvbox palettes are well-suited to retro/vintage aesthetic and will transition well to Phase IV+ TVA design
- All chosen palettes are warm, friendly, and avoid harsh or overly neon colors
- Consider using Gruvbox as foundation for Phase IV+ theme rather than completely replacing it
- The playful nature of Popsicle and the richness of Velvet provide good contrast with the sophistication of Embers
