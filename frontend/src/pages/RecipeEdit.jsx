import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { recipeAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import RecipeForm from '../components/RecipeForm';

const RecipeEdit = () => {
  const { id } = useParams();
  const { isDark } = useTheme();
  const [recipe, setRecipe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  return <RecipeForm recipeId={id} initialData={recipe} />;
};

export default RecipeEdit;
