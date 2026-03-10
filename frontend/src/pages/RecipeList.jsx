import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { recipeAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { usePageActions } from '../context/MenuBarContext';
import RecipeImportModal from '../components/RecipeImportModal';
import Toast from '../components/Toast';

const RecipeList = () => {
  const { isDark } = useTheme();
  const [index, setIndex] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [includeRetired, setIncludeRetired] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSection, setActiveSection] = useState('');
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [toast, setToast] = useState(null);
  const navigate = useNavigate();

  const fetchIndex = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await recipeAPI.get(`index?include_retired=${includeRetired}`);
      setIndex(response.data.index || {});
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load recipe index');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIndex();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [includeRetired]);

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
      fetchIndex(); // Refresh index
    } catch (err) {
      setToast({
        message: err.response?.data?.detail || 'Failed to import recipe',
        type: 'error',
      });
    } finally {
      event.target.value = ''; // Reset file input
    }
  };

  // Register page actions
  usePageActions([
    {
      id: 'show-retired',
      label: 'Show retired',
      variant: 'toggle',
      checked: includeRetired,
      onClick: (e) => setIncludeRetired(e.target.checked),
      color: 'gray',
    },
    { id: 'import-url', label: 'Import from URL', onClick: () => setImportModalOpen(true), color: 'blue' },
    {
      id: 'import-json',
      label: 'Import JSON',
      variant: 'file-input',
      accept: '.json',
      onChange: handleJSONImport,
      color: 'aqua',
    },
    { id: 'new-recipe', label: '+ New Recipe', onClick: () => navigate('/recipes/new'), color: 'green' },
  ], [includeRetired]);

  // Filter index based on search query
  const filterIndex = (indexData, query) => {
    if (!query.trim()) return indexData;

    const lowerQuery = query.toLowerCase();
    const filtered = {};

    Object.entries(indexData).forEach(([letter, entries]) => {
      const filteredEntries = entries.filter((entry) => {
        // Check if entry name matches
        if (entry.name.toLowerCase().includes(lowerQuery)) {
          return true;
        }

        // For ingredient entries, check if any recipe name matches
        if (entry.type === 'ingredient' && entry.recipes) {
          return entry.recipes.some((recipe) =>
            recipe.name.toLowerCase().includes(lowerQuery)
          );
        }

        return false;
      });

      // For ingredient entries, filter recipe list to only matching recipes
      const processedEntries = filteredEntries.map((entry) => {
        if (entry.type === 'ingredient' && entry.recipes) {
          // If ingredient name matches, show all recipes
          if (entry.name.toLowerCase().includes(lowerQuery)) {
            return entry;
          }

          // Otherwise, filter recipes
          return {
            ...entry,
            recipes: entry.recipes.filter((recipe) =>
              recipe.name.toLowerCase().includes(lowerQuery)
            ),
          };
        }
        return entry;
      });

      if (processedEntries.length > 0) {
        filtered[letter] = processedEntries;
      }
    });

    return filtered;
  };

  const filteredIndex = filterIndex(index, searchQuery);
  const allLetters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ#'.split('');
  const availableLetters = Object.keys(filteredIndex);

  // Scroll spy: Track which section is currently visible
  useEffect(() => {
    const handleScroll = () => {
      const sections = allLetters
        .map((letter) => ({
          letter,
          element: document.getElementById(`section-${letter}`),
        }))
        .filter((s) => s.element);

      // Find the section that's currently most visible in the viewport
      const currentSection = sections.find((section) => {
        const rect = section.element.getBoundingClientRect();
        // Section is considered active if its top is in the upper half of viewport
        return rect.top >= 0 && rect.top <= window.innerHeight / 2;
      });

      if (currentSection) {
        setActiveSection(currentSection.letter);
      } else {
        // If no section is in the upper half, find the one closest to top
        const closestSection = sections.reduce((closest, section) => {
          const rect = section.element.getBoundingClientRect();
          if (!closest) return section;
          
          const closestRect = closest.element.getBoundingClientRect();
          return Math.abs(rect.top) < Math.abs(closestRect.top) ? section : closest;
        }, null);

        if (closestSection) {
          setActiveSection(closestSection.letter);
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Initial check

    return () => window.removeEventListener('scroll', handleScroll);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filteredIndex]);

  const scrollToLetter = (letter) => {
    const element = document.getElementById(`section-${letter}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  if (loading) {
    return (
      <div className={`p-8 flex items-center justify-center ${
        isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'
      }`}>
        <div className={`text-xl ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
          Loading recipe index...
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

  const hasEntries = availableLetters.length > 0;

  return (
    <div className={`p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      {/* Header */}
      <h1 className={`text-3xl font-bold mb-6 ${
        isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
      }`}>
        Recipe Index
      </h1>

      {/* Search Box */}
      {Object.keys(index).length > 0 && (
        <div className="mb-6">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search recipes or ingredients..."
            className={`w-full p-3 rounded border ${
              isDark
                ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg placeholder-gruvbox-dark-gray focus:border-gruvbox-dark-orange-bright'
                : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg placeholder-gruvbox-light-gray focus:border-gruvbox-light-orange-bright'
            } focus:outline-none`}
          />
        </div>
      )}

      {!hasEntries && searchQuery ? (
        <div className="text-center py-12">
          <p className={`text-xl mb-4 ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
            No recipes match "{searchQuery}"
          </p>
          <button
            onClick={() => setSearchQuery('')}
            className={`px-6 py-3 rounded font-semibold transition ${
              isDark
                ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright text-gruvbox-dark-bg'
                : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright text-gruvbox-light-bg'
            }`}
          >
            Clear search
          </button>
        </div>
      ) : !hasEntries ? (
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
        <>
          {/* Alphabet Navigation */}
          <div className={`sticky top-0 z-10 py-4 mb-6 border-b ${
            isDark 
              ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray'
              : 'bg-gruvbox-light-bg border-gruvbox-light-gray'
          }`}>
            <div className="flex flex-wrap gap-2 justify-center">
              {allLetters.map((letter) => {
                const isAvailable = availableLetters.includes(letter);
                const isActive = letter === activeSection;
                return (
                  <button
                    key={letter}
                    onClick={() => isAvailable && scrollToLetter(letter)}
                    disabled={!isAvailable}
                    className={`px-3 py-1 rounded font-semibold transition ${
                      isAvailable
                        ? isActive
                          ? isDark
                            ? 'bg-gruvbox-dark-orange text-gruvbox-dark-bg ring-2 ring-gruvbox-dark-orange-bright cursor-pointer'
                            : 'bg-gruvbox-light-orange text-gruvbox-light-bg ring-2 ring-gruvbox-light-orange-bright cursor-pointer'
                          : isDark
                            ? 'bg-gruvbox-dark-blue text-gruvbox-dark-bg hover:bg-gruvbox-dark-blue-bright cursor-pointer'
                            : 'bg-gruvbox-light-blue text-gruvbox-light-bg hover:bg-gruvbox-light-blue-bright cursor-pointer'
                        : isDark
                          ? 'bg-gruvbox-dark-bg-hard text-gruvbox-dark-gray cursor-not-allowed opacity-40'
                          : 'bg-gruvbox-light-bg-hard text-gruvbox-light-gray cursor-not-allowed opacity-40'
                    }`}
                  >
                    {letter}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Index Content */}
          <div className="space-y-8">
            {allLetters.map((letter) => {
              const entries = filteredIndex[letter];
              if (!entries || entries.length === 0) return null;

              return (
                <div key={letter} id={`section-${letter}`} className="scroll-mt-24">
                  {/* Letter Header */}
                  <h2 className={`text-3xl font-bold mb-4 pb-2 border-b ${
                    isDark
                      ? 'text-gruvbox-dark-orange-bright border-gruvbox-dark-gray'
                      : 'text-gruvbox-light-orange-bright border-gruvbox-light-gray'
                  }`}>
                    {letter}
                  </h2>

                  {/* Entries */}
                  <div className="space-y-4">
                    {entries.map((entry, index) => (
                      <div key={index}>
                        {entry.type === 'ingredient' ? (
                          /* Ingredient Entry */
                          <div>
                            <div className={`text-lg font-bold ${
                              isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                            }`}>
                              {entry.name}
                            </div>
                            <div className="ml-6 mt-1 space-y-1">
                              {entry.recipes && entry.recipes.map((recipe) => (
                                <div key={recipe.id}>
                                  <Link
                                    to={`/recipes/${recipe.id}`}
                                    className={`hover:underline ${
                                      isDark ? 'text-gruvbox-dark-blue-bright' : 'text-gruvbox-light-blue-bright'
                                    }`}
                                    title={recipe.name}
                                  >
                                    {recipe.sub_entry || recipe.name}
                                  </Link>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          /* Standalone Recipe Entry */
                          <div>
                            <Link
                              to={`/recipes/${entry.id}`}
                              className={`text-lg hover:underline ${
                                isDark ? 'text-gruvbox-dark-blue-bright' : 'text-gruvbox-light-blue-bright'
                              }`}
                            >
                              {entry.name}
                            </Link>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      <RecipeImportModal
        isOpen={importModalOpen}
        onClose={() => {
          setImportModalOpen(false);
          fetchIndex(); // Refresh index after import
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
