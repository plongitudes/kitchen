import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { recipeAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import RetireRecipeModal from '../components/RetireRecipeModal';
import RecipeImportModal from '../components/RecipeImportModal';
import Toast from '../components/Toast';

const RecipeList = () => {
  const { isDark } = useTheme();
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState({ include_retired: false });
  const [retireModal, setRetireModal] = useState({ isOpen: false, recipe: null });
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [toast, setToast] = useState(null);
  const navigate = useNavigate();

  const fetchRecipes = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await recipeAPI.list(filter);
      setRecipes(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load recipes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecipes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const handleRetireClick = (recipe) => {
    setRetireModal({ isOpen: true, recipe });
  };

  const handleRetireConfirm = async () => {
    if (!retireModal.recipe) return;

    try {
      await recipeAPI.delete(retireModal.recipe.id);

      // Remove from list immediately if not showing retired recipes
      if (!filter.include_retired) {
        setRecipes(recipes.filter(r => r.id !== retireModal.recipe.id));
      } else {
        // Update the recipe in place to show retired status
        const response = await recipeAPI.get(retireModal.recipe.id);
        setRecipes(recipes.map(r =>
          r.id === retireModal.recipe.id ? response.data : r
        ));
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to retire recipe';
      setToast({
        message: errorMsg,
        type: 'error',
      });
    }
  };

  const handleJSONImport = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.json')) {
      setToast({
        message: 'Only .json files are allowed',
        type: 'error',
      });
      event.target.value = '';
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await recipeAPI.post('import-json', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setToast({
        message: response.data.message || 'Recipe imported successfully',
        type: 'success',
      });
      fetchRecipes(); // Refresh list
    } catch (err) {
      setToast({
        message: err.response?.data?.detail || 'Failed to import recipe',
        type: 'error',
      });
    } finally {
      event.target.value = ''; // Reset file input
    }
  };

  if (loading) {
    return (
      <div className={`p-8 flex items-center justify-center ${
        isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'
      }`}>
        <div className={`text-xl ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
          Loading recipes...
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
          Error: {error}
        </div>
      </div>
    );
  }

  return (
    <div className={`p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      <div className="flex justify-between items-center mb-6">
        <h1 className={`text-3xl font-bold ${
          isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
        }`}>
          Recipes
        </h1>
        <div className="flex gap-4">
          <label className={`flex items-center gap-2 ${
            isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
          }`}>
            <input
              type="checkbox"
              checked={filter.include_retired}
              onChange={(e) =>
                setFilter({ ...filter, include_retired: e.target.checked })
              }
              className="rounded"
            />
            <span>Show retired</span>
          </label>
          <button
            onClick={() => setImportModalOpen(true)}
            className={`px-4 py-2 rounded font-semibold transition ${
              isDark
                ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright text-gruvbox-dark-bg'
                : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright text-gruvbox-light-bg'
            }`}
          >
            Import from URL
          </button>
          <label className={`px-4 py-2 rounded font-semibold transition cursor-pointer ${
            isDark
              ? 'bg-gruvbox-dark-aqua hover:bg-gruvbox-dark-aqua-bright text-gruvbox-dark-bg'
              : 'bg-gruvbox-light-aqua hover:bg-gruvbox-light-aqua-bright text-gruvbox-light-bg'
          }`}>
            Import JSON
            <input
              type="file"
              accept=".json"
              onChange={handleJSONImport}
              className="hidden"
            />
          </label>
          <button
            onClick={() => navigate('/recipes/new')}
            className={`px-4 py-2 rounded font-semibold transition ${
              isDark
                ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg'
                : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg'
            }`}
          >
            + New Recipe
          </button>
        </div>
      </div>

      {recipes.length === 0 ? (
        <div className="text-center py-12">
          <p className={`text-xl mb-4 ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
            No recipes yet.
          </p>
          <button
            onClick={() => navigate('/recipes/new')}
            className={`px-6 py-3 rounded font-semibold transition ${
              isDark
                ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg'
                : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg'
            }`}
          >
            Create your first recipe
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {recipes.map((recipe) => (
            <div
              key={recipe.id}
              className={`p-6 rounded-lg border ${
                recipe.retired_at
                  ? isDark
                    ? 'bg-gruvbox-dark-bg-hard border-gruvbox-dark-gray opacity-60'
                    : 'bg-gruvbox-light-bg-hard border-gruvbox-light-gray opacity-60'
                  : isDark
                    ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray hover:border-gruvbox-dark-orange transition'
                    : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray hover:border-gruvbox-light-orange transition'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className={`text-xl font-semibold ${
                  isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
                }`}>
                  {recipe.name}
                </h3>
                {recipe.retired_at && (
                  <span className={`text-xs px-2 py-1 rounded ${
                    isDark
                      ? 'bg-gruvbox-dark-gray text-gruvbox-dark-bg'
                      : 'bg-gruvbox-light-gray text-gruvbox-light-bg'
                  }`}>
                    Retired
                  </span>
                )}
              </div>

              {recipe.recipe_type && (
                <div className={`text-sm mb-2 ${
                  isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                }`}>
                  {recipe.recipe_type}
                </div>
              )}

              <div className={`text-sm mb-4 ${
                isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
              }`}>
                {recipe.prep_time_minutes && (
                  <span>Prep: {recipe.prep_time_minutes}min </span>
                )}
                {recipe.cook_time_minutes && (
                  <span>Cook: {recipe.cook_time_minutes}min</span>
                )}
              </div>

              <div className="flex gap-2">
                <Link
                  to={`/recipes/${recipe.id}`}
                  className={`flex-1 text-center px-3 py-2 rounded transition ${
                    isDark
                      ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright'
                      : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright'
                  }`}
                >
                  View
                </Link>
                {!recipe.retired_at && (
                  <>
                    <Link
                      to={`/recipes/${recipe.id}/edit`}
                      className={`flex-1 text-center px-3 py-2 rounded transition ${
                        isDark
                          ? 'bg-gruvbox-dark-purple hover:bg-gruvbox-dark-purple-bright'
                          : 'bg-gruvbox-light-purple hover:bg-gruvbox-light-purple-bright'
                      }`}
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleRetireClick(recipe)}
                      className={`px-3 py-2 rounded transition ${
                        isDark
                          ? 'bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright'
                          : 'bg-gruvbox-light-red hover:bg-gruvbox-light-red-bright'
                      }`}
                    >
                      Retire
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <RetireRecipeModal
        recipe={retireModal.recipe}
        isOpen={retireModal.isOpen}
        onClose={() => setRetireModal({ isOpen: false, recipe: null })}
        onConfirm={handleRetireConfirm}
      />

      <RecipeImportModal
        isOpen={importModalOpen}
        onClose={() => {
          setImportModalOpen(false);
          fetchRecipes(); // Refresh list after import
        }}
      />

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

export default RecipeList;
