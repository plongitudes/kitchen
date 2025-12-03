import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { recipeAPI } from '../services/api';
import Toast from './Toast';
import UnitAutocomplete from './UnitAutocomplete';
import PrepStepAutocomplete from './PrepStepAutocomplete';

const RecipeForm = ({ recipeId = null, initialData = null }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOverIndex, setDragOverIndex] = useState(null);
  const [reimportModal, setReimportModal] = useState(false);
  const [reimporting, setReimporting] = useState(false);
  const [toast, setToast] = useState(null);
  const [prepStepsForAutocomplete, setPrepStepsForAutocomplete] = useState([]);
  const ingredientRefs = useRef([]);
  const instructionRefs = useRef([]);
  const prepStepCreationInProgress = useRef(new Set()); // Track in-flight prep step creations

  const [formData, setFormData] = useState({
    name: '',
    recipe_type: '',
    description: '',
    prep_time_minutes: '',
    cook_time_minutes: '',
    prep_notes: '',
    postmortem_notes: '',
    source_url: '',
    ingredients: [],
    instructions: [],
  });

  useEffect(() => {
    if (initialData) {
      // Build a map of prep steps for easy lookup
      const prepStepsById = {};
      if (initialData.prep_steps) {
        initialData.prep_steps.forEach(ps => {
          prepStepsById[ps.id] = ps;
        });
      }

      // Populate prep_step_description on ingredients from linked prep steps
      const ingredientsWithPrepSteps = (initialData.ingredients || []).map(ing => {
        let prep_step_description = '';
        
        // If ingredient is linked to a prep step, use that description
        if (ing.linked_prep_step_ids && ing.linked_prep_step_ids.length > 0) {
          const prepStepId = ing.linked_prep_step_ids[0]; // Take first one
          const prepStep = prepStepsById[prepStepId];
          if (prepStep) {
            prep_step_description = prepStep.description;
          }
        }
        
        // Spread ingredient but ensure prep_step_description is never null/undefined
        const { prep_step_description: _, ...restOfIng } = ing;
        return {
          ...restOfIng,
          prep_step_description,
        };
      });

      setFormData({
        name: initialData.name || '',
        recipe_type: initialData.recipe_type || '',
        description: initialData.description || '',
        prep_time_minutes: initialData.prep_time_minutes || '',
        cook_time_minutes: initialData.cook_time_minutes || '',
        prep_notes: initialData.prep_notes || '',
        postmortem_notes: initialData.postmortem_notes || '',
        source_url: initialData.source_url || '',
        ingredients: ingredientsWithPrepSteps.sort((a, b) => a.order - b.order),
        instructions: (initialData.instructions || []).sort((a, b) => a.step_number - b.step_number),
      });
    }
  }, [initialData]);

  // Fetch prep steps for autocomplete when editing a recipe
  useEffect(() => {
    const fetchPrepSteps = async () => {
      if (!recipeId) {
        setPrepStepsForAutocomplete([]);
        return;
      }

      try {
        const response = await recipeAPI.getPrepSteps(recipeId);
        // Transform backend response to autocomplete format
        // Backend provides: { id, description, ingredient_ids }
        // We need: { id, description, linked_ingredient_names }
        const transformedSteps = response.data.map(step => {
          // Match ingredient_ids to ingredient names from formData
          const linkedNames = formData.ingredients
            .filter(ing => ing.id && step.ingredient_ids.includes(ing.id))
            .map(ing => ing.ingredient_name);
          
          return {
            id: step.id,
            description: step.description,
            linked_ingredient_names: linkedNames,
          };
        });
        setPrepStepsForAutocomplete(transformedSteps);
      } catch (err) {
        console.error('Failed to fetch prep steps:', err);
        setPrepStepsForAutocomplete([]);
      }
    };

    fetchPrepSteps();
  }, [recipeId, formData.ingredients]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Validate ingredients: if unit is set, quantity must be set
    for (let i = 0; i < formData.ingredients.length; i++) {
      const ing = formData.ingredients[i];
      if (ing.unit && ing.unit !== '' && (!ing.quantity || ing.quantity === '')) {
        setError(`Ingredient "${ing.ingredient_name}": quantity is required when unit is specified`);
        setLoading(false);
        return;
      }
    }

    try {
      const payload = {
        name: formData.name,
        recipe_type: formData.recipe_type || null,
        description: formData.description || null,
        prep_time_minutes: formData.prep_time_minutes ? parseInt(formData.prep_time_minutes) : null,
        cook_time_minutes: formData.cook_time_minutes ? parseInt(formData.cook_time_minutes) : null,
        prep_notes: formData.prep_notes || null,
        postmortem_notes: formData.postmortem_notes || null,
        source_url: formData.source_url || null,
        ingredients: formData.ingredients.map(ing => ({
          ingredient_name: ing.ingredient_name,
          quantity: ing.quantity ? parseFloat(ing.quantity) : null,
          unit: ing.unit || null,
          order: ing.order,
          prep_step_description: ing.prep_step_description || null,
        })),
        instructions: formData.instructions.map(inst => ({
          step_number: inst.step_number,
          description: inst.description,
          duration_minutes: inst.duration_minutes ? parseInt(inst.duration_minutes) : null,
        })),
      };

      if (recipeId) {
        await recipeAPI.update(recipeId, payload);
      } else {
        await recipeAPI.create(payload);
      }

      // Navigate to returnTo location if provided, otherwise default to /recipes
      if (location.state?.returnTo) {
        // If we have returnTo, preserve the tab state
        navigate(location.state.returnTo, {
          state: { tab: location.state.tab }
        });
      } else {
        navigate('/recipes');
      }
    } catch (err) {
      let errorMessage = 'Failed to save recipe';
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          errorMessage = detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ');
        } else {
          errorMessage = detail;
        }
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleReimportConfirm = async () => {
    try {
      setReimporting(true);
      const response = await recipeAPI.reimport(recipeId);
      setReimportModal(false);
      // Update form with new data from reimport
      setFormData({
        ...formData,
        name: response.data.name || formData.name,
        description: response.data.description || formData.description,
        prep_time_minutes: response.data.prep_time_minutes || formData.prep_time_minutes,
        cook_time_minutes: response.data.cook_time_minutes || formData.cook_time_minutes,
        ingredients: (response.data.ingredients || []).sort((a, b) => a.order - b.order),
        instructions: (response.data.instructions || []).sort((a, b) => a.step_number - b.step_number),
        // Preserve user edits
        recipe_type: formData.recipe_type,
        prep_notes: formData.prep_notes,
        postmortem_notes: formData.postmortem_notes,
        source_url: formData.source_url,
      });
      setError(null);
      setToast({
        message: 'Recipe successfully re-imported from source! Your recipe_type, prep_notes, and postmortem_notes have been preserved.',
        type: 'success',
      });
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to re-import recipe';
      setError(errorMsg);
    } finally {
      setReimporting(false);
    }
  };

  const addIngredient = () => {
    const newIndex = formData.ingredients.length;
    setFormData({
      ...formData,
      ingredients: [
        ...formData.ingredients,
        {
          ingredient_name: '',
          quantity: '',
          unit: '',
          order: newIndex,
          prep_step_description: '',
        },
      ],
    });
    // Focus on the new ingredient's name field
    setTimeout(() => {
      if (ingredientRefs.current[newIndex]) {
        ingredientRefs.current[newIndex].focus();
      }
    }, 0);
  };

  const updateIngredient = (index, field, value) => {
    const updated = [...formData.ingredients];
    updated[index] = { ...updated[index], [field]: value };
    setFormData({ ...formData, ingredients: updated });
  };

  const removeIngredient = (index) => {
    const updated = formData.ingredients.filter((_, i) => i !== index);
    // Re-index the order
    updated.forEach((ing, i) => {
      ing.order = i;
    });
    setFormData({ ...formData, ingredients: updated });
  };

  const handlePrepStepBlur = async (prepStepText) => {
    // Only create prep steps for existing recipes (edit mode)
    if (!recipeId || !prepStepText || !prepStepText.trim()) {
      return;
    }

    const trimmedText = prepStepText.trim().toLowerCase();

    // Check if this prep step already exists
    const exists = prepStepsForAutocomplete.some(
      ps => ps.description.toLowerCase() === trimmedText
    );

    if (exists) {
      return; // Already exists, no need to create
    }

    // Check if we're already creating this prep step (prevent race condition)
    if (prepStepCreationInProgress.current.has(trimmedText)) {
      return;
    }

    // Mark this prep step as being created
    prepStepCreationInProgress.current.add(trimmedText);

    try {
      // Create the prep step on the backend
      const response = await recipeAPI.createPrepStep(recipeId, {
        description: prepStepText.trim(),
        order: prepStepsForAutocomplete.length,
      });

      // Add to autocomplete list immediately
      setPrepStepsForAutocomplete(prev => [
        ...prev,
        {
          id: response.data.id,
          description: response.data.description,
          linked_ingredient_names: [],
        },
      ]);
    } catch (err) {
      console.error('Failed to create prep step on-the-fly:', err);
      // Show error to user since this is a background operation that failed
      setToast({
        message: `Could not create prep step "${prepStepText.trim()}". You can still save the recipe.`,
        type: 'error',
      });
    } finally {
      // Always remove from in-progress set
      prepStepCreationInProgress.current.delete(trimmedText);
    }
  };

  const addInstruction = () => {
    const newIndex = formData.instructions.length;
    setFormData({
      ...formData,
      instructions: [
        ...formData.instructions,
        {
          step_number: newIndex + 1,
          description: '',
          duration_minutes: '',
        },
      ],
    });
    // Focus on the new instruction's description field
    setTimeout(() => {
      if (instructionRefs.current[newIndex]) {
        instructionRefs.current[newIndex].focus();
      }
    }, 0);
  };

  const updateInstruction = (index, field, value) => {
    const updated = [...formData.instructions];
    updated[index] = { ...updated[index], [field]: value };
    setFormData({ ...formData, instructions: updated });
  };

  const removeInstruction = (index) => {
    const updated = formData.instructions.filter((_, i) => i !== index);
    // Re-number the steps
    updated.forEach((inst, i) => {
      inst.step_number = i + 1;
    });
    setFormData({ ...formData, instructions: updated });
  };

  const cloneInstruction = (index) => {
    const original = formData.instructions[index];
    const updated = [...formData.instructions];

    // Check if there's selected text
    const selection = window.getSelection();
    const selectedText = selection.toString();

    let newDescription = '';

    // If text was selected, remove it from the original instruction and use it for new one
    if (selectedText.trim()) {
      const originalDescription = updated[index].description;
      const updatedDescription = originalDescription.replace(selectedText, '').replace(/\s+/g, ' ').trim();
      updated[index] = { ...updated[index], description: updatedDescription };

      // Use trimmed selected text for new instruction
      newDescription = selectedText.trim();
    } else {
      // No selection - check if we can split at cursor position using the ref
      const textarea = instructionRefs.current[index];

      // Check if we have the textarea ref and it has a cursor position
      if (textarea && textarea.selectionStart !== undefined) {
        const cursorPos = textarea.selectionStart;
        const originalDescription = updated[index].description;

        // Split the text at cursor position
        const beforeCursor = originalDescription.slice(0, cursorPos).trim();
        const afterCursor = originalDescription.slice(cursorPos).trim();

        // Update the current instruction with text before cursor
        updated[index] = { ...updated[index], description: beforeCursor };

        // Use text after cursor for new instruction
        newDescription = afterCursor;
      }
      // else: create empty instruction (no selection and no cursor position)
    }

    updated.splice(index + 1, 0, {
      step_number: index + 2,
      description: newDescription,
      duration_minutes: '', // Always start with empty duration
    });
    // Re-number all steps
    updated.forEach((inst, i) => {
      inst.step_number = i + 1;
    });
    setFormData({ ...formData, instructions: updated });
  };

  const moveInstruction = (index, direction) => {
    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === formData.instructions.length - 1)
    ) {
      return;
    }

    const updated = [...formData.instructions];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    [updated[index], updated[newIndex]] = [updated[newIndex], updated[index]];

    // Re-number the steps
    updated.forEach((inst, i) => {
      inst.step_number = i + 1;
    });

    setFormData({ ...formData, instructions: updated });
  };



  const handleDragStart = (e, index) => {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', index.toString());
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverIndex(index);
  };

  const handleDragLeave = () => {
    setDragOverIndex(null);
  };

  const handleDrop = (e, dropIndex) => {
    e.preventDefault();
    setDragOverIndex(null);
    const dragIndex = parseInt(e.dataTransfer.getData('text/plain'));

    if (dragIndex === dropIndex) return;

    const updated = [...formData.instructions];
    const [draggedItem] = updated.splice(dragIndex, 1);
    updated.splice(dropIndex, 0, draggedItem);

    // Re-number the steps
    updated.forEach((inst, i) => {
      inst.step_number = i + 1;
    });

    setFormData({ ...formData, instructions: updated });
  };



  return (
    <form onSubmit={handleSubmit} className="max-w-4xl mx-auto p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gruvbox-dark-orange-bright">
          {recipeId ? 'Edit Recipe' : 'New Recipe'}
        </h1>
        <div className="flex gap-2">
          {recipeId && formData.source_url && (
            <button
              type="button"
              onClick={() => setReimportModal(true)}
              className="px-4 py-2 bg-gruvbox-dark-blue hover:bg-gruvbox-dark-blue-bright rounded transition"
              disabled={loading || reimporting}
            >
              Re-import from Source
            </button>
          )}
          <button
            type="button"
            onClick={() => {
              if (location.state?.returnTo) {
                // If we have returnTo, preserve the tab state
                navigate(location.state.returnTo, {
                  state: { tab: location.state.tab }
                });
              } else {
                navigate('/recipes');
              }
            }}
            className="px-4 py-2 bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright rounded transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright text-gruvbox-dark-fg rounded font-semibold transition disabled:opacity-50"
          >
            {loading ? 'Saving...' : recipeId ? 'Update Recipe' : 'Create Recipe'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-gruvbox-dark-red text-gruvbox-dark-fg rounded">
          {error}
        </div>
      )}

      {/* Basic Info */}
      <div className="bg-gruvbox-dark-bg-soft p-6 rounded-lg border border-gruvbox-dark-gray mb-6">
        <h2 className="text-xl font-semibold mb-4 text-gruvbox-dark-green-bright">
          Basic Information
        </h2>

        <div className="mb-4">
          <label className="block mb-2">Name *</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full p-2 rounded bg-gruvbox-dark-bg border border-gruvbox-dark-gray text-gruvbox-dark-fg focus:outline-none focus:border-gruvbox-dark-orange-bright"
            required
          />
        </div>

        <div className="mb-4">
          <label className="block mb-2">Description</label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full p-2 rounded bg-gruvbox-dark-bg border border-gruvbox-dark-gray text-gruvbox-dark-fg focus:outline-none focus:border-gruvbox-dark-orange-bright resize-none overflow-hidden"
            rows="1"
            placeholder="Brief description or summary of the recipe..."
            onInput={(e) => {
              e.target.style.height = 'auto';
              e.target.style.height = e.target.scrollHeight + 'px';
            }}
            ref={(el) => {
              if (el) {
                el.style.height = 'auto';
                el.style.height = el.scrollHeight + 'px';
              }
            }}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block mb-2">Type</label>
            <input
              type="text"
              value={formData.recipe_type}
              onChange={(e) => setFormData({ ...formData, recipe_type: e.target.value })}
              className="w-full p-2 rounded bg-gruvbox-dark-bg border border-gruvbox-dark-gray text-gruvbox-dark-fg focus:outline-none focus:border-gruvbox-dark-orange-bright"
              placeholder="e.g., dinner, breakfast"
            />
          </div>
          <div>
            <label className="block mb-2">Prep Time (minutes)</label>
            <input
              type="number"
              value={formData.prep_time_minutes}
              onChange={(e) => setFormData({ ...formData, prep_time_minutes: e.target.value })}
              className="w-full p-2 rounded bg-gruvbox-dark-bg border border-gruvbox-dark-gray text-gruvbox-dark-fg focus:outline-none focus:border-gruvbox-dark-orange-bright"
              min="0"
            />
          </div>
          <div>
            <label className="block mb-2">Cook Time (minutes)</label>
            <input
              type="number"
              value={formData.cook_time_minutes}
              onChange={(e) => setFormData({ ...formData, cook_time_minutes: e.target.value })}
              className="w-full p-2 rounded bg-gruvbox-dark-bg border border-gruvbox-dark-gray text-gruvbox-dark-fg focus:outline-none focus:border-gruvbox-dark-orange-bright"
              min="0"
            />
          </div>
        </div>

        <div className="mb-4">
          <label className="block mb-2">Source URL</label>
          <input
            type="url"
            value={formData.source_url}
            onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
            className="w-full p-2 rounded bg-gruvbox-dark-bg border border-gruvbox-dark-gray text-gruvbox-dark-fg focus:outline-none focus:border-gruvbox-dark-orange-bright"
            placeholder="https://..."
          />
        </div>
      </div>

      {/* Ingredients */}
      <div className="bg-gruvbox-dark-bg-soft p-6 rounded-lg border border-gruvbox-dark-gray mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gruvbox-dark-green-bright">
            Ingredients
          </h2>
          <button
            type="button"
            onClick={addIngredient}
            className="px-3 py-1 bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright rounded transition"
          >
            + Add
          </button>
        </div>

        {formData.ingredients.length === 0 ? (
          <p className="text-gruvbox-dark-gray">No ingredients yet. Click "Add" to get started.</p>
        ) : (
          <div className="space-y-3">
            {formData.ingredients.map((ing, index) => (
              <div key={index} className="space-y-2">
                <div className="flex gap-2">
                  <input
                    ref={(el) => (ingredientRefs.current[index] = el)}
                    type="text"
                    value={ing.ingredient_name ?? ''}
                    onChange={(e) => updateIngredient(index, 'ingredient_name', e.target.value)}
                    className="flex-1 p-2 rounded bg-gruvbox-dark-bg border border-gruvbox-dark-gray text-gruvbox-dark-fg focus:outline-none focus:border-gruvbox-dark-orange-bright"
                    placeholder="Ingredient name"
                    required
                  />
                  <input
                    type="number"
                    value={ing.quantity ?? ''}
                    onChange={(e) => updateIngredient(index, 'quantity', e.target.value)}
                    className="w-24 p-2 rounded bg-gruvbox-dark-bg border border-gruvbox-dark-gray text-gruvbox-dark-fg focus:outline-none focus:border-gruvbox-dark-orange-bright"
                    placeholder="Qty"
                    step="0.01"
                    required={ing.unit && ing.unit !== ''}
                  />
                  <div className="w-40">
                    <UnitAutocomplete
                      value={ing.unit || ''}
                      onChange={(value) => updateIngredient(index, 'unit', value)}
                      required={false}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeIngredient(index)}
                    className="px-3 py-2 bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright rounded transition"
                  >
                    ×
                  </button>
                </div>
                <PrepStepAutocomplete
                  value={ing.prep_step_description ?? ''}
                  onChange={(value) => updateIngredient(index, 'prep_step_description', value)}
                  onBlur={() => handlePrepStepBlur(ing.prep_step_description)}
                  prepSteps={prepStepsForAutocomplete}
                  required={false}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Instructions */}
      <div className="bg-gruvbox-dark-bg-soft p-6 rounded-lg border border-gruvbox-dark-gray mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gruvbox-dark-green-bright">
            Instructions
          </h2>
          <button
            type="button"
            onClick={addInstruction}
            className="px-3 py-1 bg-gruvbox-dark-green hover:bg-gruvbox-dark-green-bright rounded transition"
          >
            + Add
          </button>
        </div>

        {formData.instructions.length === 0 ? (
          <p className="text-gruvbox-dark-gray">No instructions yet. Click "Add" to get started.</p>
        ) : (
          <div className="space-y-2">
            {formData.instructions.map((inst, index) => (
              <div key={index} className="relative">
                {dragOverIndex === index && (
                  <div className="absolute -top-1 left-0 right-0 h-0.5 bg-gruvbox-dark-orange-bright shadow-lg" />
                )}
                <div
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, index)}
                  className="flex gap-2 p-2 -m-2 rounded transition"
                >
                <div
                  draggable
                  onDragStart={(e) => handleDragStart(e, index)}
                  className="flex items-center cursor-grab active:cursor-grabbing hover:bg-gruvbox-dark-bg-hard p-1 -m-1 rounded"
                >
                  <span className="text-2xl text-gruvbox-dark-gray select-none">
                    ⋮⋮
                  </span>
                </div>
                <span className="w-8 p-2 text-center text-gruvbox-dark-gray">
                  {inst.step_number}.
                </span>
                <textarea
                  value={inst.description}
                  onChange={(e) => updateInstruction(index, 'description', e.target.value)}
                  className="flex-1 p-2 rounded bg-gruvbox-dark-bg border border-gruvbox-dark-gray text-gruvbox-dark-fg focus:outline-none focus:border-gruvbox-dark-orange-bright resize-none overflow-hidden"
                  placeholder="Instruction description"
                  rows="1"
                  required
                  onInput={(e) => {
                    e.target.style.height = 'auto';
                    e.target.style.height = e.target.scrollHeight + 'px';
                  }}
                  ref={(el) => {
                    instructionRefs.current[index] = el;
                    if (el) {
                      el.style.height = 'auto';
                      el.style.height = el.scrollHeight + 'px';
                    }
                  }}
                />
                <input
                  type="number"
                  value={inst.duration_minutes}
                  onChange={(e) => updateInstruction(index, 'duration_minutes', e.target.value)}
                  className="w-20 p-2 rounded bg-gruvbox-dark-bg border border-gruvbox-dark-gray text-gruvbox-dark-fg focus:outline-none focus:border-gruvbox-dark-orange-bright"
                  placeholder="min"
                  min="0"
                />
                <div className="flex flex-col gap-1 self-stretch">
                  <button
                    type="button"
                    onClick={() => removeInstruction(index)}
                    className="flex-1 px-3 bg-gruvbox-dark-red hover:bg-gruvbox-dark-red-bright rounded transition"
                    title="Remove step"
                  >
                    ×
                  </button>
                  <button
                    type="button"
                    onClick={() => cloneInstruction(index)}
                    className="flex-1 px-3 bg-gruvbox-dark-aqua hover:bg-gruvbox-dark-aqua-bright rounded transition"
                    title="Insert step (splits at cursor or selection)"
                  >
                    ⎘
                  </button>
                </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Notes */}
      <div className="bg-gruvbox-dark-bg-soft p-6 rounded-lg border border-gruvbox-dark-gray mb-6">
        <h2 className="text-xl font-semibold mb-4 text-gruvbox-dark-green-bright">
          Notes
        </h2>

        <div className="mb-4">
          <label className="block mb-2">Prep Notes</label>
          <textarea
            value={formData.prep_notes}
            onChange={(e) => setFormData({ ...formData, prep_notes: e.target.value })}
            className="w-full p-2 rounded bg-gruvbox-dark-bg border border-gruvbox-dark-gray text-gruvbox-dark-fg focus:outline-none focus:border-gruvbox-dark-orange-bright"
            rows="3"
            placeholder="Notes about preparation..."
          />
        </div>

        <div>
          <label className="block mb-2">Postmortem Notes</label>
          <textarea
            value={formData.postmortem_notes}
            onChange={(e) => setFormData({ ...formData, postmortem_notes: e.target.value })}
            className="w-full p-2 rounded bg-gruvbox-dark-bg border border-gruvbox-dark-gray text-gruvbox-dark-fg focus:outline-none focus:border-gruvbox-dark-orange-bright"
            rows="3"
            placeholder="Notes after cooking..."
          />
        </div>
      </div>

      {/* Re-import Confirmation Modal */}
      {reimportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gruvbox-dark-bg-soft p-6 rounded-lg border border-gruvbox-dark-orange-bright max-w-lg">
            <h3 className="text-xl font-bold mb-4 text-gruvbox-dark-orange-bright">
              Re-import Recipe from Source?
            </h3>
            <p className="mb-4 text-gruvbox-dark-fg">
              This will fetch the latest data from the source URL and update the recipe name, description,
              prep/cook times, ingredients, and instructions.
            </p>
            <p className="mb-4 text-gruvbox-dark-yellow">
              <strong>Preserved:</strong> Your recipe_type, prep_notes, and postmortem_notes will be kept.
            </p>
            <p className="mb-6 text-gruvbox-dark-red">
              <strong>Warning:</strong> Current ingredients and instructions will be replaced with the latest
              data from the source.
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setReimportModal(false)}
                disabled={reimporting}
                className="px-4 py-2 bg-gruvbox-dark-gray hover:bg-gruvbox-dark-gray-bright rounded transition disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleReimportConfirm}
                disabled={reimporting}
                className="px-4 py-2 bg-gruvbox-dark-orange hover:bg-gruvbox-dark-orange-bright text-gruvbox-dark-fg rounded font-semibold transition disabled:opacity-50"
              >
                {reimporting ? 'Re-importing...' : 'Re-import Recipe'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </form>
  );
};

export default RecipeForm;
