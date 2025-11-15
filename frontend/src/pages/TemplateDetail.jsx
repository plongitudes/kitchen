import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { templateAPI, authAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';

const TemplateDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const [template, setTemplate] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [forkName, setForkName] = useState('');
  const [showForkModal, setShowForkModal] = useState(false);
  const [forking, setForking] = useState(false);
  const [retiring, setRetiring] = useState(false);

  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  useEffect(() => {
    loadTemplate();
  }, [id]);

  const loadTemplate = async () => {
    try {
      setLoading(true);
      setError(null);
      const [templateRes, usersRes] = await Promise.all([
        templateAPI.get(id),
        authAPI.listUsers(),
      ]);
      setTemplate(templateRes.data);
      setUsers(usersRes.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load template');
    } finally {
      setLoading(false);
    }
  };

  const getUsernameById = (userId) => {
    const user = users.find(u => u.id === userId);
    return user ? user.username : 'Unknown User';
  };

  const handleFork = async () => {
    if (!forkName.trim()) {
      alert('Please enter a name for the forked template');
      return;
    }

    try {
      setForking(true);
      const response = await templateAPI.fork(id, forkName);
      navigate(`/templates/${response.data.id}`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to fork template');
    } finally {
      setForking(false);
    }
  };

  const handleRetire = async () => {
    if (!confirm('Are you sure you want to retire this template? It will be removed from all schedules.')) {
      return;
    }

    try {
      setRetiring(true);
      await templateAPI.retire(id);
      navigate('/templates');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to retire template');
      setRetiring(false);
    }
  };

  const getAssignmentsForDay = (dayIndex) => {
    if (!template) return [];
    return template.day_assignments
      .filter(a => a.day_of_week === dayIndex)
      .sort((a, b) => a.order - b.order);
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

  if (error) {
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
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className={`text-3xl font-bold mb-2 ${
              isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
            }`}>
              {template.name}
              {template.retired_at && (
                <span className={`ml-3 text-lg ${
                  isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                }`}>
                  (Retired)
                </span>
              )}
            </h1>
            <div className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
              Created: {new Date(template.created_at).toLocaleDateString()}
              {template.retired_at && (
                <> • Retired: {new Date(template.retired_at).toLocaleDateString()}</>
              )}
            </div>
          </div>

          {!template.retired_at && (
            <div className="flex gap-2">
              <Link
                to={`/templates/${id}/edit`}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-purple hover:bg-gruvbox-dark-purple-bright text-gruvbox-dark-bg'
                    : 'bg-gruvbox-light-purple hover:bg-gruvbox-light-purple-bright text-gruvbox-light-bg'
                }`}
              >
                Edit
              </Link>
              <button
                onClick={() => setShowForkModal(true)}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright text-gruvbox-dark-bg'
                    : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright text-gruvbox-light-bg'
                }`}
              >
                Fork Template
              </button>
              <button
                onClick={handleRetire}
                disabled={retiring}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright text-gruvbox-dark-bg disabled:opacity-50'
                    : 'bg-gruvbox-light-red hover:bg-gruvbox-light-red-bright text-gruvbox-light-bg disabled:opacity-50'
                }`}
              >
                {retiring ? 'Retiring...' : 'Retire'}
              </button>
            </div>
          )}
        </div>

        {/* Day Assignments */}
        <div className="space-y-4">
          <h2 className={`text-xl font-semibold ${
            isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
          }`}>
            Weekly Schedule
          </h2>

          {dayNames.map((day, dayIndex) => {
            const assignments = getAssignmentsForDay(dayIndex);
            return (
              <div
                key={dayIndex}
                className={`p-4 rounded border ${
                  isDark
                    ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
                    : 'bg-white border-gruvbox-light-gray'
                }`}
              >
                <div className={`font-semibold mb-2 ${
                  isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                }`}>
                  {day}
                </div>

                {assignments.length === 0 ? (
                  <div className={`text-sm ${
                    isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                  }`}>
                    No assignments
                  </div>
                ) : (
                  <div className="space-y-2">
                    {assignments.map((assignment) => (
                      <div
                        key={assignment.id}
                        className={`p-3 rounded ${
                          isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'
                        }`}
                      >
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className={`font-medium ${
                              isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                            }`}>
                              Person:{' '}
                            </span>
                            <span className={isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}>
                              {assignment.assigned_user_id ? getUsernameById(assignment.assigned_user_id) : 'Unassigned'}
                            </span>
                          </div>
                          <div>
                            <span className={`font-medium ${
                              isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                            }`}>
                              Action:{' '}
                            </span>
                            <span className={isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}>
                              {assignment.action}
                            </span>
                          </div>
                          <div>
                            <span className={`font-medium ${
                              isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                            }`}>
                              Recipe:{' '}
                            </span>
                            <span className={isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}>
                              {assignment.recipe_name || 'None'}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Back Button */}
        <div className="mt-8">
          <Link
            to="/templates"
            className={`hover:underline ${
              isDark ? 'text-gruvbox-dark-blue-bright' : 'text-gruvbox-light-blue-bright'
            }`}
          >
            ← Back to Templates
          </Link>
        </div>
      </div>

      {/* Fork Modal */}
      {showForkModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className={`rounded-lg p-6 max-w-md w-full ${
            isDark ? 'bg-gruvbox-dark-bg-soft' : 'bg-white'
          }`}>
            <h3 className={`text-xl font-bold mb-4 ${
              isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
            }`}>
              Fork Template
            </h3>
            <p className={`mb-4 ${
              isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
            }`}>
              Create a copy of this template with a new name:
            </p>
            <input
              type="text"
              value={forkName}
              onChange={(e) => setForkName(e.target.value)}
              placeholder="Enter new template name"
              className={`w-full px-4 py-2 rounded border mb-4 ${
                isDark
                  ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                  : 'bg-white border-gruvbox-light-gray text-gruvbox-light-fg'
              }`}
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setShowForkModal(false);
                  setForkName('');
                }}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright text-gruvbox-dark-fg'
                    : 'bg-gruvbox-light-gray hover:bg-gruvbox-light-gray-bright text-gruvbox-light-fg'
                }`}
              >
                Cancel
              </button>
              <button
                onClick={handleFork}
                disabled={forking || !forkName.trim()}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg disabled:opacity-50'
                    : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg disabled:opacity-50'
                }`}
              >
                {forking ? 'Creating...' : 'Create Fork'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateDetail;
