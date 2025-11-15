import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { mealPlanAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';

const MealPlanList = () => {
  const { isDark } = useTheme();
  const [searchParams] = useSearchParams();
  const sequenceId = searchParams.get('sequence_id');

  const [mealPlans, setMealPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [advancing, setAdvancing] = useState(false);

  useEffect(() => {
    loadMealPlans();
  }, []);

  const loadMealPlans = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await mealPlanAPI.list(50);
      setMealPlans(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load meal plans');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const handleStartWeek = async () => {
    // Get sequence ID from URL or latest meal plan
    let targetSequenceId = sequenceId;
    if (!targetSequenceId && mealPlans.length > 0) {
      targetSequenceId = mealPlans[0].schedule_sequence_id;
    }

    if (!targetSequenceId) {
      setError('No schedule found. Create a schedule first.');
      return;
    }

    if (!confirm('Start a new week? This will create a new meal plan instance.')) {
      return;
    }

    try {
      setAdvancing(true);
      setError(null);
      await mealPlanAPI.advanceWeek(targetSequenceId);
      await loadMealPlans();
      alert('New week started successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start new week');
    } finally {
      setAdvancing(false);
    }
  };

  if (loading) {
    return (
      <div className={`p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Loading meal plans...
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

  return (
    <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className={`text-3xl font-bold ${
            isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
          }`}>
            Meal Plan History
          </h1>
          <div className="flex gap-3">
            <button
              onClick={handleStartWeek}
              disabled={advancing || mealPlans.length === 0}
              className={`px-4 py-2 rounded font-semibold transition ${
                advancing || mealPlans.length === 0
                  ? isDark
                    ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                    : 'bg-gruvbox-light-gray cursor-not-allowed'
                  : isDark
                    ? 'bg-gruvbox-dark-yellow hover:bg-gruvbox-dark-yellow-bright'
                    : 'bg-gruvbox-light-yellow hover:bg-gruvbox-light-yellow-bright'
              }`}
            >
              {advancing ? 'Starting...' : 'Start New Week'}
            </button>
            {sequenceId && (
              <Link
                to={`/meal-plans/current?sequence_id=${sequenceId}`}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                    : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
                }`}
              >
                View Current Week
              </Link>
            )}
          </div>
        </div>

        {mealPlans.length === 0 ? (
          <div className={`text-center p-8 border-2 border-dashed rounded ${
            isDark ? 'border-gruvbox-dark-gray text-gruvbox-dark-gray' : 'border-gruvbox-light-gray text-gruvbox-light-gray'
          }`}>
            <p className="mb-4">No meal plan instances yet</p>
            <Link
              to="/schedules"
              className={`inline-block px-4 py-2 rounded transition ${
                isDark
                  ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                  : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
              }`}
            >
              Set up a Schedule
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {mealPlans.map((mealPlan) => (
              <Link
                key={mealPlan.id}
                to={`/meal-plans/${mealPlan.id}`}
                className={`block p-6 rounded border-2 transition ${
                  isDark
                    ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray hover:border-gruvbox-dark-orange'
                    : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray hover:border-gruvbox-light-orange'
                }`}
              >
                <div className={`text-sm mb-2 ${
                  isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                }`}>
                  {formatDate(mealPlan.instance_start_date)}
                </div>
                <div className={`text-xs ${
                  isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                }`}>
                  Click to view details
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MealPlanList;
