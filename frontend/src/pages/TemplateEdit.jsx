import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { templateAPI, recipeAPI, authAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

const TemplateEdit = () => {
  const { id } = useParams();
  const navigate = useNavigate();
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

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load template, recipes, and users
      const [templateRes, recipesRes, usersRes] = await Promise.all([
        templateAPI.get(id),
        recipeAPI.list(),
        authAPI.listUsers()
      ]);

      const template = templateRes.data;
      setName(template.name);
      setRecipes(recipesRes.data || []);
      setUsers(usersRes.data || [user]);

      // Convert template day_assignments to form assignments
      // Ensure we have one assignment per day
      const templateAssignments = template.day_assignments || [];
      const allDayAssignments = dayNames.map((_, dayIndex) => {
        const existingAssignment = templateAssignments.find(a => a.day_of_week === dayIndex);
        if (existingAssignment) {
          return {
            day_of_week: existingAssignment.day_of_week,
            assigned_user_id: existingAssignment.assigned_user_id,
            action: existingAssignment.action,
            recipe_id: existingAssignment.recipe_id,
            order: existingAssignment.order || 0,
          };
        }
        // Default for days without assignments
        return {
          day_of_week: dayIndex,
          assigned_user_id: user.id,
          action: 'cook',
          recipe_id: null,
          order: 0,
        };
      });

      setAssignments(allDayAssignments);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load template');
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
      await templateAPI.update(id, {
        name,
        assignments: assignments.map(a => ({
          day_of_week: a.day_of_week,
          assigned_user_id: a.assigned_user_id,
          action: a.action,
          recipe_id: a.recipe_id || null,
          order: a.order || 0,
        })),
      });

      navigate(`/templates/${id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update template');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Loading template...
        </div>
      </div>
    );
  }

  if (error && !name) {
    return (
      <div className="p-8">
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
        <h1 className={`text-3xl font-bold mb-6 ${
          isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
        }`}>
          Edit Template
        </h1>

        {error && (
          <div className={`p-4 rounded mb-4 ${
            isDark ? 'bg-gruvbox-dark-red text-gruvbox-dark-bg' : 'bg-gruvbox-light-red text-gruvbox-light-bg'
          }`}>
            {error}
          </div>
        )}

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
                  ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray text-gruvbox-dark-fg'
                  : 'bg-white border-gruvbox-light-gray text-gruvbox-light-fg'
              }`}
              placeholder="e.g., Standard Week, Holiday Week, etc."
            />
          </div>

          <div className="space-y-4">
            <h2 className={`text-xl font-semibold ${
              isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
            }`}>
              Daily Assignments
            </h2>

            {dayNames.map((day, dayIndex) => {
              const assignment = getAssignmentForDay(dayIndex);
              return (
                <div
                  key={dayIndex}
                  className={`p-4 rounded border ${
                    isDark
                      ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
                      : 'bg-white border-gruvbox-light-gray'
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
                            ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
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
                            ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
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
                            ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg disabled:opacity-50'
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

          <div className="mt-6 flex gap-4">
            <button
              type="submit"
              disabled={submitting || !name}
              className={`px-6 py-2 rounded transition ${
                isDark
                  ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright disabled:opacity-50 text-gruvbox-dark-bg'
                  : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright disabled:opacity-50 text-gruvbox-light-bg'
              }`}
            >
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
            <button
              type="button"
              onClick={() => navigate(`/templates/${id}`)}
              className={`px-6 py-2 rounded transition ${
                isDark
                  ? 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright text-gruvbox-dark-fg'
                  : 'bg-gruvbox-light-gray hover:bg-gruvbox-light-gray-bright text-gruvbox-light-fg'
              }`}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TemplateEdit;
