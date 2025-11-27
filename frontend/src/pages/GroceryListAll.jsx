import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { mealPlanAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { formatLocalDate } from '../utils/dateUtils';

const GroceryListAll = () => {
  const { isDark } = useTheme();
  const [groceryLists, setGroceryLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadGroceryLists();
  }, []);

  const loadGroceryLists = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await mealPlanAPI.listAllGroceryLists();
      setGroceryLists(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load grocery lists');
    } finally {
      setLoading(false);
    }
  };

  // Use utility for date-only strings (shopping_date) to avoid UTC timezone shifts
  const formatDate = (dateString) => formatLocalDate(dateString, {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  // formatDateTime is for full datetime strings (generated_at) - native Date is fine
  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const handleGenerateForToday = async () => {
    // Find most recent meal plan instance with current week
    const latestList = groceryLists[0];
    if (!latestList) {
      setError('No meal plan found. Create a schedule first.');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      const today = new Date().toISOString().split('T')[0];
      await mealPlanAPI.generateGroceryList(latestList.meal_plan_instance_id, today);
      await loadGroceryLists();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate grocery list');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className={`p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Loading grocery lists...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
        <div className={`p-4 rounded ${
          isDark ? 'bg-gruvbox-dark-red text-gruvbox-dark-bg' : 'bg-gruvbox-light-red text-gruvbox-light-bg'
        }`}>
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className={`text-3xl font-bold ${
            isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
          }`}>
            Grocery Lists
          </h1>
          <button
            onClick={handleGenerateForToday}
            disabled={generating}
            className={`px-4 py-2 rounded font-semibold transition ${
              generating
                ? isDark
                  ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                  : 'bg-gruvbox-light-gray cursor-not-allowed'
                : isDark
                  ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                  : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
            }`}
          >
            {generating ? 'Generating...' : 'Generate for Today'}
          </button>
        </div>

        {groceryLists.length === 0 ? (
          <div className={`text-center p-8 border-2 border-dashed rounded ${
            isDark ? 'border-gruvbox-dark-gray text-gruvbox-dark-gray' : 'border-gruvbox-light-gray text-gruvbox-light-gray'
          }`}>
            <p className="mb-4">No grocery lists yet</p>
            <p className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
              Generate grocery lists from your meal plans on shopping days
            </p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {groceryLists.map((list) => (
              <Link
                key={list.id}
                to={`/grocery-lists/${list.id}`}
                className={`block p-6 rounded border-2 transition ${
                  isDark
                    ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray hover:border-gruvbox-dark-green'
                    : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray hover:border-gruvbox-light-green'
                }`}
              >
                <h3 className={`text-xl font-bold mb-2 ${
                  isDark ? 'text-gruvbox-dark-green-bright' : 'text-gruvbox-light-green-bright'
                }`}>
                  {formatDate(list.shopping_date)}
                </h3>
                <div className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                  Generated {formatDateTime(list.generated_at)}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default GroceryListAll;
