import { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import api from '../services/api';
import ConfirmModal from '../components/ConfirmModal';


const Backup = () => {
  const { isDark } = useTheme();
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [confirmModal, setConfirmModal] = useState({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: null,
    variant: 'warning',
    confirmText: 'Confirm',
  });

  useEffect(() => {
    loadBackups();
  }, []);

  const loadBackups = async () => {
    try {
      const response = await api.get(`/backup/list`, {
      });
      setBackups(response.data);
    } catch (err) {
      console.error('Failed to load backups:', err);
    }
  };

  const createBackup = async () => {
    setLoading(true);
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
      setLoading(false);
    }
  };

  const downloadBackup = async (filename) => {
    try {
      const response = await api.get(`/backup/download/${filename}`, {
        responseType: 'blob',
      });

      // Create download link
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
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await api.post(`/backup/restore/${filename}`, {}, {
      });

      // Check if reload is required
      if (response.data.reload_required) {
        // Show success and prompt reload
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
      setLoading(false);
    }
  };

  const uploadBackup = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.sql')) {
      setError('Only .sql files are allowed');
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
      event.target.value = ''; // Reset file input
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

  return (
    <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      <div className="max-w-4xl mx-auto">
        <h1 className={`text-3xl font-bold mb-6 ${
          isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
        }`}>
          Database Backup & Restore
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

        <div className="mb-6 flex gap-3">
          <button
            onClick={createBackup}
            disabled={loading}
            className={`px-6 py-3 rounded font-semibold transition ${
              loading
                ? isDark
                  ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                  : 'bg-gruvbox-light-gray cursor-not-allowed'
                : isDark
                  ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                  : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
            }`}
          >
            {loading ? 'Creating...' : 'Create Backup'}
          </button>

          <label className={`px-6 py-3 rounded font-semibold transition cursor-pointer ${
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

        <div className={`p-6 rounded border ${
          isDark
            ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
            : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
        }`}>
          <h2 className={`text-2xl font-bold mb-4 ${
            isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
          }`}>
            Available Backups
          </h2>

          {backups.length === 0 ? (
            <p className={isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}>
              No backups found. Create one to get started.
            </p>
          ) : (
            <div className="space-y-3">
              {backups.map((backup) => (
                <div
                  key={backup.filename}
                  className={`p-4 rounded border ${
                    isDark
                      ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray'
                      : 'bg-gruvbox-light-bg border-gruvbox-light-gray'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className={`font-semibold ${
                        isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                      }`}>
                        {backup.filename}
                      </div>
                      <div className={`text-sm ${
                        isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                      }`}>
                        {formatSize(backup.size)} • {new Date(backup.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => downloadBackup(backup.filename)}
                        className={`px-3 py-1 rounded text-sm transition ${
                          isDark
                            ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright'
                            : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright'
                        }`}
                      >
                        Download
                      </button>
                      <button
                        onClick={() => restoreBackup(backup.filename)}
                        disabled={loading}
                        className={`px-3 py-1 rounded text-sm transition ${
                          loading
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
                        onClick={() => deleteBackup(backup.filename)}
                        className={`px-3 py-1 rounded text-sm transition ${
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

export default Backup;
