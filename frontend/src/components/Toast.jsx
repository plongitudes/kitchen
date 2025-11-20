import { useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';

const Toast = ({ message, type = 'info', onClose, duration = 5000 }) => {
  const { isDark } = useTheme();

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const getTypeStyles = () => {
    switch (type) {
      case 'success':
        return isDark
          ? 'bg-gruvbox-dark-green text-gruvbox-dark-bg border-gruvbox-dark-green-bright'
          : 'bg-gruvbox-light-green text-gruvbox-light-bg border-gruvbox-light-green-bright';
      case 'error':
        return isDark
          ? 'bg-gruvbox-dark-red text-gruvbox-dark-bg border-gruvbox-dark-red-bright'
          : 'bg-gruvbox-light-red text-gruvbox-light-bg border-gruvbox-light-red-bright';
      case 'warning':
        return isDark
          ? 'bg-gruvbox-dark-yellow text-gruvbox-dark-bg border-gruvbox-dark-yellow-bright'
          : 'bg-gruvbox-light-yellow text-gruvbox-light-bg border-gruvbox-light-yellow-bright';
      default:
        return isDark
          ? 'bg-gruvbox-dark-blue text-gruvbox-dark-bg border-gruvbox-dark-blue-bright'
          : 'bg-gruvbox-light-blue text-gruvbox-light-bg border-gruvbox-light-blue-bright';
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in">
      <div className={`px-6 py-4 rounded-lg border-2 shadow-lg max-w-md ${getTypeStyles()}`}>
        <div className="flex items-start justify-between gap-4">
          <p className="flex-1">{message}</p>
          <button
            onClick={onClose}
            className="text-xl leading-none opacity-70 hover:opacity-100 transition"
          >
            ×
          </button>
        </div>
      </div>
    </div>
  );
};

export default Toast;
