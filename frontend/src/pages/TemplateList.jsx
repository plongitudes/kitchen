import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { templateAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';

const TemplateList = () => {
  const { isDark } = useTheme();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showRetired, setShowRetired] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const loadTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await templateAPI.list({ include_retired: showRetired });
      setTemplates(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTemplates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showRetired]);

  const filteredTemplates = templates.filter(template =>
    template.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="p-8">
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Loading templates...
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
            Week Templates
          </h1>
          <Link
            to="/templates/new"
            className={`px-4 py-2 rounded transition ${
              isDark
                ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg'
                : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg'
            }`}
          >
            Create New Template
          </Link>
        </div>

        {/* Search and filter controls */}
        <div className="mb-6 flex gap-4">
          <input
            type="text"
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={`flex-1 px-4 py-2 rounded ${
              isDark
                ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray text-gruvbox-dark-fg'
                : 'bg-white border-gruvbox-light-gray text-gruvbox-light-fg'
            } border`}
          />
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showRetired}
              onChange={(e) => setShowRetired(e.target.checked)}
              className="rounded"
            />
            <span className={isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'}>
              Show retired
            </span>
          </label>
        </div>

        {filteredTemplates.length === 0 ? (
          <div className={`text-center p-8 border-2 border-dashed rounded ${
            isDark ? 'border-gruvbox-dark-gray text-gruvbox-dark-gray' : 'border-gruvbox-light-gray text-gruvbox-light-gray'
          }`}>
            <p className="mb-4">
              {templates.length === 0 ? 'No templates yet' : 'No templates match your search'}
            </p>
            {templates.length === 0 && (
              <Link
                to="/templates/new"
                className={`inline-block px-4 py-2 rounded ${
                  isDark ? 'bg-gruvbox-dark-blue text-gruvbox-dark-bg' : 'bg-gruvbox-light-blue text-gruvbox-light-bg'
                }`}
              >
                Create Your First Template
              </Link>
            )}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredTemplates.map((template) => (
              <Link
                key={template.id}
                to={`/templates/${template.id}`}
                className={`p-6 rounded-lg transition border-2 ${
                  template.retired_at
                    ? isDark
                      ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray opacity-60'
                      : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray opacity-60'
                    : isDark
                    ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray hover:border-gruvbox-dark-orange'
                    : 'bg-white border-gruvbox-light-gray hover:border-gruvbox-light-orange'
                }`}
              >
                <h3 className={`text-xl font-semibold mb-2 ${
                  isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
                }`}>
                  {template.name}
                  {template.retired_at && (
                    <span className={`ml-2 text-sm ${
                      isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                    }`}>
                      (Retired)
                    </span>
                  )}
                </h3>
                <div className={`text-sm ${
                  isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                }`}>
                  <div>Created: {new Date(template.created_at).toLocaleDateString()}</div>
                  {template.retired_at && (
                    <div>Retired: {new Date(template.retired_at).toLocaleDateString()}</div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TemplateList;
