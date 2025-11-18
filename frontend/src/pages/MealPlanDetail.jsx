import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { mealPlanAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';

const MealPlanDetail = () => {
  const { isDark } = useTheme();
  const { id } = useParams();
  const navigate = useNavigate();

  const [mealPlan, setMealPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadMealPlan();
  }, [id]);

  const loadMealPlan = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await mealPlanAPI.get(id);
      setMealPlan(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load meal plan');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getDayName = (dateString) => {
    // Parse date as local time to avoid timezone shifts
    const [year, month, day] = dateString.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString('en-US', { weekday: 'long' });
  };

  const groupAssignmentsByDate = (assignments) => {
    const grouped = {};
    assignments?.forEach(assignment => {
      const dateKey = assignment.date;
      if (!grouped[dateKey]) {
        grouped[dateKey] = [];
      }
      grouped[dateKey].push(assignment);
    });
    return grouped;
  };

  if (loading) {
    return (
      <div className={`p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Loading meal plan...
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
        <button
          onClick={() => navigate('/meal-plans')}
          className={`mt-4 px-4 py-2 rounded ${
            isDark
              ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright'
              : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright'
          }`}
        >
          Back to History
        </button>
      </div>
    );
  }

  if (!mealPlan) {
    return null;
  }

  const assignmentsByDate = groupAssignmentsByDate(mealPlan.assignments);
  const dates = Object.keys(assignmentsByDate).sort();

  return (
    <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <button
              onClick={() => navigate('/meal-plans')}
              className={`mb-2 text-sm ${
                isDark ? 'text-gruvbox-dark-blue hover:text-gruvbox-dark-blue-bright'
                : 'text-gruvbox-light-blue hover:text-gruvbox-light-blue-bright'
              }`}
            >
              ← Back to History
            </button>
            <h1 className={`text-3xl font-bold ${
              isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
            }`}>
              {mealPlan.theme_name || 'Meal Plan'}
            </h1>
            <p className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
              Week starting {formatDate(mealPlan.instance_start_date)}
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {dates.map(date => {
            const dayAssignments = assignmentsByDate[date];
            return (
              <div
                key={date}
                className={`p-4 rounded border-2 ${
                  isDark
                    ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
                    : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
                }`}
              >
                <h3 className={`font-semibold mb-3 ${
                  isDark ? 'text-gruvbox-dark-yellow-bright' : 'text-gruvbox-light-yellow-bright'
                }`}>
                  {getDayName(date)} - {(() => {
                    const [year, month, day] = date.split('-').map(Number);
                    const d = new Date(year, month - 1, day);
                    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                  })()}
                </h3>

                {dayAssignments.length === 0 ? (
                  <div className={`text-sm italic ${
                    isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                  }`}>
                    No assignments
                  </div>
                ) : (
                  <div className="space-y-2">
                    {dayAssignments.map((assignment, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded ${
                          isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`px-2 py-1 rounded text-xs font-semibold ${
                            assignment.action === 'cook'
                              ? isDark
                                ? 'bg-gruvbox-dark-orange text-gruvbox-dark-bg'
                                : 'bg-gruvbox-light-orange text-gruvbox-light-bg'
                              : assignment.action === 'shop'
                                ? isDark
                                  ? 'bg-gruvbox-dark-blue text-gruvbox-dark-bg'
                                  : 'bg-gruvbox-light-blue text-gruvbox-light-bg'
                                : isDark
                                  ? 'bg-gruvbox-dark-gray text-gruvbox-dark-bg'
                                  : 'bg-gruvbox-light-gray text-gruvbox-light-bg'
                          }`}>
                            {assignment.action}
                          </div>
                          <div className="flex-1">
                            {assignment.recipe_name ? (
                              <div className={`font-medium ${
                                isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                              }`}>
                                {assignment.recipe_name}
                              </div>
                            ) : (
                              <div className={`text-sm italic ${
                                isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                              }`}>
                                No recipe assigned
                              </div>
                            )}
                          </div>
                          {assignment.is_modified && (
                            <div className={`text-xs px-2 py-1 rounded ${
                              isDark
                                ? 'bg-gruvbox-dark-purple text-gruvbox-dark-bg'
                                : 'bg-gruvbox-light-purple text-gruvbox-light-bg'
                            }`}>
                              Modified
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default MealPlanDetail;
