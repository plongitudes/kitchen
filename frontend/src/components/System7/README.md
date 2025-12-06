# System 7 UI Components

React components styled to match authentic Mac OS System 7 appearance using pixel-perfect SVG assets.

## Architecture

Each component uses:
1. **SVG assets** from `/public/assets/system7/` for visual appearance
2. **styled-components** for layout and interactivity
3. **CSS custom properties** for theming and viewport scaling

## Components

### Window Components
- `Window` - Main window container with 9-slice border
- `WindowHeader` - Title bar with horizontal stripe pattern
- `WindowContent` - Window content area

### Form Controls
- `Button` - Standard and default/primary buttons
- `Checkbox` - Checkbox with checked/unchecked states
- `Radio` - Radio button with selected/unselected states
- `TextInput` - Text input field with focus states

### Navigation
- `MenuBar` - Application menu bar
- `MenuItem` - Individual menu item with hover state
- `Dropdown` - Dropdown/combobox selector

### Utilities
- `Scrollbar` - Vertical and horizontal scrollbars
- `ProgressBar` - Progress indicator with barber pole fill

## Usage Example

```jsx
import { Window, WindowHeader, WindowContent, Button } from '@/components/System7';

function MyApp() {
  return (
    <Window>
      <WindowHeader active>My Application</WindowHeader>
      <WindowContent>
        <p>Hello, System 7!</p>
        <Button primary>OK</Button>
        <Button>Cancel</Button>
      </WindowContent>
    </Window>
  );
}
```

## Scaling Strategy

Components use viewport-relative sizing to scale appropriately:

```css
:root {
  /* 1 "mac pixel" scales with viewport width */
  --s7-pixel: max(1px, 0.2vw);
  
  /* All measurements in mac pixels */
  --s7-border: calc(1 * var(--s7-pixel));
  --s7-border-thick: calc(3 * var(--s7-pixel));
}
```

This ensures UI remains readable on modern high-DPI displays while maintaining authentic pixel art aesthetic.

## Development Guidelines

1. **Always use SVG assets** - No CSS-generated borders or patterns
2. **Use image-rendering: pixelated** - Prevents blurry scaling
3. **Follow 9-slice pattern** - For components that resize
4. **Test at multiple viewport sizes** - Ensure scaling works correctly
5. **Maintain grayscale palette** - Stay true to System 7 aesthetic

## Asset Creation

See `/docs/research/pixel-art-requirements.md` for complete specifications on creating new System 7 assets.
