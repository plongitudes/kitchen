import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { scheduleAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';

const ScheduleNew = () => {
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const [formData, setFormData] = useState({
    name: '',
    advancement_day_of_week: '0',
    advancement_time: '00:00',
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const payload = {
        name: formData.name,
        advancement_day_of_week: parseInt(formData.advancement_day_of_week),
        advancement_time: formData.advancement_time,
      };

      const response = await scheduleAPI.create(payload);
      navigate(`/schedules/${response.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create schedule');
      setSubmitting(false);
    }
  };

  return (
    <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={() => navigate('/schedules')}
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
              Create Schedule Sequence
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

        <form onSubmit={handleSubmit} className={`p-6 rounded border ${
          isDark
            ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
            : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
        }`}>
          {/* Name */}
          <div className="mb-4">
            <label className={`block mb-2 font-semibold ${
              isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
            }`}>
              Sequence Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              className={`w-full p-2 rounded border ${
                isDark
                  ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                  : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
              }`}
              placeholder="e.g., Family Meal Rotation"
            />
          </div>

          {/* Advancement Day */}
          <div className="mb-4">
            <label className={`block mb-2 font-semibold ${
              isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
            }`}>
              Week Advances On *
            </label>
            <select
              value={formData.advancement_day_of_week}
              onChange={(e) => setFormData({ ...formData, advancement_day_of_week: e.target.value })}
              required
              className={`w-full p-2 rounded border ${
                isDark
                  ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                  : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
              }`}
            >
              {dayNames.map((day, index) => (
                <option key={index} value={index}>
                  {day}
                </option>
              ))}
            </select>
            <p className={`mt-1 text-sm ${
              isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
            }`}>
              The day of the week when the schedule advances to the next week template
            </p>
          </div>

          {/* Advancement Time */}
          <div className="mb-6">
            <label className={`block mb-2 font-semibold ${
              isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
            }`}>
              Advancement Time *
            </label>
            <input
              type="time"
              value={formData.advancement_time}
              onChange={(e) => setFormData({ ...formData, advancement_time: e.target.value })}
              required
              className={`w-full p-2 rounded border ${
                isDark
                  ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                  : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
              }`}
            />
            <p className={`mt-1 text-sm ${
              isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
            }`}>
              The time when the schedule advances (24-hour format)
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => navigate('/schedules')}
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
              {submitting ? 'Creating...' : 'Create Sequence'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ScheduleNew;
