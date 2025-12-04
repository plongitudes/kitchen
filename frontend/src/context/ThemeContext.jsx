import { createContext, useContext, useState, useEffect } from 'react';
import { AVAILABLE_FONTS, DEFAULT_FONT } from '../config/fonts';
import { getCustomFonts, generateFontFaceCSS } from '../utils/fontStorage';

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

  const [allFonts, setAllFonts] = useState(AVAILABLE_FONTS);

  // Load custom fonts from IndexedDB
  useEffect(() => {
    const loadCustomFonts = async () => {
      try {
        const fonts = await getCustomFonts();
        const customFontsMap = {};

        fonts.forEach((font) => {
          const fontKey = `custom-${font.name.toLowerCase().replace(/\s+/g, '-')}`;
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
      } catch (err) {
        console.error('Failed to load custom fonts:', err);
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

    // Apply font CSS variables
    document.documentElement.style.setProperty('--font-ui', font.family);
    document.documentElement.style.setProperty('--font-size', font.size);
    document.documentElement.style.setProperty('--line-height', font.lineHeight);

    localStorage.setItem('uiFont', currentFont);
  }, [currentFont, allFonts]);

  const toggleTheme = () => {
    setIsDark((prev) => !prev);
  };

  const setFont = (fontKey) => {
    if (allFonts[fontKey]) {
      setCurrentFont(fontKey);
    }
  };

  // Function to reload custom fonts (called after upload/delete)
  const reloadCustomFonts = async () => {
    try {
      const fonts = await getCustomFonts();
      const customFontsMap = {};

      fonts.forEach((font) => {
        const fontKey = `custom-${font.name.toLowerCase().replace(/\s+/g, '-')}`;
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
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};
