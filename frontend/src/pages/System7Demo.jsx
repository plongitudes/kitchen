import { ThemeProvider } from 'styled-components';
import { Window, Button } from '../components/System7';

/**
 * System 7 Component Demo Page
 * 
 * Use this page to test System 7 components as SVG assets are created.
 * Components will use fallback styling until SVG assets are in place.
 */

const system7Theme = {
  fontFamily: 'Chicago, Monaco, monospace',
};

function System7Demo() {
  return (
    <ThemeProvider theme={system7Theme}>
      <div style={{ 
        padding: '40px',
        background: '#DDDDDD',
        minHeight: '100vh'
      }}>
        <h1 style={{ marginBottom: '20px', fontFamily: 'Chicago, monospace' }}>
          System 7 UI Component Testing
        </h1>
        
        <p style={{ marginBottom: '20px', maxWidth: '600px' }}>
          This page demonstrates System 7 components. Currently using fallback CSS styling.
          As you create SVG assets, uncomment the border-image CSS in the component files
          to see the pixel-perfect appearance.
        </p>
        
        {/* Window Component Test */}
        <Window 
          title="Test Window"
          active={true}
          style={{ 
            width: '400px',
            marginBottom: '20px'
          }}
        >
          <p style={{ marginBottom: '12px' }}>
            This is a System 7 window. The title bar should have horizontal stripes
            (black and white when active, gray when inactive).
          </p>
          
          <p style={{ marginBottom: '16px' }}>
            The window border should be a simple 1px black line with a drop shadow
            on the bottom and right edges.
          </p>
          
          {/* Button Tests */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <Button primary>OK</Button>
            <Button>Cancel</Button>
            <Button disabled>Disabled</Button>
          </div>
          
          <p style={{ fontSize: '11px', color: '#666' }}>
            Note: Primary button (OK) has 3px border, regular buttons have 1px border.
            All buttons should have rounded corners (~4px radius in pixel steps).
          </p>
        </Window>
        
        {/* Inactive Window Test */}
        <Window 
          title="Inactive Window"
          active={false}
          closable={false}
          style={{ width: '300px' }}
        >
          <p>
            This window is inactive. The title bar should show gray stripes
            instead of black/white stripes.
          </p>
        </Window>
        
        {/* Asset Status */}
        <div style={{ 
          marginTop: '40px',
          padding: '20px',
          background: 'white',
          border: '1px solid #000',
          maxWidth: '600px'
        }}>
          <h2 style={{ marginBottom: '12px' }}>Asset Creation Progress</h2>
          <p style={{ marginBottom: '12px' }}>
            Check <code>/public/assets/system7/</code> directories for PLACEHOLDER.md files.
            These list all required SVG assets for each component.
          </p>
          <p style={{ marginBottom: '12px' }}>
            <strong>Priority 1:</strong> Window border (9-slice), title bars, close box, buttons
          </p>
          <p style={{ marginBottom: '12px' }}>
            <strong>Priority 2:</strong> Form controls (checkbox, radio, input)
          </p>
          <p>
            <strong>Priority 3:</strong> Scrollbar, menu, dropdown, progress bar
          </p>
        </div>
      </div>
    </ThemeProvider>
  );
}

export default System7Demo;
