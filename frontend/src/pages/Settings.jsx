import { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import api from '../services/api';
import ConfirmModal from '../components/ConfirmModal';

const Settings = () => {
  const { isDark, toggleTheme, currentFont, setFont, availableFonts } = useTheme();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Form state
  const [notificationTime, setNotificationTime] = useState('07:00');
  const [timezone, setTimezone] = useState('UTC');

  // Discord connection state
  const [discordConnected, setDiscordConnected] = useState(false);
  const [checkingConnection, setCheckingConnection] = useState(false);

  // Bulk import/export state
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);

  // Database backup state
  const [backups, setBackups] = useState([]);
  const [creatingBackup, setCreatingBackup] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [confirmModal, setConfirmModal] = useState({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: null,
    variant: 'warning',
    confirmText: 'Confirm',
  });

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
      const response = await api.get(`/settings`, {
      });

      const data = response.data;
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
      const response = await api.get(`/discord/status`, {
      });
      setDiscordConnected(response.data.connected);
    } catch (err) {
      setDiscordConnected(false);
    }
  };

  const loadBackups = async () => {
    try {
      const response = await api.get(`/backup/list`, {
      });
      setBackups(response.data);
    } catch (err) {
      console.error('Failed to load backups:', err);
    }
  };

  useEffect(() => {
    loadSettings();
    checkDiscordStatus();
    loadBackups();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await api.put(
        `/settings`,
        {
          notification_time: notificationTime,
          notification_timezone: timezone,
        },
        {
        }
      );

      setSuccess('Settings saved successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleReconnect = async () => {
    setCheckingConnection(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await api.post(
        `/discord/reconnect`,
        {},
        {
        }
      );
      setSuccess(response.data.message);
      await checkDiscordStatus();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reconnect Discord bot');
    } finally {
      setCheckingConnection(false);
    }
  };

  const handleTestNotifications = async () => {
    setCheckingConnection(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await api.post(
        `/discord/test-notifications`,
        {},
        {
        }
      );
      setSuccess(response.data.message);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send test notifications');
    } finally {
      setCheckingConnection(false);
    }
  };

  const handleExportAll = async () => {
    setExporting(true);
    setError(null);

    try {
      const response = await api.get(`/recipes/export-all`, {
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
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post(`/recipes/import-multiple-json`, formData, {
        headers: {
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

  const createBackup = async () => {
    setCreatingBackup(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await api.post(`/backup/create`, {}, {
      });

      setSuccess(`Backup created: ${response.data.filename}`);
      await loadBackups();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create backup');
    } finally {
      setCreatingBackup(false);
    }
  };

  const downloadBackup = async (filename) => {
    try {
      const response = await api.get(`/backup/download/${filename}`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download backup');
    }
  };

  const restoreBackup = (filename) => {
    setConfirmModal({
      isOpen: true,
      title: 'Restore Database',
      message: `Are you sure you want to restore from ${filename}?\n\nThis will overwrite all current data and disconnect all active sessions!`,
      variant: 'danger',
      confirmText: 'Restore',
      onConfirm: () => performRestore(filename),
    });
  };

  const performRestore = async (filename) => {
    setCreatingBackup(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await api.post(`/backup/restore/${filename}`, {}, {
      });

      if (response.data.reload_required) {
        setConfirmModal({
          isOpen: true,
          title: 'Restore Complete',
          message: response.data.message + '\n\nClick "Reload" to refresh the page now.',
          variant: 'info',
          confirmText: 'Reload',
          cancelText: 'Later',
          onConfirm: () => window.location.reload(),
        });
      } else {
        setSuccess(response.data.message || 'Database restored successfully!');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to restore backup');
    } finally {
      setCreatingBackup(false);
    }
  };

  const uploadBackup = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.sql')) {
      setError('Only .sql files are allowed');
      event.target.value = '';
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      await api.post(`/backup/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSuccess(`Uploaded ${file.name}`);
      await loadBackups();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload backup');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const deleteBackup = (filename) => {
    setConfirmModal({
      isOpen: true,
      title: 'Delete Backup',
      message: `Are you sure you want to delete ${filename}?\n\nThis action cannot be undone.`,
      variant: 'danger',
      confirmText: 'Delete',
      onConfirm: () => performDelete(filename),
    });
  };

  const performDelete = async (filename) => {
    try {
      await api.delete(`/backup/${filename}`, {
      });

      setSuccess(`Deleted ${filename}`);
      await loadBackups();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete backup');
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
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

            {!discordConnected && (
              <div className={`mb-4 p-4 rounded border-l-4 ${
                isDark
                  ? 'bg-gruvbox-dark-red bg-opacity-20 border-gruvbox-dark-red'
                  : 'bg-gruvbox-light-red bg-opacity-20 border-gruvbox-light-red'
              }`}>
                <p className={`font-semibold mb-2 ${
                  isDark ? 'text-gruvbox-dark-red-bright' : 'text-gruvbox-light-red'
                }`}>
                  Discord Bot Not Configured
                </p>
                <p className={`text-sm ${
                  isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                }`}>
                  Configure <code className="px-1 rounded bg-opacity-50">DISCORD_BOT_TOKEN</code>,{' '}
                  <code className="px-1 rounded bg-opacity-50">DISCORD_NOTIFICATION_CHANNEL_ID</code>, and{' '}
                  <code className="px-1 rounded bg-opacity-50">DISCORD_TEST_CHANNEL_ID</code> in your{' '}
                  <code className="px-1 rounded bg-opacity-50">.env</code> file.
                </p>
                <p className={`text-sm mt-2 ${
                  isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                }`}>
                  Get your bot token from{' '}
                  <a
                    href="https://discord.com/developers/applications"
                    target="_blank"
                    rel="noopener noreferrer"
                    className={isDark ? 'text-gruvbox-dark-blue underline' : 'text-gruvbox-light-blue underline'}
                  >
                    Discord Developer Portal
                  </a>
                </p>
              </div>
            )}

            <div className="flex gap-3 flex-wrap">
              <button
                type="button"
                onClick={handleReconnect}
                disabled={checkingConnection}
                className={`px-4 py-2 rounded transition ${
                  checkingConnection
                    ? isDark
                      ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                      : 'bg-gruvbox-light-gray cursor-not-allowed'
                    : isDark
                      ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright'
                      : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright'
                }`}
              >
                {checkingConnection ? 'Reconnecting...' : 'Reconnect Discord Bot'}
              </button>

              <button
                type="button"
                onClick={handleTestNotifications}
                disabled={checkingConnection || !discordConnected}
                className={`px-4 py-2 rounded transition ${
                  checkingConnection || !discordConnected
                    ? isDark
                      ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                      : 'bg-gruvbox-light-gray cursor-not-allowed'
                    : isDark
                      ? 'bg-gruvbox-dark-aqua hover:bg-gruvbox-dark-aqua-bright'
                      : 'bg-gruvbox-light-aqua hover:bg-gruvbox-light-aqua-bright'
                }`}
              >
                {checkingConnection ? 'Sending...' : 'Test Notifications'}
              </button>
            </div>

            {/* Discord User ID Linking */}
            {discordConnected && (
              <div className="mt-4 p-4 rounded border border-opacity-50">
                <h3 className={`font-semibold mb-2 ${
                  isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                }`}>
                  Link Your Discord Account
                </h3>
                <p className={`text-sm mb-3 ${
                  isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                }`}>
                  Link your Discord user ID to get @mentioned in notifications. To find your Discord ID:
                  <br />
                  1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
                  <br />
                  2. Right-click your username and select "Copy User ID"
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Discord User ID (e.g., 123456789012345678)"
                    className={`flex-1 p-2 rounded border ${
                      isDark
                        ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                        : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
                    }`}
                    id="discordUserId"
                  />
                  <button
                    type="button"
                    onClick={async () => {
                      const input = document.getElementById('discordUserId');
                      const discordUserId = input.value.trim();
                      if (!discordUserId) {
                        setError('Please enter your Discord User ID');
                        return;
                      }
                      setCheckingConnection(true);
                      setError(null);
                      setSuccess(null);
                      try {
                        const response = await api.post(
                          `/discord/sync-user`,
                          { discord_user_id: discordUserId },
                        );
                        setSuccess(response.data.message);
                        input.value = '';
                      } catch (err) {
                        setError(err.response?.data?.detail || 'Failed to link Discord ID');
                      } finally {
                        setCheckingConnection(false);
                      }
                    }}
                    disabled={checkingConnection}
                    className={`px-4 py-2 rounded transition whitespace-nowrap ${
                      checkingConnection
                        ? isDark
                          ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                          : 'bg-gruvbox-light-gray cursor-not-allowed'
                        : isDark
                          ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                          : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
                    }`}
                  >
                    Link Discord
                  </button>
                </div>
              </div>
            )}

            <p className={`mt-2 text-sm ${
              isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
            }`}>
              After editing your <code className="px-1 rounded bg-opacity-50">.env</code> file, click Reconnect to apply changes without restarting.
            </p>
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

          {/* Database Backup & Restore */}
          <div className={`p-6 rounded border ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
              : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
          }`}>
            <h2 className={`text-2xl font-bold mb-4 ${
              isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
            }`}>
              Database Backup & Restore
            </h2>

            <p className={`mb-4 text-sm ${
              isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
            }`}>
              Create full database backups or restore from existing backups. Backups include all recipes, schedules, meal plans, and settings.
            </p>

            <div className="mb-4 flex gap-3">
              <button
                type="button"
                onClick={createBackup}
                disabled={creatingBackup}
                className={`px-4 py-2 rounded transition font-semibold ${
                  creatingBackup
                    ? isDark
                      ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                      : 'bg-gruvbox-light-gray cursor-not-allowed'
                    : isDark
                      ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                      : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
                }`}
              >
                {creatingBackup ? 'Creating...' : 'Create Backup'}
              </button>

              <label className={`px-4 py-2 rounded transition font-semibold cursor-pointer ${
                uploading
                  ? isDark
                    ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                    : 'bg-gruvbox-light-gray cursor-not-allowed'
                  : isDark
                    ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright'
                    : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright'
              }`}>
                {uploading ? 'Uploading...' : 'Upload Backup'}
                <input
                  type="file"
                  accept=".sql"
                  onChange={uploadBackup}
                  disabled={uploading}
                  className="hidden"
                />
              </label>
            </div>

            {backups.length === 0 ? (
              <p className={`text-sm ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
                No backups found. Create one to get started.
              </p>
            ) : (
              <div className="space-y-2">
                {backups.map((backup) => (
                  <div
                    key={backup.filename}
                    className={`p-3 rounded border ${
                      isDark
                        ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray'
                        : 'bg-gruvbox-light-bg border-gruvbox-light-gray'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className={`font-medium text-sm truncate ${
                          isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                        }`}>
                          {backup.filename}
                        </div>
                        <div className={`text-xs ${
                          isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                        }`}>
                          {formatSize(backup.size)} • {new Date(backup.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <button
                          type="button"
                          onClick={() => downloadBackup(backup.filename)}
                          className={`px-2 py-1 rounded text-xs transition ${
                            isDark
                              ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright'
                              : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright'
                          }`}
                        >
                          Download
                        </button>
                        <button
                          type="button"
                          onClick={() => restoreBackup(backup.filename)}
                          disabled={creatingBackup}
                          className={`px-2 py-1 rounded text-xs transition ${
                            creatingBackup
                              ? isDark
                                ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                                : 'bg-gruvbox-light-gray cursor-not-allowed'
                              : isDark
                                ? 'bg-gruvbox-dark-yellow hover:bg-gruvbox-dark-yellow-bright'
                                : 'bg-gruvbox-light-yellow hover:bg-gruvbox-light-yellow-bright'
                          }`}
                        >
                          Restore
                        </button>
                        <button
                          type="button"
                          onClick={() => deleteBackup(backup.filename)}
                          className={`px-2 py-1 rounded text-xs transition ${
                            isDark
                              ? 'bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright'
                              : 'bg-gruvbox-light-red hover:bg-gruvbox-light-red-bright'
                          }`}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
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

            {/* Font Selection */}
            <div className={`flex items-center justify-between p-4 rounded border ${
              isDark
                ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray'
                : 'bg-gruvbox-light-bg border-gruvbox-light-gray'
            }`}>
              <div>
                <p className={`font-semibold ${
                  isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                }`}>
                  UI Font
                </p>
                <p className={`text-sm ${
                  isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                }`}>
                  {availableFonts[currentFont]?.name} - {availableFonts[currentFont]?.description}
                </p>
              </div>
              <select
                value={currentFont}
                onChange={(e) => setFont(e.target.value)}
                className={`px-4 py-2 rounded border ${
                  isDark
                    ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg'
                    : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg'
                }`}
              >
                {Object.entries(availableFonts).map(([key, font]) => (
                  <option key={key} value={key}>
                    {font.name}
                  </option>
                ))}
              </select>
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

      <ConfirmModal
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ ...confirmModal, isOpen: false })}
        onConfirm={confirmModal.onConfirm}
        title={confirmModal.title}
        message={confirmModal.message}
        variant={confirmModal.variant}
        confirmText={confirmModal.confirmText}
        cancelText={confirmModal.cancelText}
      />
    </div>
  );
};

export default Settings;
