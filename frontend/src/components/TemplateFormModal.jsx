import { useState, useEffect } from 'react';
import { templateAPI, recipeAPI, authAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

const TemplateFormModal = ({ isOpen, onClose, onSuccess }) => {
  const { isDark } = useTheme();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [name, setName] = useState('');
  const [assignments, setAssignments] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [users, setUsers] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const defaultActions = ['cook', 'shop', 'takeout', 'rest', 'leftovers'];

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load recipes and users
      const [recipesRes, usersRes] = await Promise.all([
        recipeAPI.list(),
        authAPI.listUsers()
      ]);

      setRecipes(recipesRes.data || []);
      setUsers(usersRes.data || [user]);

      // Initialize empty assignments for all 7 days
      const emptyAssignments = dayNames.map((_, dayIndex) => ({
        day_of_week: dayIndex,
        assigned_user_id: user.id,
        action: 'cook',
        recipe_id: null,
        order: 0,
      }));
      setAssignments(emptyAssignments);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const updateAssignment = (dayIndex, field, value) => {
    const updated = [...assignments];
    const assignmentIndex = updated.findIndex(a => a.day_of_week === dayIndex);

    if (assignmentIndex >= 0) {
      updated[assignmentIndex] = {
        ...updated[assignmentIndex],
        [field]: value === '' ? null : value,
      };
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

    // Validate that cook actions have a recipe selected
    const invalidDays = [];
    assignments.forEach((assignment) => {
      if (assignment.action === 'cook' && !assignment.recipe_id) {
        invalidDays.push(dayNames[assignment.day_of_week]);
      }
    });

    if (invalidDays.length > 0) {
      const daysList = invalidDays.join(', ');
      setError(`Please select a recipe for "cook" action on: ${daysList}`);
      setSubmitting(false);
      return;
    }

    try {
      const response = await templateAPI.create({
        name,
        assignments: assignments.map(a => ({
          day_of_week: a.day_of_week,
          assigned_user_id: a.assigned_user_id,
          action: a.action,
          recipe_id: a.recipe_id || null,
          order: a.order || 0,
        })),
      });

      // Reset form
      setName('');
      setAssignments([]);

      // Call success callback with created template
      if (onSuccess) {
        onSuccess(response.data);
      }

      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create template');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    setName('');
    setAssignments([]);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className={`rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto ${
        isDark ? 'bg-gruvbox-dark-bg-soft' : 'bg-white'
      }`}>
        <h2 className={`text-2xl font-bold mb-4 ${
          isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
        }`}>
          Create New Week Template
        </h2>

        {error && (
          <div className={`p-4 rounded mb-4 ${
            isDark ? 'bg-gruvbox-dark-red text-gruvbox-dark-bg' : 'bg-gruvbox-light-red text-gruvbox-light-bg'
          }`}>
            {error}
          </div>
        )}

        {loading ? (
          <div className={`text-center py-8 ${
            isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
          }`}>
            <div className="animate-pulse">Loading...</div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="mb-6">
              <label className={`block mb-2 font-semibold ${
                isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
              }`}>
                Template Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className={`w-full px-4 py-2 rounded border ${
                  isDark
                    ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                    : 'bg-white border-gruvbox-light-gray text-gruvbox-light-fg'
                }`}
                placeholder="e.g., Standard Week, Holiday Week, etc."
              />
            </div>

            <div className="space-y-4 mb-6">
              <h3 className={`text-xl font-semibold ${
                isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
              }`}>
                Daily Assignments
              </h3>

              {dayNames.map((day, dayIndex) => {
                const assignment = getAssignmentForDay(dayIndex);
                return (
                  <div
                    key={dayIndex}
                    className={`p-4 rounded border ${
                      isDark
                        ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray'
                        : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
                    }`}
                  >
                    <div className={`font-semibold mb-3 ${
                      isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                    }`}>
                      {day}
                    </div>

                    <div className="grid gap-3 md:grid-cols-3">
                      <div>
                        <label className={`block text-sm mb-1 ${
                          isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                        }`}>
                          Person
                        </label>
                        <select
                          value={assignment.assigned_user_id}
                          onChange={(e) => updateAssignment(dayIndex, 'assigned_user_id', e.target.value)}
                          className={`w-full px-3 py-2 rounded border ${
                            isDark
                              ? 'bg-gruvbox-dark-bg-hard border-gruvbox-dark-gray text-gruvbox-dark-fg'
                              : 'bg-white border-gruvbox-light-gray text-gruvbox-light-fg'
                          }`}
                        >
                          {users.map(u => (
                            <option key={u.id} value={u.id}>{u.username}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className={`block text-sm mb-1 ${
                          isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                        }`}>
                          Action
                        </label>
                        <select
                          value={assignment.action}
                          onChange={(e) => updateAssignment(dayIndex, 'action', e.target.value)}
                          className={`w-full px-3 py-2 rounded border ${
                            isDark
                              ? 'bg-gruvbox-dark-bg-hard border-gruvbox-dark-gray text-gruvbox-dark-fg'
                              : 'bg-white border-gruvbox-light-gray text-gruvbox-light-fg'
                          }`}
                        >
                          {defaultActions.map(action => (
                            <option key={action} value={action}>{action}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className={`block text-sm mb-1 ${
                          isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                        }`}>
                          Recipe {assignment.action === 'cook' && <span className="text-red-500">*</span>}
                        </label>
                        <select
                          value={assignment.recipe_id || ''}
                          onChange={(e) => updateAssignment(dayIndex, 'recipe_id', e.target.value)}
                          disabled={assignment.action !== 'cook'}
                          className={`w-full px-3 py-2 rounded border ${
                            isDark
                              ? 'bg-gruvbox-dark-bg-hard border-gruvbox-dark-gray text-gruvbox-dark-fg disabled:opacity-50'
                              : 'bg-white border-gruvbox-light-gray text-gruvbox-light-fg disabled:opacity-50'
                          }`}
                        >
                          <option value="">No recipe</option>
                          {recipes.map(recipe => (
                            <option key={recipe.id} value={recipe.id}>{recipe.name}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex gap-4 justify-end">
              <button
                type="button"
                onClick={handleClose}
                disabled={submitting}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright text-gruvbox-dark-fg'
                    : 'bg-gruvbox-light-gray hover:bg-gruvbox-light-gray-bright text-gruvbox-light-fg'
                }`}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || !name}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright disabled:opacity-50 text-gruvbox-dark-bg'
                    : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright disabled:opacity-50 text-gruvbox-light-bg'
                }`}
              >
                {submitting ? 'Creating...' : 'Create Template'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default TemplateFormModal;
