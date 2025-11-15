import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { scheduleAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';

const ScheduleList = () => {
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSchedules();
  }, []);

  const loadSchedules = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await scheduleAPI.list();
      setSchedules(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load schedules');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (scheduleId, scheduleName, e) => {
    e.stopPropagation(); // Prevent navigation when clicking delete
    if (!confirm(`Are you sure you want to delete "${scheduleName}"? This cannot be undone.`)) {
      return;
    }

    try {
      await scheduleAPI.delete(scheduleId);
      await loadSchedules();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete schedule');
    }
  };

  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  if (loading) {
    return (
      <div className="p-8">
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Loading schedules...
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
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className={`text-3xl font-bold ${
            isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
          }`}>
            Schedule Sequences
          </h1>
          <Link
            to="/schedules/new"
            className={`px-4 py-2 rounded transition ${
              isDark
                ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
            }`}
          >
            Create New Sequence
          </Link>
        </div>

        {schedules.length === 0 ? (
          <div className={`text-center p-8 border-2 border-dashed rounded ${
            isDark ? 'border-gruvbox-dark-gray text-gruvbox-dark-gray' : 'border-gruvbox-light-gray text-gruvbox-light-gray'
          }`}>
            <p className="mb-4">No schedule sequences yet</p>
            <Link
              to="/schedules/new"
              className={`inline-block px-4 py-2 rounded transition ${
                isDark
                  ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                  : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
              }`}
            >
              Create Your First Sequence
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {schedules.map((schedule) => (
              <div
                key={schedule.id}
                onClick={() => navigate(`/schedules/${schedule.id}`)}
                className={`p-6 rounded border-2 transition cursor-pointer ${
                  isDark
                    ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray hover:border-gruvbox-dark-orange'
                    : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray hover:border-gruvbox-light-orange'
                }`}
              >
                <div className="flex justify-between items-start mb-3">
                  <h2 className={`text-xl font-bold ${
                    isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
                  }`}>
                    {schedule.name}
                  </h2>
                  <button
                    onClick={(e) => handleDelete(schedule.id, schedule.name, e)}
                    className={`px-3 py-1 rounded text-sm transition ${
                      isDark
                        ? 'bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright text-gruvbox-dark-bg'
                        : 'bg-gruvbox-light-red hover:bg-gruvbox-light-red-bright text-gruvbox-light-bg'
                    }`}
                  >
                    Delete
                  </button>
                </div>

                <div className={`space-y-2 text-sm ${
                  isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                }`}>
                  <div className="flex justify-between">
                    <span className={isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}>
                      Current Week:
                    </span>
                    <span className="font-semibold">Week {schedule.current_week_index + 1}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className={isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}>
                      Advances:
                    </span>
                    <span>
                      {dayNames[schedule.advancement_day_of_week]} at {schedule.advancement_time}
                    </span>
                  </div>

                  <div className={`mt-3 pt-3 border-t ${
                    isDark ? 'border-gruvbox-dark-gray' : 'border-gruvbox-light-gray'
                  }`}>
                    <span className={`text-xs ${
                      isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                    }`}>
                      Click to view templates
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ScheduleList;
