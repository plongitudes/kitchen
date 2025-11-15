import { Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';

const Home = () => {
  const { isDark } = useTheme();

  return (
    <div className={`p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      <h1 className={`text-4xl font-bold mb-4 ${
        isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
      }`}>
        Welcome to Roane's Kitchen
      </h1>
      <p className={`text-lg mb-4 ${
        isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
      }`}>
        Your meal planning and grocery management system.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <Link
          to="/recipes"
          className={`p-6 rounded-lg border transition cursor-pointer ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray hover:border-gruvbox-dark-orange'
              : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray hover:border-gruvbox-light-orange'
          }`}>
          <h2 className={`text-xl font-semibold mb-2 ${
            isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
          }`}>
            Recipes
          </h2>
          <p className={isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}>
            Manage your recipe collection
          </p>
        </Link>
        <Link
          to="/schedules"
          className={`p-6 rounded-lg border transition cursor-pointer ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray hover:border-gruvbox-dark-green'
              : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray hover:border-gruvbox-light-green'
          }`}>
          <h2 className={`text-xl font-semibold mb-2 ${
            isDark ? 'text-gruvbox-dark-green-bright' : 'text-gruvbox-light-green-bright'
          }`}>
            Schedules
          </h2>
          <p className={isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}>
            Plan your weekly meals
          </p>
        </Link>
        <Link
          to="/meal-plans"
          className={`p-6 rounded-lg border transition cursor-pointer ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray hover:border-gruvbox-dark-blue'
              : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray hover:border-gruvbox-light-blue'
          }`}>
          <h2 className={`text-xl font-semibold mb-2 ${
            isDark ? 'text-gruvbox-dark-blue-bright' : 'text-gruvbox-light-blue-bright'
          }`}>
            Meal Plans
          </h2>
          <p className={isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}>
            View current and upcoming meal plans
          </p>
        </Link>
      </div>
    </div>
  );
};

export default Home;
