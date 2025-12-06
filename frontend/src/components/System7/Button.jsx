import styled from 'styled-components';
import './System7.css';

/**
 * System 7 Button Component
 * 
 * Uses 9-slice SVG assets for borders with rounded corners.
 * Primary buttons have thicker borders (3px vs 1px).
 */

const StyledButton = styled.button`
  position: relative;
  font-family: ${props => props.theme.fontFamily || 'Chicago, monospace'};
  font-size: var(--s7-font-size-base);
  padding: var(--s7-spacing-xs) var(--s7-spacing-md);
  min-height: var(--s7-button-height);
  cursor: pointer;
  user-select: none;
  
  /* Fallback styling until SVG assets are created */
  border: ${props => props.$primary 
    ? 'var(--s7-border-thick)' 
    : 'var(--s7-border-thin)'} solid var(--s7-black);
  border-radius: calc(4 * var(--s7-pixel));
  background: var(--s7-button-bg);
  color: var(--s7-button-text);
  
  /* TODO: Replace with 9-slice border-image once SVGs are ready */
  /* border-image: url('/assets/system7/button/${props => props.$primary ? 'default' : 'regular'}-normal.svg') 6 fill / 6px stretch; */
  
  &:hover:not(:disabled) {
    background: var(--s7-button-bg-hover);
    /* border-image: url('/assets/system7/button/...hover.svg') ... */
  }
  
  &:active:not(:disabled) {
    background: var(--s7-button-bg-pressed);
    color: var(--s7-button-text-pressed);
    /* border-image: url('/assets/system7/button/...pressed.svg') ... */
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    /* border-image: url('/assets/system7/button/...disabled.svg') ... */
  }
  
  &:focus-visible {
    outline: var(--s7-border-thin) dotted var(--s7-black);
    outline-offset: calc(2 * var(--s7-pixel));
  }
`;

export function Button({ 
  primary = false, 
  disabled = false,
  onClick,
  children,
  ...props 
}) {
  return (
    <StyledButton
      className="s7-component s7-button"
      $primary={primary}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </StyledButton>
  );
}

export default Button;
