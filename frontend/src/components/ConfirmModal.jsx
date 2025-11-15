import { useTheme } from '../context/ThemeContext';

const ConfirmModal = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'warning' // 'warning', 'danger', 'info'
}) => {
  const { isDark } = useTheme();

  if (!isOpen) return null;

  const getButtonColors = () => {
    if (variant === 'danger') {
      return isDark
        ? 'bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright'
        : 'bg-gruvbox-light-red hover:bg-gruvbox-light-red-bright';
    }
    if (variant === 'info') {
      return isDark
        ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright'
        : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright';
    }
    return isDark
      ? 'bg-gruvbox-dark-yellow hover:bg-gruvbox-dark-yellow-bright text-gruvbox-dark-bg'
      : 'bg-gruvbox-light-yellow hover:bg-gruvbox-light-yellow-bright text-gruvbox-light-bg';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`rounded-lg p-6 max-w-lg w-full mx-4 border ${
        isDark
          ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
          : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
      }`}>
        <h2 className={`text-2xl font-bold mb-4 ${
          isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
        }`}>
          {title}
        </h2>

        <div className={`mb-6 ${
          isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
        }`}>
          {typeof message === 'string' ? (
            <p className="whitespace-pre-wrap">{message}</p>
          ) : (
            message
          )}
        </div>

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className={`px-4 py-2 rounded transition ${
              isDark
                ? 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright'
                : 'bg-gruvbox-light-gray hover:bg-gruvbox-light-gray-bright'
            }`}
          >
            {cancelText}
          </button>
          <button
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={`px-4 py-2 rounded font-semibold transition ${getButtonColors()}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;
