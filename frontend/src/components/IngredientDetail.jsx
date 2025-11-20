import { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { ingredientAPI } from '../services/api';
import Toast from './Toast';
import ConfirmDialog from './ConfirmDialog';

const IngredientDetail = ({ ingredient, onClose, onUpdate }) => {
  const { isDark } = useTheme();
  const [ingredientData, setIngredientData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(ingredient.name);
  const [editCategory, setEditCategory] = useState(ingredient.category || '');
  const [toast, setToast] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState(null);

  const categories = ['dairy', 'produce', 'meat', 'pantry', 'spices', 'seafood', 'condiments', 'baking'];

  const loadIngredientDetail = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await ingredientAPI.getIngredient(ingredient.id);
      setIngredientData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load ingredient details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIngredientDetail();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ingredient.id]);

  const handleSave = async () => {
    try {
      await ingredientAPI.updateIngredient(ingredient.id, {
        name: editName,
        category: editCategory || null,
      });
      setIsEditing(false);
      loadIngredientDetail();
      onUpdate();
    } catch (err) {
      setToast({
        message: err.response?.data?.detail || 'Failed to update ingredient',
        type: 'error',
      });
    }
  };

  const handleDelete = () => {
    setConfirmDialog({
      message: `Delete "${ingredient.name}"? This can only be done if no recipes use this ingredient.`,
      onConfirm: async () => {
        setConfirmDialog(null);
        try {
          await ingredientAPI.deleteIngredient(ingredient.id);
          onUpdate();
        } catch (err) {
          if (err.response?.status === 409) {
            setToast({
              message: 'Cannot delete ingredient that is used in recipes',
              type: 'error',
            });
          } else {
            setToast({
              message: err.response?.data?.detail || 'Failed to delete ingredient',
              type: 'error',
            });
          }
        }
      },
      onCancel: () => setConfirmDialog(null),
    });
  };

  const handleDeleteAlias = async (alias) => {
    try {
      await ingredientAPI.deleteAlias(ingredient.id, alias.id);
      setToast({
        message: `Alias "${alias.alias}" removed`,
        type: 'success',
      });
      loadIngredientDetail();
    } catch (err) {
      setToast({
        message: err.response?.data?.detail || 'Failed to delete alias',
        type: 'error',
      });
    }
  };

  if (loading) {
    return (
      <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Loading...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
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
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div className="flex-1">
            <button
              onClick={onClose}
              className={`px-3 py-1 rounded mb-4 transition ${
                isDark
                  ? 'bg-gruvbox-dark-bg-soft hover:bg-gruvbox-dark-bg-hard'
                  : 'bg-gruvbox-light-bg-soft hover:bg-gruvbox-light-bg-hard'
              }`}
            >
              ← Back
            </button>

            {isEditing ? (
              <div className="space-y-4">
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className={`w-full text-3xl font-bold px-4 py-2 rounded border ${
                    isDark
                      ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray text-gruvbox-dark-orange-bright'
                      : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray text-gruvbox-light-orange-bright'
                  }`}
                />
                <select
                  value={editCategory}
                  onChange={(e) => setEditCategory(e.target.value)}
                  className={`px-4 py-2 rounded border ${
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
                <div className="flex gap-2">
                  <button
                    onClick={handleSave}
                    className={`px-4 py-2 rounded transition ${
                      isDark
                        ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg'
                        : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg'
                    }`}
                  >
                    Save
                  </button>
                  <button
                    onClick={() => {
                      setIsEditing(false);
                      setEditName(ingredientData.name);
                      setEditCategory(ingredientData.category || '');
                    }}
                    className={`px-4 py-2 rounded transition ${
                      isDark
                        ? 'bg-gruvbox-dark-bg-soft hover:bg-gruvbox-dark-bg-hard'
                        : 'bg-gruvbox-light-bg-soft hover:bg-gruvbox-light-bg-hard'
                    }`}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <h1 className={`text-3xl font-bold mb-2 ${
                  isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
                }`}>
                  {ingredientData.name}
                </h1>
                {ingredientData.category && (
                  <span className={`inline-block px-3 py-1 rounded text-sm ${
                    isDark ? 'bg-gruvbox-dark-bg-hard text-gruvbox-dark-gray' : 'bg-gruvbox-light-bg-hard text-gruvbox-light-gray'
                  }`}>
                    {ingredientData.category}
                  </span>
                )}
                <p className={`mt-2 ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                  Used in {ingredientData.recipe_count} recipe{ingredientData.recipe_count !== 1 ? 's' : ''}
                </p>
              </>
            )}
          </div>

          {!isEditing && (
            <div className="flex gap-2">
              <button
                onClick={() => setIsEditing(true)}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright text-gruvbox-dark-bg'
                    : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright text-gruvbox-light-bg'
                }`}
              >
                Edit
              </button>
              <button
                onClick={handleDelete}
                disabled={ingredientData.recipe_count > 0}
                className={`px-4 py-2 rounded transition ${
                  ingredientData.recipe_count > 0
                    ? `${isDark ? 'bg-gruvbox-dark-bg-hard text-gruvbox-dark-gray' : 'bg-gruvbox-light-bg-hard text-gruvbox-light-gray'} cursor-not-allowed`
                    : `${isDark ? 'bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright text-gruvbox-dark-bg' : 'bg-gruvbox-light-red hover:bg-gruvbox-light-red-bright text-gruvbox-light-bg'}`
                }`}
              >
                Delete
              </button>
            </div>
          )}
        </div>

        {/* Aliases */}
        <div className={`p-6 rounded-lg border mb-6 ${
          isDark
            ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
            : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
        }`}>
          <h2 className={`text-xl font-bold mb-4 ${
            isDark ? 'text-gruvbox-dark-green-bright' : 'text-gruvbox-light-green-bright'
          }`}>
            Aliases
          </h2>
          {ingredientData.aliases && ingredientData.aliases.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {ingredientData.aliases.map(alias => (
                <div
                  key={alias.id}
                  className={`flex items-center gap-2 px-3 py-1 rounded ${
                    isDark ? 'bg-gruvbox-dark-bg-hard text-gruvbox-dark-fg' : 'bg-gruvbox-light-bg-hard text-gruvbox-light-fg'
                  }`}
                >
                  <span>{alias.alias}</span>
                  <button
                    onClick={() => handleDeleteAlias(alias)}
                    className={`text-xs hover:opacity-70 transition ${
                      isDark ? 'text-gruvbox-dark-red' : 'text-gruvbox-light-red'
                    }`}
                    title="Remove alias"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className={`${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
              No aliases defined
            </p>
          )}
        </div>

        {/* Info */}
        <div className={`p-4 rounded border text-sm ${
          isDark
            ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray text-gruvbox-dark-gray'
            : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray text-gruvbox-light-gray'
        }`}>
          <p>Created: {new Date(ingredientData.created_at).toLocaleDateString()}</p>
          <p>Updated: {new Date(ingredientData.updated_at).toLocaleDateString()}</p>
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

      {/* Confirm Dialog */}
      {confirmDialog && (
        <ConfirmDialog
          message={confirmDialog.message}
          onConfirm={confirmDialog.onConfirm}
          onCancel={confirmDialog.onCancel}
        />
      )}
    </div>
  );
};

export default IngredientDetail;
