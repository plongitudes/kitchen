import { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useMenuBar } from '../context/MenuBarContext';

const COLOR_MAP = {
  green: {
    dark: 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg',
    light: 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg',
  },
  red: {
    dark: 'bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright',
    light: 'bg-gruvbox-light-red hover:bg-gruvbox-light-red-bright',
  },
  blue: {
    dark: 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright text-gruvbox-dark-bg',
    light: 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright text-gruvbox-light-bg',
  },
  gray: {
    dark: 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-fg-0',
    light: 'bg-gruvbox-light-gray hover:bg-gruvbox-light-fg-0',
  },
  aqua: {
    dark: 'bg-gruvbox-dark-aqua hover:bg-gruvbox-dark-aqua-bright text-gruvbox-dark-bg',
    light: 'bg-gruvbox-light-aqua hover:bg-gruvbox-light-aqua-bright text-gruvbox-light-bg',
  },
  orange: {
    dark: 'bg-gruvbox-dark-orange hover:bg-gruvbox-dark-orange-bright text-gruvbox-dark-bg',
    light: 'bg-gruvbox-light-orange hover:bg-gruvbox-light-orange-bright text-gruvbox-light-bg',
  },
  purple: {
    dark: 'bg-gruvbox-dark-purple hover:bg-gruvbox-dark-purple-bright',
    light: 'bg-gruvbox-light-purple hover:bg-gruvbox-light-purple-bright',
  },
};

const ROUTE_NAMES = {
  '/': 'Home',
  '/recipes': 'Recipes',
  '/recipes/new': 'New Recipe',
  '/schedules': 'Schedules',
  '/schedules/new': 'New Sequence',
  '/templates': 'Templates',
  '/meal-plans': 'Meal Plans',
  '/grocery-lists': 'Grocery Lists',
  '/ingredients': 'Ingredients',
  '/settings': 'Settings',
};

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/recipes', label: 'Recipes' },
  { to: '/schedules', label: 'Schedules' },
  { to: '/templates', label: 'Templates' },
  { to: '/meal-plans', label: 'Meal Plans' },
  { to: '/grocery-lists', label: 'Grocery Lists' },
  { to: '/ingredients', label: 'Ingredients' },
  { to: '/settings', label: 'Settings' },
];

const getPageName = (pathname) => {
  // Exact match first
  if (ROUTE_NAMES[pathname]) return ROUTE_NAMES[pathname];

  // Pattern matching for dynamic routes
  if (/^\/recipes\/[^/]+\/edit$/.test(pathname)) return 'Edit Recipe';
  if (/^\/recipes\/[^/]+$/.test(pathname)) return 'Recipe';
  if (/^\/schedules\/[^/]+$/.test(pathname)) return 'Schedule';
  if (/^\/templates\/[^/]+\/edit$/.test(pathname)) return 'Edit Template';
  if (/^\/templates\/[^/]+$/.test(pathname)) return 'Template';
  if (/^\/meal-plans\/current$/.test(pathname)) return 'Current Plan';
  if (/^\/meal-plans\/[^/]+$/.test(pathname)) return 'Meal Plan';
  if (/^\/grocery-lists\/[^/]+$/.test(pathname)) return 'Grocery List';

  return 'Kitchen';
};

const ActionButton = ({ action, isDark }) => {
  const colorClasses = COLOR_MAP[action.color || 'gray'];
  const themeClass = isDark ? colorClasses?.dark : colorClasses?.light;
  const baseClass = 'px-3 py-1.5 rounded text-sm font-semibold transition whitespace-nowrap';

  if (action.hidden) return null;

  if (action.variant === 'toggle') {
    return (
      <label className={`${baseClass} ${themeClass} cursor-pointer flex items-center gap-1.5`}>
        <input
          type="checkbox"
          checked={action.checked || false}
          onChange={action.onClick}
          className="rounded"
        />
        <span>{action.label}</span>
      </label>
    );
  }

  if (action.variant === 'file-input') {
    return (
      <label className={`${baseClass} ${themeClass} cursor-pointer inline-block`}>
        {action.label}
        <input
          type="file"
          accept={action.accept || '*'}
          onChange={action.onChange}
          className="hidden"
        />
      </label>
    );
  }

  if (action.variant === 'link' && action.href) {
    return (
      <a
        href={action.href}
        target="_blank"
        rel="noopener noreferrer"
        className={`${baseClass} ${themeClass} inline-block`}
      >
        {action.label}
      </a>
    );
  }

  if (action.to) {
    return (
      <Link
        to={action.to}
        className={`${baseClass} ${themeClass} inline-block`}
      >
        {action.label}
      </Link>
    );
  }

  return (
    <button
      onClick={action.onClick}
      disabled={action.disabled}
      className={`${baseClass} ${themeClass} disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      {action.label}
    </button>
  );
};

const MenuBar = () => {
  const { isDark, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const { pageActions, sectionActions } = useMenuBar();
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  const pageName = getPageName(location.pathname);

  // Close menu on route change
  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  // Close on Escape
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') setMenuOpen(false);
    };
    if (menuOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [menuOpen]);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    };
    if (menuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [menuOpen]);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMenuOpen(false);
  };

  return (
    <div
      className={`h-12 shrink-0 z-20 flex items-center px-4 border-b ${
        isDark
          ? 'bg-gruvbox-dark-bg-hard border-gruvbox-dark-gray'
          : 'bg-gruvbox-light-bg-hard border-gruvbox-light-gray'
      }`}
    >
      {/* Zone 1: App Menu */}
      <div className="relative" ref={menuRef}>
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className={`px-3 py-1.5 rounded text-sm font-bold transition flex items-center gap-1 ${
            isDark
              ? 'hover:bg-gruvbox-dark-bg-soft text-gruvbox-dark-orange-bright'
              : 'hover:bg-gruvbox-light-bg-soft text-gruvbox-light-orange-bright'
          }`}
        >
          <span>☰</span>
          <span>{pageName}</span>
          <span className="text-xs">▾</span>
        </button>

        {menuOpen && (
          <div className={`absolute top-full left-0 mt-1 w-56 rounded-lg shadow-lg border py-1 ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
              : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
          }`}>
            {NAV_LINKS.map((link) => {
              const isActive = location.pathname === link.to ||
                (link.to !== '/' && location.pathname.startsWith(link.to));
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setMenuOpen(false)}
                  className={`block px-4 py-2 text-sm transition ${
                    isActive
                      ? isDark
                        ? 'bg-gruvbox-dark-bg text-gruvbox-dark-orange-bright font-semibold'
                        : 'bg-gruvbox-light-bg text-gruvbox-light-orange-bright font-semibold'
                      : isDark
                        ? 'text-gruvbox-dark-fg hover:bg-gruvbox-dark-bg'
                        : 'text-gruvbox-light-fg hover:bg-gruvbox-light-bg'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}

            <div className={`my-1 border-t ${
              isDark ? 'border-gruvbox-dark-gray' : 'border-gruvbox-light-gray'
            }`} />

            <button
              onClick={() => { toggleTheme(); setMenuOpen(false); }}
              className={`w-full text-left px-4 py-2 text-sm transition ${
                isDark
                  ? 'text-gruvbox-dark-fg hover:bg-gruvbox-dark-bg'
                  : 'text-gruvbox-light-fg hover:bg-gruvbox-light-bg'
              }`}
            >
              {isDark ? '☀️ Light Mode' : '🌙 Dark Mode'}
            </button>

            <div className={`px-4 py-2 text-xs ${
              isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
            }`}>
              {user?.username}
            </div>

            <button
              onClick={handleLogout}
              className={`w-full text-left px-4 py-2 text-sm transition ${
                isDark
                  ? 'text-gruvbox-dark-red hover:bg-gruvbox-dark-bg'
                  : 'text-gruvbox-light-red hover:bg-gruvbox-light-bg'
              }`}
            >
              Logout
            </button>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex-1 flex items-center gap-2 ml-4">
        {pageActions.filter(a => !a.hidden).map((action) => (
          <ActionButton key={action.id} action={action} isDark={isDark} />
        ))}
        {sectionActions.length > 0 && (
          <>
            <div className={`w-px h-5 mx-1 ${
              isDark ? 'bg-gruvbox-dark-gray' : 'bg-gruvbox-light-gray'
            }`} />
            {sectionActions.filter(a => !a.hidden).map((action) => (
              <ActionButton key={action.id} action={action} isDark={isDark} />
            ))}
          </>
        )}
      </div>
    </div>
  );
};

export default MenuBar;
