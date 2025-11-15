import { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Settings = () => {
  const { isDark, toggleTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Form state
  const [discordToken, setDiscordToken] = useState('');
  const [channelId, setChannelId] = useState('');
  const [notificationTime, setNotificationTime] = useState('07:00');
  const [timezone, setTimezone] = useState('UTC');

  // Discord connection state
  const [discordConnected, setDiscordConnected] = useState(false);
  const [checkingConnection, setCheckingConnection] = useState(false);
  const [channels, setChannels] = useState([]);
  const [loadingChannels, setLoadingChannels] = useState(false);

  // Bulk import/export state
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);

  const timezones = [
    'UTC',
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'America/Anchorage',
    'Pacific/Honolulu',
    'Europe/London',
    'Europe/Paris',
    'Asia/Tokyo',
    'Australia/Sydney',
  ];

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${API_URL}/settings`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = response.data;
      setDiscordToken(data.discord_bot_token || '');
      setChannelId(data.notification_channel_id || '');
      setNotificationTime(data.notification_time || '07:00');
      setTimezone(data.notification_timezone || 'UTC');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const checkDiscordStatus = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${API_URL}/discord/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setDiscordConnected(response.data.connected);

      // If connected, fetch channels
      if (response.data.connected) {
        await fetchChannels();
      }
    } catch (err) {
      setDiscordConnected(false);
    }
  };

  const fetchChannels = async () => {
    try {
      setLoadingChannels(true);
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${API_URL}/discord/channels`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setChannels(response.data.channels.sort((a, b) => a.name.localeCompare(b.name)));
    } catch (err) {
      console.error('Failed to fetch Discord channels:', err);
      setChannels([]);
    } finally {
      setLoadingChannels(false);
    }
  };

  useEffect(() => {
    loadSettings();
    checkDiscordStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const token = localStorage.getItem('access_token');
      await axios.put(
        `${API_URL}/settings`,
        {
          discord_bot_token: discordToken || null,
          notification_channel_id: channelId || null,
          notification_time: notificationTime,
          notification_timezone: timezone,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setSuccess('Settings saved successfully! Restart the app to apply Discord changes.');
      await checkDiscordStatus();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setCheckingConnection(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${API_URL}/discord/test-message`,
        { message: 'Test message from Roanes Kitchen settings!' },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setSuccess('Test message sent successfully!');
      setDiscordConnected(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send test message');
      setDiscordConnected(false);
    } finally {
      setCheckingConnection(false);
    }
  };

  const handleExportAll = async () => {
    setExporting(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${API_URL}/recipes/export-all`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'all_recipes.json');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setSuccess('All recipes exported successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to export recipes');
    } finally {
      setExporting(false);
    }
  };

  const handleImportMultiple = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.json')) {
      setError('Only .json files are allowed');
      event.target.value = '';
      return;
    }

    setImporting(true);
    setError(null);
    setSuccess(null);

    try {
      const token = localStorage.getItem('access_token');
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_URL}/recipes/import-multiple-json`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });

      const result = response.data;
      let message = result.message;

      if (result.errors && result.errors.length > 0) {
        message += '\n\nErrors:\n' + result.errors.join('\n');
      }

      setSuccess(message);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to import recipes');
    } finally {
      setImporting(false);
      event.target.value = ''; // Reset file input
    }
  };

  if (loading) {
    return (
      <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Loading settings...
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
          Settings
        </h1>

        {error && (
          <div className={`mb-4 p-4 rounded ${
            isDark ? 'bg-gruvbox-dark-red text-gruvbox-dark-bg' : 'bg-gruvbox-light-red text-gruvbox-light-bg'
          }`}>
            {error}
          </div>
        )}

        {success && (
          <div className={`mb-4 p-4 rounded ${
            isDark ? 'bg-gruvbox-dark-green text-gruvbox-dark-bg' : 'bg-gruvbox-light-green text-gruvbox-light-bg'
          }`}>
            {success}
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-6">
          {/* Discord Configuration */}
          <div className={`p-6 rounded border ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
              : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
          }`}>
            <h2 className={`text-2xl font-bold mb-4 ${
              isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
            }`}>
              Discord Bot Configuration
            </h2>

            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className={`font-semibold ${
                  isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                }`}>
                  Connection Status
                </label>
                <span className={`px-3 py-1 rounded text-sm font-semibold ${
                  discordConnected
                    ? isDark
                      ? 'bg-gruvbox-dark-green text-gruvbox-dark-bg'
                      : 'bg-gruvbox-light-green text-gruvbox-light-bg'
                    : isDark
                      ? 'bg-gruvbox-dark-gray text-gruvbox-dark-fg'
                      : 'bg-gruvbox-light-gray text-gruvbox-light-fg'
                }`}>
                  {discordConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>

            <div className="mb-4">
              <label className={`block mb-2 font-semibold ${
                isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
              }`}>
                Bot Token
              </label>
              <input
                type="password"
                value={discordToken}
                onChange={(e) => setDiscordToken(e.target.value)}
                className={`w-full p-2 rounded border ${
                  isDark
                    ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                    : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
                }`}
                placeholder="Enter Discord bot token..."
              />
              <p className={`mt-1 text-sm ${
                isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
              }`}>
                Get your bot token from{' '}
                <a
                  href="https://discord.com/developers/applications"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={isDark ? 'text-gruvbox-dark-blue' : 'text-gruvbox-light-blue'}
                >
                  Discord Developer Portal
                </a>
              </p>
            </div>

            <div className="mb-4">
              <label className={`block mb-2 font-semibold ${
                isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
              }`}>
                Notification Channel
              </label>
              {discordConnected && channels.length > 0 ? (
                <select
                  value={channelId}
                  onChange={(e) => setChannelId(e.target.value)}
                  className={`w-full p-2 rounded border ${
                    isDark
                      ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                      : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
                  }`}
                  disabled={loadingChannels}
                >
                  <option value="">Select a channel...</option>
                  {channels.map((channel) => (
                    <option key={channel.id} value={channel.id}>
                      #{channel.name} ({channel.guild_name})
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  value={channelId}
                  onChange={(e) => setChannelId(e.target.value)}
                  className={`w-full p-2 rounded border ${
                    isDark
                      ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                      : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
                  }`}
                  placeholder="Enter channel ID..."
                />
              )}
              <p className={`mt-1 text-sm ${
                isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
              }`}>
                {discordConnected && channels.length > 0
                  ? loadingChannels
                    ? 'Loading channels...'
                    : 'Select from available channels'
                  : 'Manual entry - right-click a channel in Discord and select "Copy Channel ID"'}
              </p>
            </div>

            <button
              type="button"
              onClick={handleTestConnection}
              disabled={!discordToken || !channelId || checkingConnection}
              className={`px-4 py-2 rounded transition ${
                !discordToken || !channelId || checkingConnection
                  ? isDark
                    ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                    : 'bg-gruvbox-light-gray cursor-not-allowed'
                  : isDark
                    ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright'
                    : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright'
              }`}
            >
              {checkingConnection ? 'Testing...' : 'Test Connection'}
            </button>
          </div>

          {/* Notification Settings */}
          <div className={`p-6 rounded border ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
              : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
          }`}>
            <h2 className={`text-2xl font-bold mb-4 ${
              isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
            }`}>
              Notification Settings
            </h2>

            <div className="mb-4">
              <label className={`block mb-2 font-semibold ${
                isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
              }`}>
                Notification Time
              </label>
              <input
                type="time"
                value={notificationTime}
                onChange={(e) => setNotificationTime(e.target.value)}
                className={`w-full p-2 rounded border ${
                  isDark
                    ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                    : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
                }`}
              />
              <p className={`mt-1 text-sm ${
                isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
              }`}>
                Time when daily notifications will be sent
              </p>
            </div>

            <div className="mb-4">
              <label className={`block mb-2 font-semibold ${
                isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
              }`}>
                Timezone
              </label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className={`w-full p-2 rounded border ${
                  isDark
                    ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                    : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
                }`}
              >
                {timezones.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Bulk Recipe Import/Export */}
          <div className={`p-6 rounded border ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
              : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
          }`}>
            <h2 className={`text-2xl font-bold mb-4 ${
              isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
            }`}>
              Recipe Backup & Restore
            </h2>

            <p className={`mb-4 text-sm ${
              isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
            }`}>
              Export all your recipes to a single JSON file for backup, or import multiple recipes at once.
            </p>

            <div className="flex gap-3 flex-wrap">
              <button
                type="button"
                onClick={handleExportAll}
                disabled={exporting}
                className={`px-4 py-2 rounded transition font-semibold ${
                  exporting
                    ? isDark
                      ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                      : 'bg-gruvbox-light-gray cursor-not-allowed'
                    : isDark
                      ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright'
                      : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright'
                }`}
              >
                {exporting ? 'Exporting...' : 'Export All Recipes'}
              </button>

              <label className={`px-4 py-2 rounded transition font-semibold cursor-pointer ${
                importing
                  ? isDark
                    ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                    : 'bg-gruvbox-light-gray cursor-not-allowed'
                  : isDark
                    ? 'bg-gruvbox-dark-aqua hover:bg-gruvbox-dark-aqua-bright text-gruvbox-dark-bg'
                    : 'bg-gruvbox-light-aqua hover:bg-gruvbox-light-aqua-bright text-gruvbox-light-bg'
              }`}>
                {importing ? 'Importing...' : 'Import Multiple Recipes'}
                <input
                  type="file"
                  accept=".json"
                  onChange={handleImportMultiple}
                  disabled={importing}
                  className="hidden"
                />
              </label>
            </div>
          </div>

          {/* Appearance Settings */}
          <div className={`p-6 rounded border ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
              : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
          }`}>
            <h2 className={`text-2xl font-bold mb-4 ${
              isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
            }`}>
              Appearance
            </h2>

            <div className="flex items-center justify-between">
              <div>
                <p className={`font-semibold ${
                  isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                }`}>
                  Theme
                </p>
                <p className={`text-sm ${
                  isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                }`}>
                  Current: {isDark ? 'Dark' : 'Light'}
                </p>
              </div>
              <button
                type="button"
                onClick={toggleTheme}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-yellow hover:bg-gruvbox-dark-yellow-bright'
                    : 'bg-gruvbox-light-yellow hover:bg-gruvbox-light-yellow-bright'
                }`}
              >
                Toggle Theme
              </button>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={saving}
              className={`px-6 py-3 rounded transition font-semibold ${
                saving
                  ? isDark
                    ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                    : 'bg-gruvbox-light-gray cursor-not-allowed'
                  : isDark
                    ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                    : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
              }`}
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Settings;
