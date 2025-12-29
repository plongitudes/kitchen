import { createContext, useContext, useState, useEffect } from 'react';
import { AVAILABLE_FONTS, DEFAULT_FONT } from '../config/fonts';
import { getCustomFonts, generateFontFaceCSS } from '../utils/fontStorage';
import { getCustomFontKey } from '../utils/fontUtils';

const ThemeContext = createContext(null);

// eslint-disable-next-line react-refresh/only-export-components
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved ? saved === 'dark' : true; // Default to dark
  });

  const [currentFont, setCurrentFont] = useState(() => {
    const saved = localStorage.getItem('uiFont');
    return saved && AVAILABLE_FONTS[saved] ? saved : DEFAULT_FONT;
  });

  const [fontSizeOverrides, setFontSizeOverrides] = useState(() => {
    const saved = localStorage.getItem('fontSizeOverrides');
    return saved ? JSON.parse(saved) : {};
  });

  const [allFonts, setAllFonts] = useState(AVAILABLE_FONTS);
  const [fontLoadError, setFontLoadError] = useState(null);

  // Load custom fonts from IndexedDB
  useEffect(() => {
    const loadCustomFonts = async () => {
      try {
        const fonts = await getCustomFonts();
        const customFontsMap = {};

        fonts.forEach((font) => {
          const fontKey = getCustomFontKey(font.name);
          customFontsMap[fontKey] = {
            name: font.name,
            description: 'Custom uploaded font',
            family: font.name,
            size: font.size,
            lineHeight: font.lineHeight,
            isCustom: true,
            fontData: font.data,
          };
        });

        setAllFonts({ ...AVAILABLE_FONTS, ...customFontsMap });
        setFontLoadError(null); // Clear any previous errors
      } catch (err) {
        console.error('Failed to load custom fonts:', err);
        
        // Set user-friendly error message
        if (err.message?.includes('IndexedDB is not available')) {
          setFontLoadError('Custom fonts are not available in this browser. Google Fonts will still work.');
        } else {
          setFontLoadError('Failed to load custom fonts. They may not display correctly.');
        }
        
        // Fall back to Google Fonts only
        setAllFonts(AVAILABLE_FONTS);
      }
    };

    loadCustomFonts();
  }, []);

  // Apply theme (dark/light)
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      document.body.classList.remove('light');
    } else {
      document.documentElement.classList.remove('dark');
      document.body.classList.add('light');
    }
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  // Apply font settings
  useEffect(() => {
    const font = allFonts[currentFont];
    if (!font) return;

    // Clean up previous font loaders
    const existingLink = document.querySelector('link[data-font-loader]');
    if (existingLink) {
      existingLink.remove();
    }
    const existingStyle = document.querySelector('style[data-custom-font]');
    if (existingStyle) {
      existingStyle.remove();
    }

    if (font.isCustom) {
      // Inject @font-face CSS for custom font
      const style = document.createElement('style');
      style.setAttribute('data-custom-font', 'true');
      style.textContent = generateFontFaceCSS(font);
      document.head.appendChild(style);
    } else {
      // Load Google Font dynamically
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = `https://fonts.googleapis.com/css2?${font.googleFonts}&display=swap`;
      link.setAttribute('data-font-loader', 'true');
      document.head.appendChild(link);
    }

    // Get size/lineHeight overrides or use defaults
    const override = fontSizeOverrides[currentFont];
    const finalSize = override?.size || font.size;
    const finalLineHeight = override?.lineHeight || font.lineHeight;

    // Apply font CSS variables
    document.documentElement.style.setProperty('--font-ui', font.family);
    document.documentElement.style.setProperty('--font-size', finalSize);
    document.documentElement.style.setProperty('--line-height', finalLineHeight);

    localStorage.setItem('uiFont', currentFont);
  }, [currentFont, allFonts, fontSizeOverrides]);

  const toggleTheme = () => {
    setIsDark((prev) => !prev);
  };

  const setFont = (fontKey) => {
    if (allFonts[fontKey]) {
      setCurrentFont(fontKey);
    }
  };

  const setFontSizeOverride = (fontKey, size, lineHeight) => {
    const newOverrides = {
      ...fontSizeOverrides,
      [fontKey]: {
        size: typeof size === 'number' ? `${size}px` : size,
        lineHeight: typeof lineHeight === 'number' ? lineHeight.toString() : lineHeight,
      },
    };
    setFontSizeOverrides(newOverrides);
    localStorage.setItem('fontSizeOverrides', JSON.stringify(newOverrides));
  };

  const resetFontSizeOverride = (fontKey) => {
    const newOverrides = { ...fontSizeOverrides };
    delete newOverrides[fontKey];
    setFontSizeOverrides(newOverrides);
    localStorage.setItem('fontSizeOverrides', JSON.stringify(newOverrides));
  };

  const getCurrentFontSettings = () => {
    const font = allFonts[currentFont];
    if (!font) return null;

    const override = fontSizeOverrides[currentFont];
    return {
      ...font,
      currentSize: override?.size || font.size,
      currentLineHeight: override?.lineHeight || font.lineHeight,
      hasOverride: !!override,
    };
  };

  // Function to reload custom fonts (called after upload/delete)
  const reloadCustomFonts = async () => {
    try {
      const fonts = await getCustomFonts();
      const customFontsMap = {};

      fonts.forEach((font) => {
        const fontKey = getCustomFontKey(font.name);
        customFontsMap[fontKey] = {
          name: font.name,
          description: 'Custom uploaded font',
          family: font.name,
          size: font.size,
          lineHeight: font.lineHeight,
          isCustom: true,
          fontData: font.data,
        };
      });

      setAllFonts({ ...AVAILABLE_FONTS, ...customFontsMap });

      // If current font was deleted, switch to default
      if (!AVAILABLE_FONTS[currentFont] && !customFontsMap[currentFont]) {
        setCurrentFont(DEFAULT_FONT);
      }
    } catch (err) {
      console.error('Failed to reload custom fonts:', err);
    }
  };

  return (
    <ThemeContext.Provider
      value={{
        isDark,
        toggleTheme,
        currentFont,
        setFont,
        availableFonts: allFonts,
        reloadCustomFonts,
        setFontSizeOverride,
        resetFontSizeOverride,
        getCurrentFontSettings,
        fontLoadError,
        clearFontLoadError: () => setFontLoadError(null),
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};
