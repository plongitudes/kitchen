import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const Layout = () => {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) {
    return <Outlet />;
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar Navigation */}
      <nav className={`w-64 border-r p-4 ${
        isDark
          ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
          : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
      }`}>
        <div className="mb-8">
          <h1 className={`text-2xl font-bold ${
            isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
          }`}>
            Roane's Kitchen
          </h1>
        </div>

        <ul className="space-y-2">
          <li>
            <Link
              to="/"
              className={`block p-3 rounded transition ${
                isDark
                  ? 'hover:bg-gruvbox-dark-bg'
                  : 'hover:bg-gruvbox-light-bg-hard'
              }`}
            >
              Home
            </Link>
          </li>
          <li>
            <Link
              to="/recipes"
              className={`block p-3 rounded transition ${
                isDark
                  ? 'hover:bg-gruvbox-dark-bg'
                  : 'hover:bg-gruvbox-light-bg-hard'
              }`}
            >
              Recipes
            </Link>
          </li>
          <li>
            <Link
              to="/schedules"
              className={`block p-3 rounded transition ${
                isDark
                  ? 'hover:bg-gruvbox-dark-bg'
                  : 'hover:bg-gruvbox-light-bg-hard'
              }`}
            >
              Schedules
            </Link>
          </li>
          <li>
            <Link
              to="/templates"
              className={`block p-3 rounded transition ${
                isDark
                  ? 'hover:bg-gruvbox-dark-bg'
                  : 'hover:bg-gruvbox-light-bg-hard'
              }`}
            >
              Templates
            </Link>
          </li>
          <li>
            <Link
              to="/meal-plans"
              className={`block p-3 rounded transition ${
                isDark
                  ? 'hover:bg-gruvbox-dark-bg'
                  : 'hover:bg-gruvbox-light-bg-hard'
              }`}
            >
              Meal Plans
            </Link>
          </li>
          <li>
            <Link
              to="/grocery-lists"
              className={`block p-3 rounded transition ${
                isDark
                  ? 'hover:bg-gruvbox-dark-bg'
                  : 'hover:bg-gruvbox-light-bg-hard'
              }`}
            >
              Grocery Lists
            </Link>
          </li>
          <li>
            <Link
              to="/settings"
              className={`block p-3 rounded transition ${
                isDark
                  ? 'hover:bg-gruvbox-dark-bg'
                  : 'hover:bg-gruvbox-light-bg-hard'
              }`}
            >
              Settings
            </Link>
          </li>
          <li>
            <Link
              to="/backup"
              className={`block p-3 rounded transition ${
                isDark
                  ? 'hover:bg-gruvbox-dark-bg'
                  : 'hover:bg-gruvbox-light-bg-hard'
              }`}
            >
              Backup
            </Link>
          </li>
        </ul>

        <div className={`mt-8 pt-4 border-t ${
          isDark ? 'border-gruvbox-dark-gray' : 'border-gruvbox-light-gray'
        }`}>
          <button
            onClick={toggleTheme}
            className={`w-full p-3 mb-2 rounded transition ${
              isDark
                ? 'bg-gruvbox-dark-bg hover:bg-gruvbox-dark-bg-hard'
                : 'bg-gruvbox-light-bg hover:bg-gruvbox-light-bg-hard'
            }`}
          >
            {isDark ? '☀️ Light Mode' : '🌙 Dark Mode'}
          </button>
          <div className={`text-sm mb-2 ${
            isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
          }`}>
            Logged in as: {user.username}
          </div>
          <button
            onClick={handleLogout}
            className={`w-full p-3 rounded transition ${
              isDark
                ? 'bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright'
                : 'bg-gruvbox-light-red hover:bg-gruvbox-light-red-bright'
            }`}
          >
            Logout
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
