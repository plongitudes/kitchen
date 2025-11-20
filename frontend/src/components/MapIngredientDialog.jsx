import { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { ingredientAPI } from '../services/api';
import Toast from './Toast';

const MapIngredientDialog = ({ unmappedIngredient, onClose, onComplete }) => {
  const { isDark } = useTheme();
  const [ingredients, setIngredients] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [showRecipes, setShowRecipes] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedIngredient, setSelectedIngredient] = useState(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState(unmappedIngredient.ingredient_name);
  const [newCategory, setNewCategory] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState(null);

  const categories = ['dairy', 'produce', 'meat', 'pantry', 'spices', 'seafood', 'condiments', 'baking'];

  useEffect(() => {
    loadIngredients();
    loadRecipes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm]);

  const loadIngredients = async () => {
    try {
      const response = await ingredientAPI.listIngredients(searchTerm);
      setIngredients(response.data);
    } catch (err) {
      console.error('Failed to load ingredients:', err);
    }
  };

  const loadRecipes = async () => {
    try {
      const response = await ingredientAPI.getRecipesForUnmapped(unmappedIngredient.ingredient_name);
      setRecipes(response.data);
    } catch (err) {
      console.error('Failed to load recipes:', err);
    }
  };

  const handleMapToExisting = async () => {
    if (!selectedIngredient) return;

    setSubmitting(true);
    try {
      await ingredientAPI.mapIngredient(
        unmappedIngredient.ingredient_name,
        selectedIngredient.id
      );
      onComplete();
    } catch (err) {
      setToast({
        message: err.response?.data?.detail || 'Failed to map ingredient',
        type: 'error',
      });
      setSubmitting(false);
    }
  };

  const handleCreateNew = async () => {
    if (!newName.trim()) return;

    setSubmitting(true);
    try {
      await ingredientAPI.createWithMapping(
        newName,
        newCategory || null,
        unmappedIngredient.ingredient_name
      );
      onComplete();
    } catch (err) {
      setToast({
        message: err.response?.data?.detail || 'Failed to create ingredient',
        type: 'error',
      });
      setSubmitting(false);
    }
  };

  // Helper function to calculate word match score
  const calculateMatchScore = (commonIngredientName, unmappedName) => {
    const unmappedWords = unmappedName.toLowerCase().split(/[\s,]+/).filter(w => w.length > 2);
    const commonWords = commonIngredientName.toLowerCase().split(/[\s,]+/).filter(w => w.length > 2);

    let score = 0;
    unmappedWords.forEach(unmappedWord => {
      commonWords.forEach(commonWord => {
        if (unmappedWord === commonWord) {
          score += 2; // Exact match
        } else if (unmappedWord.includes(commonWord) || commonWord.includes(unmappedWord)) {
          score += 1; // Partial match
        }
      });
    });

    return score;
  };

  // Sort ingredients by relevance when not searching
  const sortedIngredients = searchTerm
    ? ingredients
    : [...ingredients].sort((a, b) => {
        const scoreA = calculateMatchScore(a.name, unmappedIngredient.ingredient_name);
        const scoreB = calculateMatchScore(b.name, unmappedIngredient.ingredient_name);

        if (scoreB !== scoreA) {
          return scoreB - scoreA; // Higher score first
        }

        // If same score, sort by usage count
        return b.recipe_count - a.recipe_count;
      });

  const filteredIngredients = searchTerm
    ? sortedIngredients
    : sortedIngredients.slice(0, 10); // Show top 10 when no search

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className={`max-w-2xl w-full max-h-[90vh] overflow-y-auto rounded-lg ${
        isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'
      }`}>
        <div className={`sticky top-0 p-6 border-b ${
          isDark ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray' : 'bg-gruvbox-light-bg border-gruvbox-light-gray'
        }`}>
          <h2 className={`text-2xl font-bold mb-2 ${
            isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
          }`}>
            Map Ingredient
          </h2>
          <p className={`text-lg ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
            "{unmappedIngredient.ingredient_name}"
          </p>
          <div className="flex items-center gap-3">
            <p className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
              Used in {unmappedIngredient.recipe_count} recipe{unmappedIngredient.recipe_count !== 1 ? 's' : ''}
            </p>
            {recipes.length > 0 && (
              <button
                onClick={() => setShowRecipes(!showRecipes)}
                className={`text-sm px-2 py-1 rounded transition ${
                  isDark
                    ? 'text-gruvbox-dark-blue hover:bg-gruvbox-dark-bg-soft'
                    : 'text-gruvbox-light-blue hover:bg-gruvbox-light-bg-soft'
                }`}
              >
                {showRecipes ? '▼ Hide Recipes' : '▶ Show Recipes'}
              </button>
            )}
          </div>
          {showRecipes && recipes.length > 0 && (
            <div className={`mt-3 p-3 rounded border ${
              isDark ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray' : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
            }`}>
              <ul className="space-y-1">
                {recipes.map((recipe) => (
                  <li key={recipe.id} className={`text-sm ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
                    • {recipe.name}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="p-6 space-y-6">
          {/* Toggle between Map and Create */}
          <div className="flex gap-4 border-b ${isDark ? 'border-gruvbox-dark-gray' : 'border-gruvbox-light-gray'}">
            <button
              onClick={() => setCreating(false)}
              className={`px-4 py-2 -mb-px border-b-2 transition ${
                !creating
                  ? `${isDark ? 'border-gruvbox-dark-orange-bright text-gruvbox-dark-orange-bright' : 'border-gruvbox-light-orange-bright text-gruvbox-light-orange-bright'}`
                  : `border-transparent ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`
              }`}
            >
              Map to Existing
            </button>
            <button
              onClick={() => setCreating(true)}
              className={`px-4 py-2 -mb-px border-b-2 transition ${
                creating
                  ? `${isDark ? 'border-gruvbox-dark-orange-bright text-gruvbox-dark-orange-bright' : 'border-gruvbox-light-orange-bright text-gruvbox-light-orange-bright'}`
                  : `border-transparent ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`
              }`}
            >
              Create New
            </button>
          </div>

          {!creating ? (
            /* Map to Existing */
            <>
              <div>
                <input
                  type="text"
                  placeholder="Search existing ingredients..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className={`w-full px-4 py-2 rounded border ${
                    isDark
                      ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray text-gruvbox-dark-fg placeholder-gruvbox-dark-gray'
                      : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray text-gruvbox-light-fg placeholder-gruvbox-light-gray'
                  }`}
                />
              </div>

              <div className="space-y-2 max-h-96 overflow-y-auto">
                {filteredIngredients.map(ingredient => (
                  <div
                    key={ingredient.id}
                    onClick={() => setSelectedIngredient(ingredient)}
                    className={`p-3 rounded border cursor-pointer transition ${
                      selectedIngredient?.id === ingredient.id
                        ? `${isDark ? 'border-gruvbox-dark-orange bg-gruvbox-dark-bg-hard' : 'border-gruvbox-light-orange bg-gruvbox-light-bg-hard'}`
                        : `${isDark ? 'border-gruvbox-dark-gray hover:border-gruvbox-dark-orange' : 'border-gruvbox-light-gray hover:border-gruvbox-light-orange'}`
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className={`font-semibold ${
                          isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                        }`}>
                          {ingredient.name}
                        </h3>
                        {ingredient.category && (
                          <span className={`text-xs ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                            {ingredient.category}
                          </span>
                        )}
                      </div>
                      <span className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                        {ingredient.recipe_count} recipes
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-2 pt-4 border-t ${isDark ? 'border-gruvbox-dark-gray' : 'border-gruvbox-light-gray'}">
                <button
                  onClick={handleMapToExisting}
                  disabled={!selectedIngredient || submitting}
                  className={`flex-1 px-4 py-2 rounded transition ${
                    !selectedIngredient || submitting
                      ? `${isDark ? 'bg-gruvbox-dark-bg-hard text-gruvbox-dark-gray' : 'bg-gruvbox-light-bg-hard text-gruvbox-light-gray'} cursor-not-allowed`
                      : `${isDark ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg' : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg'}`
                  }`}
                >
                  {submitting ? 'Mapping...' : 'Map to Selected'}
                </button>
                <button
                  onClick={onClose}
                  disabled={submitting}
                  className={`px-4 py-2 rounded transition ${
                    isDark
                      ? 'bg-gruvbox-dark-bg-soft hover:bg-gruvbox-dark-bg-hard'
                      : 'bg-gruvbox-light-bg-soft hover:bg-gruvbox-light-bg-hard'
                  }`}
                >
                  Cancel
                </button>
              </div>
            </>
          ) : (
            /* Create New */
            <>
              <div className="space-y-4">
                <div>
                  <label className={`block text-sm font-medium mb-2 ${
                    isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                  }`}>
                    Common Ingredient Name
                  </label>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className={`w-full px-4 py-2 rounded border ${
                      isDark
                        ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray text-gruvbox-dark-fg'
                        : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray text-gruvbox-light-fg'
                    }`}
                  />
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-2 ${
                    isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                  }`}>
                    Category (optional)
                  </label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className={`w-full px-4 py-2 rounded border ${
                      isDark
                        ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray text-gruvbox-dark-fg'
                        : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray text-gruvbox-light-fg'
                    }`}
                  >
                    <option value="">No category</option>
                    {categories.map(cat => (
                      <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
                    ))}
                  </select>
                </div>

                <div className={`p-3 rounded ${isDark ? 'bg-gruvbox-dark-bg-soft' : 'bg-gruvbox-light-bg-soft'}`}>
                  <p className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                    This will create a new common ingredient "{newName}" and map "{unmappedIngredient.ingredient_name}" as an alias.
                  </p>
                </div>
              </div>

              <div className="flex gap-2 pt-4 border-t ${isDark ? 'border-gruvbox-dark-gray' : 'border-gruvbox-light-gray'}">
                <button
                  onClick={handleCreateNew}
                  disabled={!newName.trim() || submitting}
                  className={`flex-1 px-4 py-2 rounded transition ${
                    !newName.trim() || submitting
                      ? `${isDark ? 'bg-gruvbox-dark-bg-hard text-gruvbox-dark-gray' : 'bg-gruvbox-light-bg-hard text-gruvbox-light-gray'} cursor-not-allowed`
                      : `${isDark ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg' : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg'}`
                  }`}
                >
                  {submitting ? 'Creating...' : 'Create & Map'}
                </button>
                <button
                  onClick={onClose}
                  disabled={submitting}
                  className={`px-4 py-2 rounded transition ${
                    isDark
                      ? 'bg-gruvbox-dark-bg-soft hover:bg-gruvbox-dark-bg-hard'
                      : 'bg-gruvbox-light-bg-soft hover:bg-gruvbox-light-bg-hard'
                  }`}
                >
                  Cancel
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default MapIngredientDialog;
