import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { mealPlanAPI, recipeAPI, authAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import Toast from '../components/Toast';
import ConfirmDialog from '../components/ConfirmDialog';

const MealPlanCurrent = () => {
  const { isDark } = useTheme();
  const [searchParams] = useSearchParams();
  const sequenceId = searchParams.get('sequence_id');

  const [mealPlan, setMealPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [editingDate, setEditingDate] = useState(null);
  const [editForm, setEditForm] = useState({ userId: '', action: '', recipeId: '' });
  const [users, setUsers] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState(null);

  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  const loadUsersAndRecipes = async () => {
    try {
      const [usersResponse, recipesResponse] = await Promise.all([
        authAPI.listUsers(),
        recipeAPI.list({ deleted: false })
      ]);
      setUsers(usersResponse.data);
      setRecipes(recipesResponse.data);
    } catch (err) {
      console.error('Failed to load users and recipes:', err);
    }
  };

  const loadCurrentMealPlan = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await mealPlanAPI.getCurrent(sequenceId);
      setMealPlan(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load current meal plan');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (sequenceId) {
      loadCurrentMealPlan();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sequenceId]);

  useEffect(() => {
    loadUsersAndRecipes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleGenerateGroceryList = async (date) => {
    try {
      setGenerating(true);
      await mealPlanAPI.generateGroceryList(mealPlan.id, date);
      // Reload to show updated grocery list count
      await loadCurrentMealPlan();
      setToast({
        message: 'Grocery list generated successfully!',
        type: 'success',
      });
    } catch (err) {
      setToast({
        message: err.response?.data?.detail || 'Failed to generate grocery list',
        type: 'error',
      });
    } finally {
      setGenerating(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const handleEditClick = (date, assignment) => {
    setEditingDate(date);
    setEditForm({
      userId: assignment.assigned_user_id,
      action: assignment.action,
      recipeId: assignment.recipe_id || '',
    });
  };

  const handleCancelEdit = () => {
    setEditingDate(null);
    setEditForm({ userId: '', action: '', recipeId: '' });
  };

  const handleSaveEdit = async (date, dayOfWeek, assignment) => {
    try {
      setSaving(true);

      // Check if this assignment is already a per-instance override (has an id)
      if (assignment.is_modified && assignment.id) {
        // Update existing meal_assignment
        await mealPlanAPI.updateAssignment(mealPlan.id, assignment.id, {
          assigned_user_id: editForm.userId,
          action: editForm.action,
          recipe_id: editForm.action === 'cook' ? editForm.recipeId : null,
        });
      } else {
        // Create new meal_assignment (override template)
        await mealPlanAPI.createAssignment(mealPlan.id, {
          day_of_week: dayOfWeek,
          assigned_user_id: editForm.userId,
          action: editForm.action,
          recipe_id: editForm.action === 'cook' ? editForm.recipeId : null,
          order: assignment.order,
        });
      }

      // Reload the meal plan to get updated data
      await loadCurrentMealPlan();
      setEditingDate(null);
      setEditForm({ userId: '', action: '', recipeId: '' });
    } catch (err) {
      setToast({
        message: err.response?.data?.detail || 'Failed to save assignment',
        type: 'error',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleResetToTemplate = async (assignment) => {
    setConfirmDialog({
      message: 'Reset this day to the template assignment?',
      onConfirm: async () => {
        setConfirmDialog(null);
        try {
          setSaving(true);

          if (assignment.is_modified && assignment.id) {
            await mealPlanAPI.deleteAssignment(mealPlan.id, assignment.id);
            await loadCurrentMealPlan();
          }
        } catch (err) {
          setToast({
            message: err.response?.data?.detail || 'Failed to reset assignment',
            type: 'error',
          });
        } finally {
          setSaving(false);
        }
      },
      onCancel: () => setConfirmDialog(null),
    });
  };

  const groupAssignmentsByDate = (assignments) => {
    const grouped = {};
    assignments.forEach(assignment => {
      if (!grouped[assignment.date]) {
        grouped[assignment.date] = [];
      }
      grouped[assignment.date].push(assignment);
    });
    return grouped;
  };

  const getUsernameById = (userId) => {
    const user = users.find(u => u.id === userId);
    return user ? user.username : 'Unknown';
  };

  if (!sequenceId) {
    return (
      <div className={`p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
        <div className={`p-4 rounded ${
          isDark ? 'bg-gruvbox-dark-yellow text-gruvbox-dark-bg' : 'bg-gruvbox-light-yellow text-gruvbox-light-bg'
        }`}>
          Please select a schedule sequence. <Link to="/schedules" className="underline">Go to Schedules</Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={`p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Loading current meal plan...
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

  if (!mealPlan) {
    return (
      <div className={`p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          No active meal plan for this sequence
        </div>
      </div>
    );
  }

  const assignmentsByDate = groupAssignmentsByDate(mealPlan.assignments || []);
  const sortedDates = Object.keys(assignmentsByDate).sort();

  return (
    <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className={`text-3xl font-bold mb-2 ${
            isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
          }`}>
            Current Meal Plan
          </h1>
          <p className={`text-lg ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
            <span className="font-semibold">{mealPlan.theme_name}</span> - Week {mealPlan.week_number}
          </p>
          <p className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
            Starting {formatDate(mealPlan.instance_start_date)}
          </p>
        </div>

        {/* Daily Schedule */}
        <div className="space-y-4 mb-8">
          {sortedDates.map(date => {
            const assignments = assignmentsByDate[date];
            const dayAssignment = assignments[0];
            // Parse date as local time to avoid timezone shifts
            const [year, month, day] = date.split('-').map(Number);
            const dateObj = new Date(year, month - 1, day);
            const dayName = dayNames[dateObj.getDay()];
            const isToday = new Date().toDateString() === dateObj.toDateString();

            const isModified = dayAssignment.is_modified;
            const isEditing = editingDate === date;

            return (
              <div
                key={date}
                className={`p-6 rounded-lg border-2 relative ${
                  isModified
                    ? 'border-l-4 border-l-gruvbox-dark-orange-bright'
                    : ''
                } ${
                  isToday
                    ? isDark
                      ? 'border-gruvbox-dark-orange bg-gruvbox-dark-bg-soft'
                      : 'border-gruvbox-light-orange bg-gruvbox-light-bg-soft'
                    : isDark
                      ? 'border-gruvbox-dark-gray bg-gruvbox-dark-bg-soft'
                      : 'border-gruvbox-light-gray bg-gruvbox-light-bg-soft'
                } ${isModified ? (isDark ? 'bg-opacity-95 bg-gruvbox-dark-orange/5' : 'bg-gruvbox-light-orange/5') : ''}`}
              >
                {isModified && (
                  <div className="absolute top-2 right-2">
                    <span className="text-xs px-2 py-1 rounded bg-gruvbox-dark-orange-bright text-white" title="Modified from template">
                      ✏️
                    </span>
                  </div>
                )}
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className={`text-xl font-bold ${
                      isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                    }`}>
                      {dayName}
                      {isToday && (
                        <span className={`ml-2 text-xs px-2 py-1 rounded ${
                          isDark
                            ? 'bg-gruvbox-dark-orange text-gruvbox-dark-bg'
                            : 'bg-gruvbox-light-orange text-gruvbox-light-bg'
                        }`}>
                          TODAY
                        </span>
                      )}
                    </h3>
                    <p className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                      {formatDate(date)}
                    </p>
                  </div>
                  {dayAssignment.action === 'shop' && (
                    <button
                      onClick={() => handleGenerateGroceryList(date)}
                      disabled={generating}
                      className={`px-4 py-2 rounded transition ${
                        generating
                          ? isDark
                            ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                            : 'bg-gruvbox-light-gray cursor-not-allowed'
                          : isDark
                            ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                            : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
                      }`}
                    >
                      {generating ? 'Generating...' : 'Generate Grocery List'}
                    </button>
                  )}
                </div>

                {isEditing ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
                          Person
                        </label>
                        <select
                          value={editForm.userId}
                          onChange={(e) => setEditForm({ ...editForm, userId: e.target.value })}
                          className={`w-full px-3 py-2 rounded border ${
                            isDark
                              ? 'bg-gruvbox-dark-bg-hard border-gruvbox-dark-gray text-gruvbox-dark-fg'
                              : 'bg-white border-gruvbox-light-gray text-gruvbox-light-fg'
                          }`}
                        >
                          <option value="">Select person...</option>
                          {users.map(user => (
                            <option key={user.id} value={user.id}>{user.username}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
                          Action
                        </label>
                        <select
                          value={editForm.action}
                          onChange={(e) => setEditForm({ ...editForm, action: e.target.value, recipeId: e.target.value === 'cook' ? editForm.recipeId : '' })}
                          className={`w-full px-3 py-2 rounded border ${
                            isDark
                              ? 'bg-gruvbox-dark-bg-hard border-gruvbox-dark-gray text-gruvbox-dark-fg'
                              : 'bg-white border-gruvbox-light-gray text-gruvbox-light-fg'
                          }`}
                        >
                          <option value="">Select action...</option>
                          <option value="cook">Cook</option>
                          <option value="shop">Shop</option>
                          <option value="takeout">Takeout</option>
                          <option value="rest">Rest</option>
                          <option value="leftovers">Leftovers</option>
                        </select>
                      </div>
                      {editForm.action === 'cook' && (
                        <div>
                          <label className={`block text-sm font-medium mb-2 ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
                            Recipe
                          </label>
                          <select
                            value={editForm.recipeId}
                            onChange={(e) => setEditForm({ ...editForm, recipeId: e.target.value })}
                            className={`w-full px-3 py-2 rounded border ${
                              isDark
                                ? 'bg-gruvbox-dark-bg-hard border-gruvbox-dark-gray text-gruvbox-dark-fg'
                                : 'bg-white border-gruvbox-light-gray text-gruvbox-light-fg'
                            }`}
                          >
                            <option value="">Select recipe...</option>
                            {recipes.map(recipe => (
                              <option key={recipe.id} value={recipe.id}>{recipe.name}</option>
                            ))}
                          </select>
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleSaveEdit(date, dateObj.getDay(), dayAssignment)}
                        disabled={saving || !editForm.userId || !editForm.action || (editForm.action === 'cook' && !editForm.recipeId)}
                        className={`px-4 py-2 rounded transition ${
                          saving || !editForm.userId || !editForm.action || (editForm.action === 'cook' && !editForm.recipeId)
                            ? 'bg-gray-400 cursor-not-allowed'
                            : isDark
                              ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                              : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
                        }`}
                      >
                        {saving ? 'Saving...' : 'Save'}
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        disabled={saving}
                        className={`px-4 py-2 rounded transition ${
                          isDark
                            ? 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-fg0'
                            : 'bg-gruvbox-light-gray hover:bg-gruvbox-light-fg0'
                        }`}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {assignments.map((assignment, idx) => (
                      <div key={idx} className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4">
                          <span className={`px-3 py-1 rounded text-sm font-semibold uppercase ${
                            isDark
                              ? 'bg-gruvbox-dark-blue text-gruvbox-dark-bg'
                              : 'bg-gruvbox-light-blue text-gruvbox-light-bg'
                          }`}>
                            {assignment.action}
                          </span>
                          <span className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                            {getUsernameById(assignment.assigned_user_id)}
                          </span>
                          {assignment.recipe_name && (
                            <span className={`text-lg ${
                              isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                            }`}>
                              {assignment.recipe_name}
                            </span>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditClick(date, assignment)}
                            className={`px-3 py-1 text-sm rounded transition ${
                              isDark
                                ? 'bg-gruvbox-dark-purple hover:bg-gruvbox-dark-purple-bright'
                                : 'bg-gruvbox-light-purple hover:bg-gruvbox-light-purple-bright'
                            }`}
                          >
                            Edit
                          </button>
                          {isModified && (
                            <button
                              onClick={() => handleResetToTemplate(assignment)}
                              className={`px-3 py-1 text-sm rounded transition ${
                                isDark
                                  ? 'bg-gruvbox-dark-orange hover:bg-gruvbox-dark-orange-bright'
                                  : 'bg-gruvbox-light-orange hover:bg-gruvbox-light-orange-bright'
                              }`}
                            >
                              Reset
                            </button>
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

        {/* Links */}
        <div className="flex gap-4">
          <Link
            to={`/meal-plans?sequence_id=${sequenceId}`}
            className={`px-4 py-2 rounded transition ${
              isDark
                ? 'bg-gruvbox-dark-purple hover:bg-gruvbox-dark-purple-bright'
                : 'bg-gruvbox-light-purple hover:bg-gruvbox-light-purple-bright'
            }`}
          >
            View All Meal Plans
          </Link>
          <Link
            to="/grocery-lists"
            className={`px-4 py-2 rounded transition ${
              isDark
                ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright'
                : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright'
            }`}
          >
            View Grocery Lists
          </Link>
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

export default MealPlanCurrent;
