import { useState } from 'react';
import styled from 'styled-components';
import './System7.css';

/**
 * System 7 Window Component
 * 
 * Uses 9-slice SVG assets for borders and repeating pattern for title bar.
 * Will gracefully degrade if assets aren't created yet.
 */

const WindowContainer = styled.div`
  position: relative;
  background: var(--s7-window-bg);
  min-width: 200px;
  min-height: 100px;
  
  /* Fallback border until SVG assets are created */
  border: var(--s7-border-thin) solid var(--s7-window-border);
  
  /* TODO: Replace with 9-slice border-image once SVGs are ready */
  /* border-image: url('/assets/system7/window/border.svg') 2 fill / 2px stretch; */
`;

const TitleBar = styled.div`
  height: var(--s7-titlebar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--s7-spacing-sm);
  font-family: ${props => props.theme.fontFamily || 'Chicago, monospace'};
  font-size: var(--s7-font-size-base);
  font-weight: bold;
  cursor: move;
  user-select: none;
  
  /* Fallback: solid background until SVG pattern is created */
  background: ${props => props.$active 
    ? 'var(--s7-black)' 
    : 'var(--s7-gray)'};
  color: ${props => props.$active 
    ? 'var(--s7-white)' 
    : 'var(--s7-black)'};
  
  /* TODO: Replace with repeating SVG pattern once created */
  /* background-image: url('/assets/system7/window/titlebar-${props => props.$active ? 'active' : 'inactive'}.svg'); */
  /* background-repeat: repeat-x; */
`;

const CloseBox = styled.button`
  width: calc(13 * var(--s7-pixel));
  height: calc(13 * var(--s7-pixel));
  padding: 0;
  border: var(--s7-border-thin) solid var(--s7-black);
  background: var(--s7-white);
  cursor: pointer;
  flex-shrink: 0;
  
  &:hover {
    background: var(--s7-black);
  }
  
  &:active {
    background: var(--s7-dark-gray);
  }
  
  /* TODO: Replace with SVG icon once created */
  /* background-image: url('/assets/system7/window/closebox-normal.svg'); */
  /* &:hover { background-image: url('/assets/system7/window/closebox-hover.svg'); } */
  /* &:active { background-image: url('/assets/system7/window/closebox-pressed.svg'); } */
`;

const TitleText = styled.span`
  flex: 1;
  text-align: center;
  margin: 0 var(--s7-spacing-sm);
`;

const WindowContent = styled.div`
  padding: var(--s7-spacing-md);
  overflow: auto;
`;

export function Window({ 
  title = 'Untitled', 
  active = true, 
  closable = true,
  onClose,
  children,
  ...props 
}) {
  const [isActive, setIsActive] = useState(active);
  
  const handleClose = () => {
    if (onClose) {
      onClose();
    }
  };
  
  return (
    <WindowContainer 
      className="s7-component s7-window"
      onMouseDown={() => setIsActive(true)}
      {...props}
    >
      <TitleBar 
        $active={isActive}
        className="s7-titlebar"
      >
        {closable && <CloseBox onClick={handleClose} />}
        <TitleText>{title}</TitleText>
        {/* Spacer to center title when close box is present */}
        {closable && <div style={{ width: 'calc(13 * var(--s7-pixel))' }} />}
      </TitleBar>
      
      <WindowContent className="s7-window-content">
        {children}
      </WindowContent>
    </WindowContainer>
  );
}

export default Window;
