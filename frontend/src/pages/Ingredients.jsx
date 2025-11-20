import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { ingredientAPI } from '../services/api';
import IngredientDetail from '../components/IngredientDetail';
import MapIngredientDialog from '../components/MapIngredientDialog';
import Toast from '../components/Toast';
import ConfirmDialog from '../components/ConfirmDialog';

const Ingredients = () => {
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  // Check if we're returning from a recipe edit with tab state
  const initialTab = location.state?.tab || 'all';

  const [ingredients, setIngredients] = useState([]);
  const [unmappedIngredients, setUnmappedIngredients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedIngredient, setSelectedIngredient] = useState(null);
  const [showMapDialog, setShowMapDialog] = useState(false);
  const [unmappedToMap, setUnmappedToMap] = useState(null);
  const [activeTab, setActiveTab] = useState(initialTab);
  const [autoMapping, setAutoMapping] = useState(false);
  const [toast, setToast] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState(null);
  const [showUnused, setShowUnused] = useState(false);

  const categories = ['dairy', 'produce', 'meat', 'pantry', 'spices', 'seafood', 'condiments', 'baking', 'uncategorized'];

  const loadIngredients = async () => {
    try {
      setLoading(true);
      setError(null);
      // Pass null for uncategorized, actual category value otherwise
      const categoryFilter = selectedCategory === 'uncategorized' ? null : selectedCategory;
      const response = await ingredientAPI.listIngredients(searchTerm, categoryFilter);

      // Filter on frontend for uncategorized since backend doesn't have a null filter
      let filteredIngredients = response.data;
      if (selectedCategory === 'uncategorized') {
        filteredIngredients = response.data.filter(ing => !ing.category);
      }

      setIngredients(filteredIngredients);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load ingredients');
    } finally {
      setLoading(false);
    }
  };

  const loadUnmapped = async () => {
    try {
      const response = await ingredientAPI.listUnmapped();
      setUnmappedIngredients(response.data);
    } catch (err) {
      console.error('Failed to load unmapped ingredients:', err);
    }
  };

  useEffect(() => {
    loadIngredients();
    loadUnmapped();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, selectedCategory]);

  // Update active tab when returning from recipe edit
  useEffect(() => {
    if (location.state?.tab) {
      setActiveTab(location.state.tab);
    }
  }, [location.state?.tab]);

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleCategoryFilter = (category) => {
    setSelectedCategory(selectedCategory === category ? '' : category);
  };

  const handleIngredientClick = (ingredient) => {
    setSelectedIngredient(ingredient);
  };

  const handleMapClick = (unmapped) => {
    setUnmappedToMap(unmapped);
    setShowMapDialog(true);
  };

  const handleMappingComplete = () => {
    setShowMapDialog(false);
    setUnmappedToMap(null);
    loadIngredients();
    loadUnmapped();
  };

  const handleIngredientUpdated = () => {
    setSelectedIngredient(null);
    loadIngredients();
  };

  const handleAutoMap = () => {
    setConfirmDialog({
      message: 'Auto-map all ingredients used in 2+ recipes? They will be created with no category.',
      onConfirm: async () => {
        setConfirmDialog(null);
        setAutoMapping(true);
        try {
          const response = await ingredientAPI.autoMapCommon(2);
          setToast({
            message: `Success! Created ${response.data.ingredients_created} ingredients and updated ${response.data.recipe_ingredients_updated} recipe ingredients.`,
            type: 'success',
          });
          loadIngredients();
          loadUnmapped();
        } catch (err) {
          setToast({
            message: err.response?.data?.detail || 'Failed to auto-map ingredients',
            type: 'error',
          });
        } finally {
          setAutoMapping(false);
        }
      },
      onCancel: () => setConfirmDialog(null),
    });
  };

  if (selectedIngredient) {
    return (
      <IngredientDetail
        ingredient={selectedIngredient}
        onClose={() => setSelectedIngredient(null)}
        onUpdate={handleIngredientUpdated}
      />
    );
  }

  return (
    <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className={`text-3xl font-bold mb-2 ${
            isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
          }`}>
            Ingredients
          </h1>
          <p className={`${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
            Manage common ingredients and map unmapped recipe ingredients
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b ${isDark ? 'border-gruvbox-dark-gray' : 'border-gruvbox-light-gray'}">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-4 py-2 -mb-px border-b-2 transition ${
              activeTab === 'all'
                ? `${isDark ? 'border-gruvbox-dark-orange-bright text-gruvbox-dark-orange-bright' : 'border-gruvbox-light-orange-bright text-gruvbox-light-orange-bright'}`
                : `border-transparent ${isDark ? 'text-gruvbox-dark-gray hover:text-gruvbox-dark-fg' : 'text-gruvbox-light-gray hover:text-gruvbox-light-fg'}`
            }`}
          >
            All Ingredients ({showUnused ? ingredients.length : ingredients.filter(i => i.recipe_count > 0).length})
          </button>
          <button
            onClick={() => setActiveTab('unmapped')}
            className={`px-4 py-2 -mb-px border-b-2 transition ${
              activeTab === 'unmapped'
                ? `${isDark ? 'border-gruvbox-dark-orange-bright text-gruvbox-dark-orange-bright' : 'border-gruvbox-light-orange-bright text-gruvbox-light-orange-bright'}`
                : `border-transparent ${isDark ? 'text-gruvbox-dark-gray hover:text-gruvbox-dark-fg' : 'text-gruvbox-light-gray hover:text-gruvbox-light-fg'}`
            }`}
          >
            Unmapped ({unmappedIngredients.length})
          </button>
        </div>

        {/* All Ingredients Tab */}
        {activeTab === 'all' && (
          <>
            {/* Search and Filters */}
            <div className="mb-6 space-y-4">
              <div className="flex gap-4 items-center">
                <input
                  type="text"
                  placeholder="Search ingredients..."
                  value={searchTerm}
                  onChange={handleSearch}
                  className={`flex-1 px-4 py-2 rounded border ${
                    isDark
                      ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray text-gruvbox-dark-fg placeholder-gruvbox-dark-gray'
                      : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray text-gruvbox-light-fg placeholder-gruvbox-light-gray'
                  }`}
                />

                {/* Toggle for showing unused ingredients */}
                <label className="flex items-center gap-2 cursor-pointer whitespace-nowrap">
                  <input
                    type="checkbox"
                    checked={showUnused}
                    onChange={(e) => setShowUnused(e.target.checked)}
                    className="w-4 h-4 cursor-pointer"
                  />
                  <span className={`text-sm ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
                    Show unused
                  </span>
                </label>
              </div>

              {/* Category filters */}
              <div className="flex flex-wrap gap-2">
                {categories.map(category => (
                  <button
                    key={category}
                    onClick={() => handleCategoryFilter(category)}
                    className={`px-3 py-1 rounded transition ${
                      selectedCategory === category
                        ? `${isDark ? 'bg-gruvbox-dark-orange text-gruvbox-dark-bg' : 'bg-gruvbox-light-orange text-gruvbox-light-bg'}`
                        : `${isDark ? 'bg-gruvbox-dark-bg-soft hover:bg-gruvbox-dark-bg-hard' : 'bg-gruvbox-light-bg-soft hover:bg-gruvbox-light-bg-hard'}`
                    }`}
                  >
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Ingredients List */}
            {loading ? (
              <div className={`text-center py-8 ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                Loading ingredients...
              </div>
            ) : error ? (
              <div className={`p-4 rounded ${
                isDark ? 'bg-gruvbox-dark-red text-gruvbox-dark-bg' : 'bg-gruvbox-light-red text-gruvbox-light-bg'
              }`}>
                {error}
              </div>
            ) : (() => {
              const filteredIngredients = ingredients.filter(ingredient => showUnused || ingredient.recipe_count > 0);
              return filteredIngredients.length === 0 ? (
                <div className={`text-center py-8 border-2 border-dashed rounded ${
                  isDark ? 'border-gruvbox-dark-gray text-gruvbox-dark-gray' : 'border-gruvbox-light-gray text-gruvbox-light-gray'
                }`}>
                  {ingredients.length === 0 ? 'No ingredients found' : 'No used ingredients found. Toggle "Show unused" to see all ingredients.'}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredIngredients.map(ingredient => (
                  <div
                    key={ingredient.id}
                    onClick={() => handleIngredientClick(ingredient)}
                    className={`p-4 rounded border cursor-pointer transition ${
                      isDark
                        ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray hover:border-gruvbox-dark-orange'
                        : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray hover:border-gruvbox-light-orange'
                    }`}
                  >
                    <h3 className={`text-lg font-semibold mb-1 ${
                      isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                    }`}>
                      {ingredient.name}
                    </h3>
                    {ingredient.category && (
                      <span className={`inline-block px-2 py-1 rounded text-xs mb-2 ${
                        isDark ? 'bg-gruvbox-dark-bg-hard text-gruvbox-dark-gray' : 'bg-gruvbox-light-bg-hard text-gruvbox-light-gray'
                      }`}>
                        {ingredient.category}
                      </span>
                    )}
                    {ingredient.recipes && ingredient.recipes.length > 0 ? (
                      <div className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                        Used in:
                        <div className="mt-1 space-y-1">
                          {ingredient.recipes.map(recipe => (
                            <button
                              key={recipe.id}
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/recipes/${recipe.id}/edit`, {
                                  state: {
                                    returnTo: '/ingredients',
                                    tab: activeTab
                                  }
                                });
                              }}
                              className={`block text-left hover:underline ${
                                isDark ? 'text-gruvbox-dark-blue hover:text-gruvbox-dark-blue-bright' : 'text-gruvbox-light-blue hover:text-gruvbox-light-blue-bright'
                              }`}
                            >
                              • {recipe.name}
                            </button>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <p className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                        Not used in any recipes
                      </p>
                    )}
                  </div>
                ))}
              </div>
              );
            })()}
          </>
        )}

        {/* Unmapped Ingredients Tab */}
        {activeTab === 'unmapped' && (
          <div className="space-y-4">
            {unmappedIngredients.length > 0 && (
              <div className="flex justify-end">
                <button
                  onClick={handleAutoMap}
                  disabled={autoMapping}
                  className={`px-4 py-2 rounded transition ${
                    autoMapping
                      ? `${isDark ? 'bg-gruvbox-dark-bg-hard text-gruvbox-dark-gray' : 'bg-gruvbox-light-bg-hard text-gruvbox-light-gray'} cursor-not-allowed`
                      : `${isDark ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg' : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg'}`
                  }`}
                >
                  {autoMapping ? 'Auto-mapping...' : 'Auto-map Common Ingredients (2+ recipes)'}
                </button>
              </div>
            )}
            {unmappedIngredients.length === 0 ? (
              <div className={`text-center py-8 border-2 border-dashed rounded ${
                isDark ? 'border-gruvbox-dark-gray text-gruvbox-dark-gray' : 'border-gruvbox-light-gray text-gruvbox-light-gray'
              }`}>
                All ingredients are mapped!
              </div>
            ) : (
              unmappedIngredients.map((unmapped, index) => (
                <div
                  key={index}
                  className={`p-4 rounded border flex justify-between items-start ${
                    isDark
                      ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
                      : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
                  }`}
                >
                  <div className="flex-1">
                    <h3 className={`text-lg font-semibold ${
                      isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                    }`}>
                      {unmapped.ingredient_name}
                    </h3>
                    {unmapped.recipes && unmapped.recipes.length > 0 ? (
                      <div className={`text-sm mt-1 ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                        Used in:
                        <div className="mt-1 space-y-1">
                          {unmapped.recipes.map(recipe => (
                            <button
                              key={recipe.id}
                              onClick={() => {
                                navigate(`/recipes/${recipe.id}/edit`, {
                                  state: {
                                    returnTo: '/ingredients',
                                    tab: activeTab
                                  }
                                });
                              }}
                              className={`block text-left hover:underline ${
                                isDark ? 'text-gruvbox-dark-blue hover:text-gruvbox-dark-blue-bright' : 'text-gruvbox-light-blue hover:text-gruvbox-light-blue-bright'
                              }`}
                            >
                              • {recipe.name}
                            </button>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <p className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                        Used in {unmapped.recipe_count} recipe{unmapped.recipe_count !== 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => handleMapClick(unmapped)}
                    className={`px-4 py-2 rounded transition ml-4 ${
                      isDark
                        ? 'bg-gruvbox-dark-orange hover:bg-gruvbox-dark-orange-bright text-gruvbox-dark-bg'
                        : 'bg-gruvbox-light-orange hover:bg-gruvbox-light-orange-bright text-gruvbox-light-bg'
                    }`}
                  >
                    Map Ingredient
                  </button>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Map Ingredient Dialog */}
      {showMapDialog && unmappedToMap && (
        <MapIngredientDialog
          unmappedIngredient={unmappedToMap}
          onClose={() => {
            setShowMapDialog(false);
            setUnmappedToMap(null);
          }}
          onComplete={handleMappingComplete}
        />
      )}

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

export default Ingredients;
