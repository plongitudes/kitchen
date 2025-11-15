import { useState, useEffect } from 'react';
import { recipeAPI } from '../services/api';

const RetireRecipeModal = ({ recipe, isOpen, onClose, onConfirm }) => {
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchUsage = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await recipeAPI.get(`${recipe.id}/usage`);
      setUsage(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to check recipe usage');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && recipe) {
      fetchUsage();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, recipe]);

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gruvbox-dark-bg-soft border border-gruvbox-dark-gray rounded-lg p-6 max-w-lg w-full mx-4">
        <h2 className="text-2xl font-bold mb-4 text-gruvbox-dark-orange-bright">
          Retire Recipe: {recipe?.name}
        </h2>

        {loading && (
          <div className="py-4 text-center">
            <p>Checking recipe usage...</p>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-gruvbox-dark-red rounded">
            {error}
          </div>
        )}

        {!loading && !error && usage && (
          <>
            {usage.is_used ? (
              <div className="mb-4">
                <div className="mb-3 p-3 bg-gruvbox-dark-yellow text-gruvbox-dark-bg rounded">
                  <p className="font-semibold mb-2">⚠️ Warning: This recipe is currently in use!</p>
                  <p className="text-sm">
                    Retiring this recipe will affect the following week templates:
                  </p>
                </div>

                <div className="bg-gruvbox-dark-bg p-4 rounded border border-gruvbox-dark-gray max-h-48 overflow-y-auto">
                  <ul className="space-y-2">
                    {usage.templates.map((template, index) => (
                      <li key={index} className="text-sm">
                        <span className="font-semibold text-gruvbox-dark-orange">
                          {template.theme_name}
                        </span>
                        {' - '}
                        <span className="text-gruvbox-dark-gray">
                          {getDayName(template.day_of_week)}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                <p className="mt-3 text-sm text-gruvbox-dark-gray">
                  You'll need to update these templates before retiring this recipe,
                  or the week instances using this template may fail to generate properly.
                </p>

                <div className="mt-4 p-3 bg-gruvbox-dark-red bg-opacity-20 border border-gruvbox-dark-red rounded">
                  <p className="text-sm font-semibold">
                    Cannot retire recipe while it's in use.
                  </p>
                </div>
              </div>
            ) : (
              <div className="mb-4">
                <p className="mb-3">
                  Are you sure you want to retire "{recipe.name}"?
                </p>
                <p className="text-sm text-gruvbox-dark-gray">
                  This recipe is not currently used in any week templates.
                  Retired recipes can be restored later if needed.
                </p>
              </div>
            )}
          </>
        )}

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright rounded transition"
          >
            Cancel
          </button>
          {!loading && !error && usage && !usage.is_used && (
            <button
              onClick={handleConfirm}
              className="px-4 py-2 bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright rounded font-semibold transition"
            >
              Retire Recipe
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper function to convert day number to name
const getDayName = (dayNum) => {
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  return days[dayNum] || `Day ${dayNum}`;
};

export default RetireRecipeModal;
