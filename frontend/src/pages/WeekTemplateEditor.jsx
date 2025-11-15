import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { scheduleAPI, recipeAPI, authAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

const WeekTemplateEditor = () => {
  const { sequenceId, weekId } = useParams();
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [week, setWeek] = useState(null);
  const [isNew, setIsNew] = useState(!weekId);
  const [themeName, setThemeName] = useState('');
  const [assignments, setAssignments] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [users, setUsers] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const defaultActions = ['cook', 'shop', 'takeout', 'rest', 'leftovers'];

  useEffect(() => {
    loadData();
  }, [weekId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load recipes (we'll need user list too, but for MVP we can use current user)
      const recipesRes = await recipeAPI.list();
      setRecipes(recipesRes.data || []);

      // For MVP, just use current user
      setUsers([user]);

      if (!isNew) {
        // Load existing week
        const weekRes = await scheduleAPI.getWeek(sequenceId, weekId);
        setWeek(weekRes.data);
        setThemeName(weekRes.data.theme_name);
        setAssignments(weekRes.data.day_assignments || []);
      } else {
        // Initialize empty assignments for all 7 days
        const emptyAssignments = dayNames.map((_, dayIndex) => ({
          day_of_week: dayIndex,
          assigned_user_id: user.id,
          action: 'cook',
          recipe_id: null,
          order: 0,
        }));
        setAssignments(emptyAssignments);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const updateAssignment = (dayIndex, field, value) => {
    const updated = [...assignments];
    const assignmentIndex = updated.findIndex(a => a.day_of_week === dayIndex);

    if (assignmentIndex >= 0) {
      updated[assignmentIndex] = {
        ...updated[assignmentIndex],
        [field]: value,
      };
    } else {
      updated.push({
        day_of_week: dayIndex,
        assigned_user_id: user.id,
        action: 'cook',
        recipe_id: null,
        order: 0,
        [field]: value,
      });
    }

    setAssignments(updated);
  };

  const getAssignmentForDay = (dayIndex) => {
    return assignments.find(a => a.day_of_week === dayIndex) || {
      day_of_week: dayIndex,
      assigned_user_id: user.id,
      action: 'cook',
      recipe_id: null,
      order: 0,
    };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      if (isNew) {
        // Create new week with assignments
        const payload = {
          theme_name: themeName,
          assignments: assignments.map(a => ({
            day_of_week: a.day_of_week,
            assigned_user_id: a.assigned_user_id,
            action: a.action,
            recipe_id: a.recipe_id || null,
            order: a.order || 0,
          })),
        };
        await scheduleAPI.createWeek(sequenceId, payload);
      } else {
        // Update theme name
        await scheduleAPI.updateWeek(sequenceId, weekId, { theme_name: themeName });

        // For existing weeks, we need to update/create assignments individually
        // This is a simplified version - in production you'd diff and update only changes
        for (const assignment of assignments) {
          if (assignment.id) {
            // Update existing assignment
            await scheduleAPI.updateAssignment(sequenceId, weekId, assignment.id, {
              day_of_week: assignment.day_of_week,
              assigned_user_id: assignment.assigned_user_id,
              action: assignment.action,
              recipe_id: assignment.recipe_id || null,
              order: assignment.order || 0,
            });
          } else {
            // Create new assignment
            await scheduleAPI.createAssignment(sequenceId, weekId, {
              day_of_week: assignment.day_of_week,
              assigned_user_id: assignment.assigned_user_id,
              action: assignment.action,
              recipe_id: assignment.recipe_id || null,
              order: assignment.order || 0,
            });
          }
        }
      }

      navigate(`/schedules/${sequenceId}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save week template');
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Loading...
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={() => navigate(`/schedules/${sequenceId}`)}
              className={`px-3 py-1 rounded transition ${
                isDark
                  ? 'bg-gruvbox-dark-bg-soft hover:bg-gruvbox-dark-bg-hard'
                  : 'bg-gruvbox-light-bg-soft hover:bg-gruvbox-light-bg-hard'
              }`}
            >
              ← Back
            </button>
            <h1 className={`text-3xl font-bold ${
              isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
            }`}>
              {isNew ? 'Create Week Template' : 'Edit Week Template'}
            </h1>
          </div>
        </div>

        {error && (
          <div className={`mb-4 p-4 rounded ${
            isDark ? 'bg-gruvbox-dark-red text-gruvbox-dark-bg' : 'bg-gruvbox-light-red text-gruvbox-light-bg'
          }`}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Theme Name */}
          <div className={`mb-6 p-4 rounded border ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
              : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
          }`}>
            <label className={`block mb-2 font-semibold ${
              isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
            }`}>
              Week Theme Name *
            </label>
            <input
              type="text"
              value={themeName}
              onChange={(e) => setThemeName(e.target.value)}
              required
              className={`w-full p-2 rounded border ${
                isDark
                  ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                  : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
              }`}
              placeholder="e.g., Italian Week, Comfort Foods, Quick & Easy"
            />
          </div>

          {/* Day Assignments Grid */}
          <div className={`mb-6 p-6 rounded border ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
              : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
          }`}>
            <h2 className={`text-xl font-bold mb-4 ${
              isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
            }`}>
              Daily Assignments
            </h2>

            <div className="space-y-4">
              {dayNames.map((dayName, dayIndex) => {
                const assignment = getAssignmentForDay(dayIndex);
                return (
                  <div
                    key={dayIndex}
                    className={`p-4 rounded border ${
                      isDark
                        ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray'
                        : 'bg-gruvbox-light-bg border-gruvbox-light-gray'
                    }`}
                  >
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      {/* Day Name */}
                      <div className="flex items-center">
                        <span className={`font-bold ${
                          isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                        }`}>
                          {dayName}
                        </span>
                      </div>

                      {/* Action */}
                      <div>
                        <label className={`block mb-1 text-sm ${
                          isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                        }`}>
                          Action
                        </label>
                        <select
                          value={assignment.action}
                          onChange={(e) => updateAssignment(dayIndex, 'action', e.target.value)}
                          className={`w-full p-2 rounded border ${
                            isDark
                              ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                              : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
                          }`}
                        >
                          {defaultActions.map(action => (
                            <option key={action} value={action}>
                              {action.charAt(0).toUpperCase() + action.slice(1)}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Recipe (only for 'cook' action) */}
                      <div className="md:col-span-2">
                        <label className={`block mb-1 text-sm ${
                          isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                        }`}>
                          Recipe {assignment.action === 'cook' ? '*' : '(optional)'}
                        </label>
                        <select
                          value={assignment.recipe_id || ''}
                          onChange={(e) => updateAssignment(dayIndex, 'recipe_id', e.target.value || null)}
                          disabled={assignment.action !== 'cook'}
                          required={assignment.action === 'cook'}
                          className={`w-full p-2 rounded border ${
                            assignment.action !== 'cook'
                              ? isDark
                                ? 'bg-gruvbox-dark-bg-hard border-gruvbox-dark-gray text-gruvbox-dark-gray cursor-not-allowed'
                                : 'bg-gruvbox-light-bg-hard border-gruvbox-light-gray text-gruvbox-light-gray cursor-not-allowed'
                              : isDark
                                ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                                : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
                          }`}
                        >
                          <option value="">Select a recipe...</option>
                          {recipes.map(recipe => (
                            <option key={recipe.id} value={recipe.id}>
                              {recipe.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => navigate(`/schedules/${sequenceId}`)}
              className={`px-4 py-2 rounded transition ${
                isDark
                  ? 'bg-gruvbox-dark-bg hover:bg-gruvbox-dark-bg-hard'
                  : 'bg-gruvbox-light-bg hover:bg-gruvbox-light-bg-hard'
              }`}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className={`px-4 py-2 rounded transition ${
                submitting
                  ? isDark
                    ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                    : 'bg-gruvbox-light-gray cursor-not-allowed'
                  : isDark
                    ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                    : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
              }`}
            >
              {submitting ? 'Saving...' : isNew ? 'Create Week Template' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default WeekTemplateEditor;
