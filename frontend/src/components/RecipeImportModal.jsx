import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { recipeAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';

const RecipeImportModal = ({ isOpen, onClose }) => {
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [scrapedData, setScrapedData] = useState(null);
  const urlInputRef = useRef(null);

  // Auto-focus the input when modal opens
  useEffect(() => {
    if (isOpen && !scrapedData && urlInputRef.current) {
      urlInputRef.current.focus();
    }
  }, [isOpen, scrapedData]);

  const handleScrape = async () => {
    if (!url.trim()) {
      setError('Please enter a URL');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await recipeAPI.importPreview(url);
      setScrapedData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to import recipe');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (andEdit = false) => {
    if (!scrapedData) return;

    try {
      setLoading(true);
      setError(null);

      // Create recipe with scraped data
      const recipeData = {
        name: scrapedData.name,
        recipe_type: scrapedData.recipe_type,
        description: scrapedData.description,
        prep_time_minutes: scrapedData.prep_time_minutes,
        cook_time_minutes: scrapedData.cook_time_minutes,
        source_url: scrapedData.source_url,
        ingredients: scrapedData.ingredients.map((ing, idx) => ({
          ingredient_name: ing.ingredient_name,
          quantity: ing.quantity,
          unit: ing.unit,
          order: idx,
        })),
        instructions: scrapedData.instructions.map((inst) => ({
          step_number: inst.step_number,
          description: inst.description,
        })),
      };

      const response = await recipeAPI.create(recipeData);

      // Navigate to the newly created recipe (edit or detail)
      if (andEdit) {
        navigate(`/recipes/${response.data.id}/edit`);
      } else {
        navigate(`/recipes/${response.data.id}`);
      }
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save recipe');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setUrl('');
    setScrapedData(null);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className={`${
        isDark ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray' : 'bg-gruvbox-light-bg1 border-gruvbox-light-gray'
      } border rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto`}>
        <div className="flex justify-between items-center mb-4">
          <h2 className={`text-2xl font-bold ${
            isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
          }`}>
            Import Recipe from URL
          </h2>

          {/* Action buttons at top */}
          {!scrapedData ? (
            <div className="flex gap-2">
              <button
                onClick={handleClose}
                disabled={loading}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright text-gruvbox-dark-fg'
                    : 'bg-gruvbox-light-gray hover:bg-gruvbox-light-gray-bright text-gruvbox-light-fg'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={handleScrape}
                disabled={loading || !url.trim()}
                className={`px-4 py-2 rounded font-semibold transition ${
                  isDark
                    ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg disabled:opacity-50'
                    : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg disabled:opacity-50'
                }`}
              >
                {loading ? 'Importing...' : 'Import'}
              </button>
            </div>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={() => setScrapedData(null)}
                disabled={loading}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright text-gruvbox-dark-fg'
                    : 'bg-gruvbox-light-gray hover:bg-gruvbox-light-gray-bright text-gruvbox-light-fg'
                }`}
              >
                Back
              </button>
              <button
                onClick={handleClose}
                disabled={loading}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright text-gruvbox-dark-fg'
                    : 'bg-gruvbox-light-gray hover:bg-gruvbox-light-gray-bright text-gruvbox-light-fg'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={() => handleSave(true)}
                disabled={loading}
                className={`px-4 py-2 rounded font-semibold transition ${
                  isDark
                    ? 'bg-gruvbox-dark-purple hover:bg-gruvbox-dark-purple-bright text-gruvbox-dark-bg disabled:opacity-50'
                    : 'bg-gruvbox-light-purple hover:bg-gruvbox-light-purple-bright text-gruvbox-light-bg disabled:opacity-50'
                }`}
              >
                {loading ? 'Saving...' : 'Save & Edit'}
              </button>
              <button
                onClick={() => handleSave(false)}
                disabled={loading}
                className={`px-4 py-2 rounded font-semibold transition ${
                  isDark
                    ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg disabled:opacity-50'
                    : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg disabled:opacity-50'
                }`}
              >
                {loading ? 'Saving...' : 'Save Recipe'}
              </button>
            </div>
          )}
        </div>

        {error && (
          <div className={`mb-4 p-3 rounded ${
            isDark ? 'bg-gruvbox-dark-red text-gruvbox-dark-bg' : 'bg-gruvbox-light-red text-gruvbox-light-bg'
          }`}>
            {error}
          </div>
        )}

        {!scrapedData ? (
          // Step 1: URL Input
          <div>
            <label className={`block mb-2 ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
              Recipe URL
            </label>
            <input
              ref={urlInputRef}
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleScrape()}
              placeholder="https://www.allrecipes.com/recipe/..."
              className={`w-full p-2 rounded border ${
                isDark
                  ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                  : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
              }`}
              disabled={loading}
            />
          </div>
        ) : (
          // Step 2: Preview & Save
          <div>
            <div className={`mb-4 p-4 rounded ${
              isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'
            }`}>
              <h3 className={`text-xl font-bold mb-2 ${
                isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
              }`}>
                {scrapedData.name}
              </h3>

              {scrapedData.description && (
                <p className={`mb-4 ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
                  {scrapedData.description}
                </p>
              )}

              <div className={`flex gap-4 mb-4 text-sm ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
                {scrapedData.prep_time_minutes && (
                  <span>Prep: {scrapedData.prep_time_minutes} min</span>
                )}
                {scrapedData.cook_time_minutes && (
                  <span>Cook: {scrapedData.cook_time_minutes} min</span>
                )}
                <span>Type: {scrapedData.recipe_type}</span>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <h4 className={`font-semibold mb-2 ${isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'}`}>
                    Ingredients ({scrapedData.ingredients.length})
                  </h4>
                  <ul className={`text-sm space-y-1 ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
                    {scrapedData.ingredients.slice(0, 10).map((ing, idx) => (
                      <li key={idx}>
                        {ing.quantity} {ing.unit} {ing.ingredient_name}
                      </li>
                    ))}
                    {scrapedData.ingredients.length > 10 && (
                      <li className="italic">... and {scrapedData.ingredients.length - 10} more</li>
                    )}
                  </ul>
                </div>

                <div>
                  <h4 className={`font-semibold mb-2 ${isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'}`}>
                    Instructions ({scrapedData.instructions.length} steps)
                  </h4>
                  <ol className={`text-sm space-y-1 list-decimal list-inside ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
                    {scrapedData.instructions.slice(0, 5).map((inst, idx) => (
                      <li key={idx} className="line-clamp-2">
                        {inst.description}
                      </li>
                    ))}
                    {scrapedData.instructions.length > 5 && (
                      <li className="italic">... and {scrapedData.instructions.length - 5} more steps</li>
                    )}
                  </ol>
                </div>
              </div>

              <p className={`mt-4 text-xs ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                Source: {scrapedData.source_url}
              </p>
            </div>

          </div>
        )}
      </div>
    </div>
  );
};

export default RecipeImportModal;
