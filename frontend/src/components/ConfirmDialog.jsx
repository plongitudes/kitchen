import { useTheme } from '../context/ThemeContext';

const ConfirmDialog = ({ message, onConfirm, onCancel, confirmText = 'Confirm', cancelText = 'Cancel' }) => {
  const { isDark } = useTheme();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className={`max-w-md w-full p-6 rounded-lg ${
        isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'
      }`}>
        <p className={`text-lg mb-6 ${isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}`}>
          {message}
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className={`px-4 py-2 rounded transition ${
              isDark
                ? 'bg-gruvbox-dark-bg-soft hover:bg-gruvbox-dark-bg-hard text-gruvbox-dark-fg'
                : 'bg-gruvbox-light-bg-soft hover:bg-gruvbox-light-bg-hard text-gruvbox-light-fg'
            }`}
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 rounded transition ${
              isDark
                ? 'bg-gruvbox-dark-orange hover:bg-gruvbox-dark-orange-bright text-gruvbox-dark-bg'
                : 'bg-gruvbox-light-orange hover:bg-gruvbox-light-orange-bright text-gruvbox-light-bg'
            }`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;
