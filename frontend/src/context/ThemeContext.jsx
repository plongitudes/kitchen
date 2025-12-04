import { createContext, useContext, useState, useEffect } from 'react';
import { AVAILABLE_FONTS, DEFAULT_FONT } from '../config/fonts';

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
    const font = AVAILABLE_FONTS[currentFont];
    if (!font) return;

    // Load Google Font dynamically
    const existingLink = document.querySelector('link[data-font-loader]');
    if (existingLink) {
      existingLink.remove();
    }

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = `https://fonts.googleapis.com/css2?${font.googleFonts}&display=swap`;
    link.setAttribute('data-font-loader', 'true');
    document.head.appendChild(link);

    // Apply font CSS variables
    document.documentElement.style.setProperty('--font-ui', font.family);
    document.documentElement.style.setProperty('--font-size', font.size);
    document.documentElement.style.setProperty('--line-height', font.lineHeight);

    localStorage.setItem('uiFont', currentFont);
  }, [currentFont]);

  const toggleTheme = () => {
    setIsDark((prev) => !prev);
  };

  const setFont = (fontKey) => {
    if (AVAILABLE_FONTS[fontKey]) {
      setCurrentFont(fontKey);
    }
  };

  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme, currentFont, setFont, availableFonts: AVAILABLE_FONTS }}>
      {children}
    </ThemeContext.Provider>
  );
};
