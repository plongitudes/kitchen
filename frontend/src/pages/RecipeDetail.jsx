import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { recipeAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import RetireRecipeModal from '../components/RetireRecipeModal';

const RecipeDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const [recipe, setRecipe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retireModal, setRetireModal] = useState(false);
  const [reimportModal, setReimportModal] = useState(false);
  const [reimporting, setReimporting] = useState(false);

  useEffect(() => {
    fetchRecipe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const fetchRecipe = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await recipeAPI.get(id);
      setRecipe(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load recipe');
    } finally {
      setLoading(false);
    }
  };

  const handleRetireConfirm = async () => {
    try {
      await recipeAPI.delete(id);
      navigate('/recipes');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to retire recipe';
      alert(errorMsg);
    }
  };

  const handleExportJSON = async () => {
    try {
      const response = await recipeAPI.get(`${id}/export`, { responseType: 'blob' });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${recipe.name}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to export recipe');
    }
  };

  const handleReimportConfirm = async () => {
    try {
      setReimporting(true);
      const response = await recipeAPI.reimport(id);
      setRecipe(response.data);
      setReimportModal(false);
      alert('Recipe successfully re-imported from source!');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to re-import recipe';
      alert(errorMsg);
    } finally {
      setReimporting(false);
    }
  };

  if (loading) {
    return (
      <div className={`p-8 flex items-center justify-center ${
        isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'
      }`}>
        <div className={`text-xl ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
          Loading recipe...
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
    <div className={`p-8 max-w-4xl mx-auto ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      {/* Header with Action Buttons */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <h1 className={`text-3xl font-bold ${
            isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
          }`}>
            {recipe.name}
          </h1>
        </div>

        {/* Action Buttons Row */}
        <div className="flex gap-2 mb-4 flex-wrap">
          <Link
            to="/recipes"
            className={`px-4 py-2 rounded transition ${
              isDark
                ? 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-fg-0'
                : 'bg-gruvbox-light-gray hover:bg-gruvbox-light-fg-0'
            }`}
          >
            ← Back to Recipes
          </Link>
          <Link
            to={`/recipes/${id}/edit`}
            className={`px-4 py-2 rounded transition ${
              isDark
                ? 'bg-gruvbox-dark-purple hover:bg-gruvbox-dark-purple-bright'
                : 'bg-gruvbox-light-purple hover:bg-gruvbox-light-purple-bright'
            }`}
          >
            Edit
          </Link>
          {recipe.source_url && (
            <a
              href={recipe.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className={`px-4 py-2 rounded transition ${
                isDark
                  ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright'
                  : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright'
              }`}
            >
              View Original →
            </a>
          )}
          {recipe.source_url && !recipe.retired_at && (
            <button
              onClick={() => setReimportModal(true)}
              className={`px-4 py-2 rounded transition ${
                isDark
                  ? 'bg-gruvbox-dark-aqua hover:bg-gruvbox-dark-aqua-bright text-gruvbox-dark-bg'
                  : 'bg-gruvbox-light-aqua hover:bg-gruvbox-light-aqua-bright text-gruvbox-light-bg'
              }`}
            >
              Re-import from Source
            </button>
          )}
          <button
            onClick={handleExportJSON}
            className={`px-4 py-2 rounded transition ${
              isDark
                ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright'
                : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright'
            }`}
          >
            Export JSON
          </button>
          {!recipe.retired_at && (
            <button
              onClick={() => setRetireModal(true)}
              className={`px-4 py-2 rounded transition ${
                isDark
                  ? 'bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright'
                  : 'bg-gruvbox-light-red hover:bg-gruvbox-light-red-bright'
              }`}
            >
              Retire
            </button>
          )}
        </div>

        {/* Recipe Type and Description */}
        {recipe.recipe_type && (
          <div className={`text-lg ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
            {recipe.recipe_type}
          </div>
        )}
        {recipe.description && (
          <p className={`mt-2 text-base ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
            {recipe.description}
          </p>
        )}
      </div>

      {/* Times */}
      {(recipe.prep_time_minutes || recipe.cook_time_minutes) && (
        <div className={`p-4 rounded-lg border mb-6 ${
          isDark
            ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
            : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
        }`}>
          <div className="flex gap-6">
            {recipe.prep_time_minutes && (
              <div>
                <div className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                  Prep Time
                </div>
                <div className={`text-lg font-semibold ${
                  isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                }`}>
                  {recipe.prep_time_minutes} minutes
                </div>
              </div>
            )}
            {recipe.cook_time_minutes && (
              <div>
                <div className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                  Cook Time
                </div>
                <div className={`text-lg font-semibold ${
                  isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                }`}>
                  {recipe.cook_time_minutes} minutes
                </div>
              </div>
            )}
            {recipe.prep_time_minutes && recipe.cook_time_minutes && (
              <div>
                <div className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                  Total Time
                </div>
                <div className={`text-lg font-semibold ${
                  isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                }`}>
                  {recipe.prep_time_minutes + recipe.cook_time_minutes} minutes
                </div>
              </div>
            )}
          </div>
        </div>
      )}


      {/* Ingredients */}
      {recipe.ingredients && recipe.ingredients.length > 0 && (
        <div className={`p-6 rounded-lg border mb-6 ${
          isDark
            ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
            : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
        }`}>
          <h2 className={`text-2xl font-semibold mb-4 ${
            isDark ? 'text-gruvbox-dark-green-bright' : 'text-gruvbox-light-green-bright'
          }`}>
            Ingredients
          </h2>
          <ul className="space-y-2">
            {recipe.ingredients
              .sort((a, b) => a.order - b.order)
              .map((ing) => (
                <li key={ing.id} className="flex gap-3">
                  <span className={isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'}>•</span>
                  <span className={isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}>
                    {ing.quantity} {ing.unit} {ing.ingredient_name}
                  </span>
                </li>
              ))}
          </ul>
        </div>
      )}

      {/* Instructions */}
      {recipe.instructions && recipe.instructions.length > 0 && (
        <div className={`p-6 rounded-lg border mb-6 ${
          isDark
            ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
            : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
        }`}>
          <h2 className={`text-2xl font-semibold mb-4 ${
            isDark ? 'text-gruvbox-dark-green-bright' : 'text-gruvbox-light-green-bright'
          }`}>
            Instructions
          </h2>
          <ol className="space-y-4">
            {recipe.instructions
              .sort((a, b) => a.step_number - b.step_number)
              .map((inst) => (
                <li key={inst.id} className="flex gap-3">
                  <span className={`font-bold ${
                    isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
                  }`}>
                    {inst.step_number}.
                  </span>
                  <div>
                    <p className={isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}>
                      {inst.description}
                    </p>
                    {inst.duration_minutes && (
                      <p className={`text-sm mt-1 ${
                        isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                      }`}>
                        ({inst.duration_minutes} minutes)
                      </p>
                    )}
                  </div>
                </li>
              ))}
          </ol>
        </div>
      )}

      {/* Prep Notes */}
      {recipe.prep_notes && (
        <div className={`p-6 rounded-lg border mb-6 ${
          isDark
            ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
            : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
        }`}>
          <h2 className={`text-xl font-semibold mb-3 ${
            isDark ? 'text-gruvbox-dark-yellow-bright' : 'text-gruvbox-light-yellow-bright'
          }`}>
            Prep Notes
          </h2>
          <p className={`whitespace-pre-wrap ${
            isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
          }`}>
            {recipe.prep_notes}
          </p>
        </div>
      )}

      {/* Postmortem Notes */}
      {recipe.postmortem_notes && (
        <div className={`p-6 rounded-lg border mb-6 ${
          isDark
            ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
            : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
        }`}>
          <h2 className={`text-xl font-semibold mb-3 ${
            isDark ? 'text-gruvbox-dark-purple-bright' : 'text-gruvbox-light-purple-bright'
          }`}>
            Postmortem Notes
          </h2>
          <p className={`whitespace-pre-wrap ${
            isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
          }`}>
            {recipe.postmortem_notes}
          </p>
        </div>
      )}


      <RetireRecipeModal
        recipe={recipe}
        isOpen={retireModal}
        onClose={() => setRetireModal(false)}
        onConfirm={handleRetireConfirm}
      />

      {/* Re-import Confirmation Modal */}
      {reimportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={`${
            isDark ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray' : 'bg-gruvbox-light-bg1 border-gruvbox-light-gray'
          } border rounded-lg p-6 max-w-lg w-full`}>
            <h2 className={`text-xl font-bold mb-4 ${
              isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
            }`}>
              Re-import Recipe from Source?
            </h2>
            <p className={`mb-4 ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
              This will fetch fresh data from the source URL and update:
            </p>
            <ul className={`mb-4 list-disc list-inside space-y-1 ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
              <li>Recipe name</li>
              <li>Description</li>
              <li>Prep and cook times</li>
              <li>All ingredients (replaces existing)</li>
              <li>All instructions (replaces existing)</li>
            </ul>
            <div className={`mb-4 p-3 rounded ${
              isDark ? 'bg-gruvbox-dark-yellow text-gruvbox-dark-bg' : 'bg-gruvbox-light-yellow text-gruvbox-light-bg'
            }`}>
              <p className="text-sm font-semibold">
                ⚠️ Warning: Any manual edits to ingredients or instructions will be lost.
              </p>
              <p className="text-sm mt-1">
                Your prep notes and postmortem notes will be preserved.
              </p>
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setReimportModal(false)}
                disabled={reimporting}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright text-gruvbox-dark-fg'
                    : 'bg-gruvbox-light-gray hover:bg-gruvbox-light-gray-bright text-gruvbox-light-fg'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={handleReimportConfirm}
                disabled={reimporting}
                className={`px-4 py-2 rounded font-semibold transition ${
                  isDark
                    ? 'bg-gruvbox-dark-aqua hover:bg-gruvbox-dark-aqua-bright text-gruvbox-dark-bg disabled:opacity-50'
                    : 'bg-gruvbox-light-aqua hover:bg-gruvbox-light-aqua-bright text-gruvbox-light-bg disabled:opacity-50'
                }`}
              >
                {reimporting ? 'Re-importing...' : 'Re-import Recipe'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecipeDetail;
