import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { mealPlanAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { formatGroceryItem } from '../utils/unitFormatter';

const GroceryListDetail = () => {
  const { id } = useParams();
  const { isDark } = useTheme();
  const [groceryList, setGroceryList] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadGroceryList = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await mealPlanAPI.getGroceryList(id);
      setGroceryList(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load grocery list');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGroceryList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const groupItemsByCategory = (items) => {
    // Simple grouping by first letter for now
    // Could be enhanced with category classification
    const grouped = {};
    items.forEach(item => {
      const firstLetter = item.ingredient_name[0].toUpperCase();
      if (!grouped[firstLetter]) {
        grouped[firstLetter] = [];
      }
      grouped[firstLetter].push(item);
    });
    return grouped;
  };

  if (loading) {
    return (
      <div className={`p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Loading grocery list...
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

  if (!groceryList) {
    return (
      <div className={`p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Grocery list not found
        </div>
      </div>
    );
  }

  const groupedItems = groupItemsByCategory(groceryList.items || []);
  const sortedCategories = Object.keys(groupedItems).sort();

  return (
    <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-4 mb-4">
            <Link
              to="/grocery-lists"
              className={`px-3 py-1 rounded transition ${
                isDark
                  ? 'bg-gruvbox-dark-bg-soft hover:bg-gruvbox-dark-bg-hard'
                  : 'bg-gruvbox-light-bg-soft hover:bg-gruvbox-light-bg-hard'
              }`}
            >
              ← Back
            </Link>
          </div>
          <h1 className={`text-3xl font-bold mb-2 ${
            isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
          }`}>
            Grocery List
          </h1>
          <p className={`text-lg ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
            Shopping Date: {formatDate(groceryList.shopping_date)}
          </p>
          <p className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
            Generated {formatDateTime(groceryList.generated_at)}
          </p>
        </div>

        {/* Items List */}
        {groceryList.items.length === 0 ? (
          <div className={`text-center p-8 border-2 border-dashed rounded ${
            isDark ? 'border-gruvbox-dark-gray text-gruvbox-dark-gray' : 'border-gruvbox-light-gray text-gruvbox-light-gray'
          }`}>
            No items in this grocery list
          </div>
        ) : (
          <div className="space-y-6">
            {sortedCategories.map(category => (
              <div key={category}>
                <h2 className={`text-2xl font-bold mb-4 ${
                  isDark ? 'text-gruvbox-dark-green-bright' : 'text-gruvbox-light-green-bright'
                }`}>
                  {category}
                </h2>
                <div className={`p-6 rounded-lg border ${
                  isDark
                    ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
                    : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
                }`}>
                  <ul className="space-y-3">
                    {groupedItems[category].map((item) => (
                      <li key={item.id} className="flex flex-col gap-1">
                        <div className="flex items-baseline gap-3">
                          <span className={`text-lg font-semibold ${
                            isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                          }`}>
                            {formatGroceryItem(item.total_quantity, item.unit)}
                          </span>
                          <span className={`text-lg ${
                            isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                          }`}>
                            {item.ingredient_name}
                          </span>
                        </div>
                        {item.source_recipe_ids && item.source_recipe_ids.length > 0 && (
                          <div className={`text-sm ml-6 ${
                            isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                          }`}>
                            Used in {item.source_recipe_ids.length} recipe{item.source_recipe_ids.length !== 1 ? 's' : ''}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Summary */}
        <div className={`mt-8 p-4 rounded border ${
          isDark
            ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
            : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
        }`}>
          <div className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
            Total items: <span className="font-semibold">{groceryList.items.length}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GroceryListDetail;
