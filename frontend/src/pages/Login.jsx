import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const { login, register } = useAuth();
  const { isDark } = useTheme();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const result = isRegistering
      ? await register(username, password)
      : await login(username, password);

    if (result.success) {
      navigate('/');
    } else {
      setError(result.error);
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center ${
      isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'
    }`}>
      <div className={`p-8 rounded-lg shadow-lg w-full max-w-md border ${
        isDark
          ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
          : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
      }`}>
        <h1 className={`text-3xl font-bold mb-6 ${
          isDark ? 'text-gruvbox-dark-orange-bright' : 'text-gruvbox-light-orange-bright'
        }`}>
          {isRegistering ? 'Register' : 'Login'}
        </h1>
        {error && (
          <div className={`mb-4 p-3 rounded ${
            isDark
              ? 'bg-gruvbox-dark-red text-gruvbox-dark-bg'
              : 'bg-gruvbox-light-red text-gruvbox-light-bg'
          }`}>
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className={`block mb-2 ${
              isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
            }`}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={`w-full p-2 rounded border focus:outline-none ${
                isDark
                  ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg focus:border-gruvbox-dark-orange-bright'
                  : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg focus:border-gruvbox-light-orange-bright'
              }`}
              required
            />
          </div>
          <div className="mb-6">
            <label className={`block mb-2 ${
              isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
            }`}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={`w-full p-2 rounded border focus:outline-none ${
                isDark
                  ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg focus:border-gruvbox-dark-orange-bright'
                  : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg focus:border-gruvbox-light-orange-bright'
              }`}
              required
            />
          </div>
          <button
            type="submit"
            className={`w-full p-2 rounded font-semibold transition ${
              isDark
                ? 'bg-gruvbox-dark-orange hover:bg-gruvbox-dark-orange-bright text-gruvbox-dark-bg'
                : 'bg-gruvbox-light-orange hover:bg-gruvbox-light-orange-bright text-gruvbox-light-bg'
            }`}
          >
            {isRegistering ? 'Register' : 'Login'}
          </button>
        </form>
        <button
          onClick={() => setIsRegistering(!isRegistering)}
          className={`mt-4 hover:underline ${
            isDark ? 'text-gruvbox-dark-blue-bright' : 'text-gruvbox-light-blue-bright'
          }`}
        >
          {isRegistering
            ? 'Already have an account? Login'
            : "Don't have an account? Register"}
        </button>
      </div>
    </div>
  );
};

export default Login;
