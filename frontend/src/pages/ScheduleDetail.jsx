import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { scheduleAPI, mealPlanAPI, templateAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import TemplateFormModal from '../components/TemplateFormModal';

const ScheduleDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const [schedule, setSchedule] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reordering, setReordering] = useState(false);
  const [starting, setStarting] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showStartModal, setShowStartModal] = useState(false);
  const [newlyCreatedTemplateId, setNewlyCreatedTemplateId] = useState(null);

  useEffect(() => {
    loadScheduleAndTemplates();
  }, [id]);

  const loadScheduleAndTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await scheduleAPI.get(id);
      setSchedule(response.data);
      setTemplates(response.data.week_mappings || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load schedule');
    } finally {
      setLoading(false);
    }
  };

  const handleDragStart = (e, index) => {
    if (!reordering) return;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', index.toString());
  };

  const handleDragOver = (e) => {
    if (!reordering) return;
    e.preventDefault();
  };

  const handleDrop = async (e, dropIndex) => {
    if (!reordering) return;
    e.preventDefault();
    const dragIndex = parseInt(e.dataTransfer.getData('text/plain'));
    if (dragIndex === dropIndex) return;

    const updated = [...templates];
    const [draggedItem] = updated.splice(dragIndex, 1);
    updated.splice(dropIndex, 0, draggedItem);

    // Optimistically update UI
    setTemplates(updated);

    // Save to backend
    try {
      const templateIds = updated.map(t => t.week_template_id);
      await scheduleAPI.reorderTemplates(id, templateIds);
    } catch (err) {
      // Revert on error
      setError('Failed to reorder templates');
      loadScheduleAndTemplates();
    }
  };

  const handleStartSchedule = async (weekTemplateId, position) => {
    try {
      setStarting(true);
      setError(null);
      await mealPlanAPI.startOnWeek(id, {
        week_template_id: weekTemplateId,
        position: position,
      });
      setShowStartModal(false);
      alert('Schedule started! View your current meal plan.');
      navigate(`/meal-plans/current?sequence_id=${id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start schedule');
    } finally {
      setStarting(false);
    }
  };

  const handleRemoveTemplate = async (templateId) => {
    if (!confirm('Remove this template from the schedule? It will no longer appear in the rotation.')) {
      return;
    }

    try {
      await scheduleAPI.removeTemplate(id, templateId);
      await loadScheduleAndTemplates();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove template');
    }
  };

  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  if (loading) {
    return (
      <div className="p-8">
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Loading schedule...
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

  if (!schedule) {
    return (
      <div className="p-8">
        <div className={`text-center ${isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}`}>
          Schedule not found
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen p-8 ${isDark ? 'bg-gruvbox-dark-bg' : 'bg-gruvbox-light-bg'}`}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
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
                {schedule.name}
              </h1>
            </div>
            <button
              onClick={() => setShowStartModal(true)}
              disabled={starting || templates.length === 0}
              className={`px-6 py-3 rounded font-semibold transition ${
                starting || templates.length === 0
                  ? isDark
                    ? 'bg-gruvbox-dark-gray cursor-not-allowed'
                    : 'bg-gruvbox-light-gray cursor-not-allowed'
                  : isDark
                    ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright'
                    : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright'
              }`}
            >
              {starting ? 'Starting...' : 'Start This Schedule'}
            </button>
          </div>

          <div className={`p-4 rounded border ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
              : 'bg-gruvbox-light-bg-soft border-gruvbox-light-gray'
          }`}>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className={isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}>
                  Current Week:
                </span>
                <span className="ml-2 font-semibold">Week {schedule.current_week_index + 1}</span>
              </div>
              <div>
                <span className={isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'}>
                  Advances:
                </span>
                <span className="ml-2">
                  {dayNames[schedule.advancement_day_of_week]} at {schedule.advancement_time}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Week Templates */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className={`text-2xl font-bold ${
              isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
            }`}>
              Week Templates
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => setReordering(!reordering)}
                className={`px-4 py-2 rounded transition ${
                  reordering
                    ? isDark
                      ? 'bg-gruvbox-dark-yellow text-gruvbox-dark-bg'
                      : 'bg-gruvbox-light-yellow text-gruvbox-light-bg'
                    : isDark
                      ? 'bg-gruvbox-dark-bg-soft hover:bg-gruvbox-dark-bg-hard'
                      : 'bg-gruvbox-light-bg-soft hover:bg-gruvbox-light-bg-hard'
                }`}
              >
                {reordering ? 'Done Reordering' : 'Reorder Templates'}
              </button>
              <button
                onClick={() => setShowAddModal(true)}
                className={`px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg'
                    : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg'
                }`}
              >
                Add Template
              </button>
            </div>
          </div>

          {templates.length === 0 ? (
            <div className={`text-center p-8 border-2 border-dashed rounded ${
              isDark ? 'border-gruvbox-dark-gray text-gruvbox-dark-gray' : 'border-gruvbox-light-gray text-gruvbox-light-gray'
            }`}>
              <p className="mb-4">No templates in this schedule yet</p>
              <button
                onClick={() => setShowAddModal(true)}
                className={`inline-block px-4 py-2 rounded transition ${
                  isDark
                    ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg'
                    : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg'
                }`}
              >
                Add Your First Template
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {templates.map((mapping, index) => {
                const isCurrent = index === schedule.current_week_index;
                const isRemoved = mapping.removed_at !== null;
                return (
                  <div
                    key={mapping.id}
                    draggable={reordering && !isRemoved}
                    onDragStart={(e) => handleDragStart(e, index)}
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(e, index)}
                    className={`flex items-center gap-4 p-4 rounded border-2 transition ${
                      reordering && !isRemoved ? 'cursor-move' : ''
                    } ${
                      isRemoved
                        ? 'opacity-50'
                        : isCurrent
                        ? isDark
                          ? 'border-gruvbox-dark-orange bg-gruvbox-dark-bg-soft'
                          : 'border-gruvbox-light-orange bg-gruvbox-light-bg-soft'
                        : isDark
                          ? 'border-gruvbox-dark-gray bg-gruvbox-dark-bg-soft hover:bg-gruvbox-dark-bg-hard'
                          : 'border-gruvbox-light-gray bg-gruvbox-light-bg-soft hover:bg-gruvbox-light-bg-hard'
                    }`}
                  >
                    {reordering && !isRemoved && (
                      <div className="flex items-center cursor-grab active:cursor-grabbing">
                        <span className={`text-2xl select-none ${
                          isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                        }`}>
                          ⋮⋮
                        </span>
                      </div>
                    )}

                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className={`font-semibold ${
                          isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                        }`}>
                          Position {mapping.position}
                        </span>
                        <Link
                          to={`/templates/${mapping.week_template_id}`}
                          className={`text-lg font-bold hover:underline ${
                            isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                          }`}
                        >
                          {mapping.week_template?.name || 'Unknown Template'}
                        </Link>
                        {isCurrent && !isRemoved && (
                          <span className={`px-2 py-1 text-xs rounded ${
                            isDark
                              ? 'bg-gruvbox-dark-orange text-gruvbox-dark-bg'
                              : 'bg-gruvbox-light-orange text-gruvbox-light-bg'
                          }`}>
                            CURRENT
                          </span>
                        )}
                        {isRemoved && (
                          <span className={`px-2 py-1 text-xs rounded ${
                            isDark
                              ? 'bg-gruvbox-dark-gray text-gruvbox-dark-bg'
                              : 'bg-gruvbox-light-gray text-gruvbox-light-bg'
                          }`}>
                            REMOVED
                          </span>
                        )}
                        {mapping.week_template?.retired_at && (
                          <span className={`px-2 py-1 text-xs rounded ${
                            isDark
                              ? 'bg-gruvbox-dark-red text-gruvbox-dark-bg'
                              : 'bg-gruvbox-light-red text-gruvbox-light-bg'
                          }`}>
                            TEMPLATE RETIRED
                          </span>
                        )}
                      </div>
                    </div>

                    {!reordering && !isRemoved && (
                      <div className="flex gap-2">
                        <Link
                          to={`/templates/${mapping.week_template_id}`}
                          className={`px-4 py-2 rounded transition ${
                            isDark
                              ? 'bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright text-gruvbox-dark-bg'
                              : 'bg-gruvbox-light-blue hover:bg-gruvbox-light-blue-bright text-gruvbox-light-bg'
                          }`}
                        >
                          View Template
                        </Link>
                        <button
                          onClick={() => handleRemoveTemplate(mapping.week_template_id)}
                          className={`px-4 py-2 rounded transition ${
                            isDark
                              ? 'bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright text-gruvbox-dark-bg'
                              : 'bg-gruvbox-light-red hover:bg-gruvbox-light-red-bright text-gruvbox-light-bg'
                          }`}
                        >
                          Remove
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Add Template Modal */}
      {showAddModal && <AddTemplateModal />}

      {/* Start Schedule Modal */}
      {showStartModal && <StartScheduleModal />}

      {/* Create Template Modal */}
      <TemplateFormModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={(newTemplate) => {
          setShowCreateModal(false);
          // Store the new template ID for auto-selection
          setNewlyCreatedTemplateId(newTemplate.id);
        }}
      />
    </div>
  );

  function AddTemplateModal() {
    const [availableTemplates, setAvailableTemplates] = useState([]);
    const [selectedTemplateIds, setSelectedTemplateIds] = useState(new Set());
    const [loading, setLoading] = useState(true);
    const [adding, setAdding] = useState(false);

    useEffect(() => {
      loadAvailableTemplates();
    }, []);

    useEffect(() => {
      // When create modal closes, refresh templates and auto-select if one was created
      if (!showCreateModal && newlyCreatedTemplateId) {
        loadAvailableTemplates().then(() => {
          setSelectedTemplateIds(new Set([newlyCreatedTemplateId]));
          setNewlyCreatedTemplateId(null);
        });
      }
    }, [showCreateModal]);

    const loadAvailableTemplates = async () => {
      try {
        setLoading(true);
        const response = await templateAPI.list({ include_retired: false });
        setAvailableTemplates(response.data);
      } catch (err) {
        setError('Failed to load templates');
      } finally {
        setLoading(false);
      }
    };

    const toggleTemplate = (templateId) => {
      const newSelected = new Set(selectedTemplateIds);
      if (newSelected.has(templateId)) {
        newSelected.delete(templateId);
      } else {
        newSelected.add(templateId);
      }
      setSelectedTemplateIds(newSelected);
    };

    const selectAll = () => {
      setSelectedTemplateIds(new Set(availableTemplates.map(t => t.id)));
    };

    const selectNone = () => {
      setSelectedTemplateIds(new Set());
    };

    const handleAdd = async () => {
      if (selectedTemplateIds.size === 0) {
        alert('Please select at least one template');
        return;
      }

      try {
        setAdding(true);
        // Add templates sequentially to maintain order
        for (const templateId of selectedTemplateIds) {
          await scheduleAPI.addTemplate(id, { week_template_id: templateId });
        }
        setShowAddModal(false);
        await loadScheduleAndTemplates();
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to add templates');
      } finally {
        setAdding(false);
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className={`rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto ${
          isDark ? 'bg-gruvbox-dark-bg-soft' : 'bg-white'
        }`}>
          <h3 className={`text-xl font-bold mb-4 ${
            isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
          }`}>
            Add Templates to Schedule
          </h3>

          {loading ? (
            <div className={`text-center py-8 ${
              isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
            }`}>
              <div className="animate-pulse">Loading templates...</div>
            </div>
          ) : (
            <>
              {/* Selection controls */}
              <div className="flex justify-between items-center mb-4">
                <div className={`text-sm ${
                  isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                }`}>
                  {selectedTemplateIds.size} selected
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={selectAll}
                    className={`px-3 py-1 text-sm rounded transition ${
                      isDark
                        ? 'bg-gruvbox-dark-bg hover:bg-gruvbox-dark-bg-hard border border-gruvbox-dark-gray'
                        : 'bg-gruvbox-light-bg hover:bg-gruvbox-light-bg-hard border border-gruvbox-light-gray'
                    }`}
                  >
                    Select All
                  </button>
                  <button
                    type="button"
                    onClick={selectNone}
                    className={`px-3 py-1 text-sm rounded transition ${
                      isDark
                        ? 'bg-gruvbox-dark-bg hover:bg-gruvbox-dark-bg-hard border border-gruvbox-dark-gray'
                        : 'bg-gruvbox-light-bg hover:bg-gruvbox-light-bg-hard border border-gruvbox-light-gray'
                    }`}
                  >
                    Select None
                  </button>
                </div>
              </div>

              {/* Template list */}
              {availableTemplates.length === 0 ? (
                <div className={`text-center py-8 ${
                  isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
                }`}>
                  No templates available. Create one first!
                </div>
              ) : (
                <div className={`space-y-2 mb-4 max-h-60 overflow-y-auto p-2 rounded border ${
                  isDark ? 'border-gruvbox-dark-gray' : 'border-gruvbox-light-gray'
                }`}>
                  {availableTemplates.map(template => (
                    <label
                      key={template.id}
                      className={`flex items-center gap-3 p-3 rounded cursor-pointer transition ${
                        selectedTemplateIds.has(template.id)
                          ? isDark
                            ? 'bg-gruvbox-dark-green bg-opacity-20 border border-gruvbox-dark-green'
                            : 'bg-gruvbox-light-green bg-opacity-20 border border-gruvbox-light-green'
                          : isDark
                            ? 'bg-gruvbox-dark-bg hover:bg-gruvbox-dark-bg-hard border border-transparent'
                            : 'bg-gruvbox-light-bg hover:bg-gruvbox-light-bg-hard border border-transparent'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedTemplateIds.has(template.id)}
                        onChange={() => toggleTemplate(template.id)}
                        className="w-4 h-4"
                      />
                      <span className={`flex-1 ${
                        isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                      }`}>
                        {template.name}
                      </span>
                    </label>
                  ))}
                </div>
              )}

              <div className={`mb-4 text-center ${
                isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
              }`}>
                <span className="text-sm">Don't see the template you need?</span>
              </div>

              <button
                type="button"
                onClick={() => setShowCreateModal(true)}
                className={`w-full px-4 py-2 rounded mb-4 transition ${
                  isDark
                    ? 'bg-gruvbox-dark-purple hover:bg-gruvbox-dark-purple-bright text-gruvbox-dark-bg'
                    : 'bg-gruvbox-light-purple hover:bg-gruvbox-light-purple-bright text-gruvbox-light-bg'
                }`}
              >
                + Create New Template
              </button>

              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowAddModal(false)}
                  className={`px-4 py-2 rounded transition ${
                    isDark
                      ? 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright text-gruvbox-dark-fg'
                      : 'bg-gruvbox-light-gray hover:bg-gruvbox-light-gray-bright text-gruvbox-light-fg'
                  }`}
                >
                  Cancel
                </button>
                <button
                  onClick={handleAdd}
                  disabled={adding || selectedTemplateIds.size === 0}
                  className={`px-4 py-2 rounded transition ${
                    isDark
                      ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg disabled:opacity-50'
                      : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg disabled:opacity-50'
                  }`}
                >
                  {adding ? 'Adding...' : `Add ${selectedTemplateIds.size} Template${selectedTemplateIds.size !== 1 ? 's' : ''}`}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  function StartScheduleModal() {
    const [selectedWeek, setSelectedWeek] = useState(null);
    const activeTemplates = templates.filter(t => !t.removed_at);

    const handleStart = async () => {
      if (!selectedWeek) {
        alert('Please select a week to start with');
        return;
      }
      await handleStartSchedule(selectedWeek.week_template_id, selectedWeek.position);
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className={`rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto ${
          isDark ? 'bg-gruvbox-dark-bg-soft' : 'bg-white'
        }`}>
          <h3 className={`text-xl font-bold mb-4 ${
            isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
          }`}>
            Choose Starting Week
          </h3>

          <p className={`mb-4 text-sm ${
            isDark ? 'text-gruvbox-dark-gray' : 'text-gruvbox-light-gray'
          }`}>
            Select which week in the sequence you want to start with. The schedule will begin this week (starting from the most recent Sunday) and continue rotating through the sequence.
          </p>

          {/* Week list */}
          <div className={`space-y-2 mb-4 max-h-96 overflow-y-auto p-2 rounded border ${
            isDark ? 'border-gruvbox-dark-gray' : 'border-gruvbox-light-gray'
          }`}>
            {activeTemplates.map((mapping) => (
              <label
                key={mapping.id}
                className={`flex items-center gap-3 p-4 rounded cursor-pointer transition border-2 ${
                  selectedWeek?.id === mapping.id
                    ? isDark
                      ? 'bg-gruvbox-dark-green bg-opacity-20 border-gruvbox-dark-green'
                      : 'bg-gruvbox-light-green bg-opacity-20 border-gruvbox-light-green'
                    : isDark
                      ? 'bg-gruvbox-dark-bg hover:bg-gruvbox-dark-bg-hard border-gruvbox-dark-gray'
                      : 'bg-gruvbox-light-bg hover:bg-gruvbox-light-bg-hard border-gruvbox-light-gray'
                }`}
              >
                <input
                  type="radio"
                  name="selectedWeek"
                  checked={selectedWeek?.id === mapping.id}
                  onChange={() => setSelectedWeek(mapping)}
                  className="w-4 h-4"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold ${
                      isDark ? 'text-gruvbox-dark-orange' : 'text-gruvbox-light-orange'
                    }`}>
                      Week {mapping.position}
                    </span>
                    <span className={`text-lg ${
                      isDark ? 'text-gruvbox-dark-fg' : 'text-gruvbox-light-fg'
                    }`}>
                      {mapping.week_template?.name || 'Unknown Template'}
                    </span>
                  </div>
                </div>
              </label>
            ))}
          </div>

          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setShowStartModal(false)}
              disabled={starting}
              className={`px-4 py-2 rounded transition ${
                isDark
                  ? 'bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright text-gruvbox-dark-fg disabled:opacity-50'
                  : 'bg-gruvbox-light-gray hover:bg-gruvbox-light-gray-bright text-gruvbox-light-fg disabled:opacity-50'
              }`}
            >
              Cancel
            </button>
            <button
              onClick={handleStart}
              disabled={starting || !selectedWeek}
              className={`px-4 py-2 rounded transition ${
                isDark
                  ? 'bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-bg disabled:opacity-50'
                  : 'bg-gruvbox-light-green hover:bg-gruvbox-light-green-bright text-gruvbox-light-bg disabled:opacity-50'
              }`}
            >
              {starting ? 'Starting...' : 'Start Schedule'}
            </button>
          </div>
        </div>
      </div>
    );
  }
};

export default ScheduleDetail;
