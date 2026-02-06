import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../utils/test-utils';
import RecipeForm from '../../../components/RecipeForm';
import { recipeAPI } from '../../../services/api';

// Mock the API
vi.mock('../../../services/api', () => ({
  recipeAPI: {
    create: vi.fn(),
    update: vi.fn(),
    get: vi.fn(),
    reimport: vi.fn(),
    getPrepSteps: vi.fn().mockResolvedValue({ data: [] }),
  },
}));

// Mock useLocation and useNavigate
const mockNavigate = vi.fn();
const mockLocation = { state: null };

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockLocation,
  };
});

// --- Fixtures ---

const validRecipeData = {
  id: 'recipe-123',
  name: 'Test Recipe',
  recipe_type: 'dinner',
  description: 'A test recipe',
  prep_time_minutes: 15,
  cook_time_minutes: 30,
  source_url: 'https://example.com/recipe',
  ingredients: [
    { id: 'ing-1', ingredient_name: 'flour', quantity: 2, unit: 'cup', order: 0 },
    { id: 'ing-2', ingredient_name: 'sugar', quantity: 1, unit: 'tbsp', order: 1 },
  ],
  instructions: [
    { id: 'inst-1', step_number: 1, description: 'Mix ingredients' },
    { id: 'inst-2', step_number: 2, description: 'Bake at 350F' },
  ],
  prep_steps: [],
};

const recipeWithPrepSteps = {
  ...validRecipeData,
  prep_steps: [
    { id: 'ps-1', description: 'Dice finely' },
    { id: 'ps-2', description: 'Julienne' },
  ],
  ingredients: [
    {
      id: 'ing-1', ingredient_name: 'onion', quantity: 1, unit: '',
      order: 0, linked_prep_step_ids: ['ps-1'],
    },
    {
      id: 'ing-2', ingredient_name: 'carrot', quantity: 2, unit: '',
      order: 1, linked_prep_step_ids: ['ps-1'],
    },
    {
      id: 'ing-3', ingredient_name: 'bell pepper', quantity: 1, unit: '',
      order: 2, linked_prep_step_ids: [],
    },
  ],
};

describe('RecipeForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.state = null;
  });

  // ── Rendering ──

  describe('Rendering', () => {
    it('shows "New Recipe" heading when no recipeId', () => {
      renderWithProviders(<RecipeForm />);
      expect(screen.getByText('New Recipe')).toBeInTheDocument();
    });

    it('shows "Edit Recipe" heading when recipeId is provided', () => {
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );
      expect(screen.getByText('Edit Recipe')).toBeInTheDocument();
    });

    it('populates form fields from initialData', () => {
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );
      expect(screen.getByDisplayValue('Test Recipe')).toBeInTheDocument();
      expect(screen.getByDisplayValue('A test recipe')).toBeInTheDocument();
      expect(screen.getByDisplayValue('15')).toBeInTheDocument();
      expect(screen.getByDisplayValue('30')).toBeInTheDocument();
    });

    it('shows empty ingredient/instruction messages when none exist', () => {
      renderWithProviders(<RecipeForm />);
      expect(screen.getByText(/no ingredients yet/i)).toBeInTheDocument();
      expect(screen.getByText(/no instructions yet/i)).toBeInTheDocument();
    });

    it('shows Re-import button only when editing with source_url', () => {
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );
      expect(screen.getByText(/re-import from source/i)).toBeInTheDocument();
    });

    it('hides Re-import button for new recipe', () => {
      renderWithProviders(<RecipeForm />);
      expect(screen.queryByText(/re-import from source/i)).not.toBeInTheDocument();
    });
  });

  // ── Ingredient CRUD ──

  describe('Ingredient CRUD', () => {
    it('adds an ingredient row when clicking + Add', async () => {
      const user = userEvent.setup();
      renderWithProviders(<RecipeForm />);

      // Find the Ingredients section's Add button
      const ingredientSection = screen.getByText('Ingredients').closest('div');
      const addButton = within(ingredientSection).getByText('+ Add');
      await user.click(addButton);

      expect(screen.getByPlaceholderText('Ingredient name')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Qty')).toBeInTheDocument();
    });

    it('removes an ingredient row', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      // Should have 2 ingredients initially
      const removeButtons = screen.getAllByTitle('Remove ingredient');
      // Remove the first ingredient (flour)
      await user.click(removeButtons[0]);

      expect(screen.queryByDisplayValue('flour')).not.toBeInTheDocument();
      expect(screen.getByDisplayValue('sugar')).toBeInTheDocument();
    });

    it('updates ingredient name', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      const flourInput = screen.getByDisplayValue('flour');
      await user.clear(flourInput);
      await user.type(flourInput, 'whole wheat flour');

      expect(screen.getByDisplayValue('whole wheat flour')).toBeInTheDocument();
    });
  });

  // ── Instruction CRUD ──

  describe('Instruction CRUD', () => {
    it('adds an instruction row', async () => {
      const user = userEvent.setup();
      renderWithProviders(<RecipeForm />);

      const instructionSection = screen.getByText('Instructions').closest('div');
      const addButton = within(instructionSection).getByText('+ Add');
      await user.click(addButton);

      expect(screen.getByPlaceholderText('Instruction description')).toBeInTheDocument();
    });

    it('removes an instruction and renumbers remaining', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      // Should have 2 instructions: "1." and "2."
      expect(screen.getByText('1.')).toBeInTheDocument();
      expect(screen.getByText('2.')).toBeInTheDocument();

      // Remove the first instruction (× buttons in instruction area)
      const removeButtons = screen.getAllByTitle('Remove step');
      await user.click(removeButtons[0]);

      // Remaining instruction should now be "1."
      expect(screen.getByText('1.')).toBeInTheDocument();
      expect(screen.queryByText('2.')).not.toBeInTheDocument();
      expect(screen.getByDisplayValue('Bake at 350F')).toBeInTheDocument();
    });

    it('clones an instruction via the split button', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      const splitButtons = screen.getAllByTitle(/insert step/i);
      await user.click(splitButtons[0]);

      // Should now have 3 instructions
      expect(screen.getByText('3.')).toBeInTheDocument();
    });
  });

  // ── Form Submission ──

  describe('Form Submission', () => {
    it('calls recipeAPI.create for new recipe', async () => {
      recipeAPI.create.mockResolvedValue({ data: { id: 'new-123' } });
      const user = userEvent.setup();
      renderWithProviders(<RecipeForm />);

      // Name is the first text input in the form
      const allInputs = screen.getAllByRole('textbox');
      await user.type(allInputs[0], 'My New Recipe');

      await user.click(screen.getByText('Create Recipe'));

      await waitFor(() => {
        expect(recipeAPI.create).toHaveBeenCalled();
        expect(mockNavigate).toHaveBeenCalledWith('/recipes');
      });
    });

    it('calls recipeAPI.update for existing recipe', async () => {
      recipeAPI.update.mockResolvedValue({ data: validRecipeData });
      const user = userEvent.setup();
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      await user.click(screen.getByText('Update Recipe'));

      await waitFor(() => {
        expect(recipeAPI.update).toHaveBeenCalledWith('recipe-123', expect.any(Object));
      });
    });

    it('validates quantity is required when unit is set', async () => {
      const user = userEvent.setup();
      const dataWithBadIngredient = {
        ...validRecipeData,
        ingredients: [
          // quantity: 0 passes HTML5 required but fails JS check (!0 === true)
          { id: 'ing-1', ingredient_name: 'flour', quantity: 0, unit: 'cup', order: 0 },
        ],
      };
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={dataWithBadIngredient} />
      );

      await user.click(screen.getByText('Update Recipe'));

      await waitFor(() => {
        expect(screen.getByText(/quantity is required when unit is specified/i)).toBeInTheDocument();
      });
      expect(recipeAPI.update).not.toHaveBeenCalled();
    });

    it('displays API error detail on failure', async () => {
      recipeAPI.update.mockRejectedValue({
        response: { data: { detail: 'Recipe name already exists' } }
      });
      const user = userEvent.setup();
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      await user.click(screen.getByText('Update Recipe'));

      await waitFor(() => {
        expect(screen.getByText('Recipe name already exists')).toBeInTheDocument();
      });
    });
  });

  // ── Navigation State ──

  describe('Navigation State', () => {
    it('navigates to returnTo location after updating recipe', async () => {
      mockLocation.state = { returnTo: '/ingredients', tab: 'unmapped' };
      recipeAPI.update.mockResolvedValue({ data: validRecipeData });
      const user = userEvent.setup();

      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );
      await user.click(screen.getByText(/update recipe/i));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/ingredients', {
          state: { tab: 'unmapped' }
        });
      });
    });

    it('falls back to /recipes when no returnTo state', async () => {
      recipeAPI.update.mockResolvedValue({ data: validRecipeData });
      const user = userEvent.setup();

      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );
      await user.click(screen.getByText(/update recipe/i));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/recipes');
      });
    });

    it('cancel button navigates to returnTo when provided', async () => {
      mockLocation.state = { returnTo: '/ingredients', tab: 'unmapped' };
      const user = userEvent.setup();

      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );
      await user.click(screen.getByText(/^cancel$/i));

      expect(mockNavigate).toHaveBeenCalledWith('/ingredients', {
        state: { tab: 'unmapped' }
      });
    });

    it('cancel button falls back to /recipes', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );
      await user.click(screen.getByText(/^cancel$/i));

      expect(mockNavigate).toHaveBeenCalledWith('/recipes');
    });
  });

  // ── Prep Step Linking ──

  describe('Prep Step Linking', () => {
    it('hydrates ingredient prep_step_description from linked prep steps', () => {
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={recipeWithPrepSteps} />
      );

      // Onion and carrot should both show "Dice finely" in their prep step fields
      const diceFields = screen.getAllByDisplayValue('Dice finely');
      expect(diceFields).toHaveLength(2);
    });

    it('shows link icon for linked ingredients', () => {
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={recipeWithPrepSteps} />
      );

      // Linked ingredients show the 🔗 icon
      const linkIcons = screen.getAllByText('🔗');
      expect(linkIcons).toHaveLength(2); // onion and carrot
    });

    it('shows edit button for linked ingredients', () => {
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={recipeWithPrepSteps} />
      );

      const editButtons = screen.getAllByTitle('Edit prep step');
      expect(editButtons).toHaveLength(2); // onion and carrot are linked
    });

    it('shows clear (✕) button on linked prep step fields', () => {
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={recipeWithPrepSteps} />
      );

      // The ✕ clear buttons inside prep step inputs for linked ingredients
      const clearButtons = screen.getAllByText('✕');
      expect(clearButtons.length).toBeGreaterThanOrEqual(2);
    });
  });

  // ── Re-import ──

  describe('Re-import', () => {
    it('opens confirmation modal when clicking Re-import', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      await user.click(screen.getByText(/re-import from source/i));

      expect(screen.getByText(/re-import recipe from source\?/i)).toBeInTheDocument();
      expect(screen.getByText(/current ingredients and instructions will be replaced/i)).toBeInTheDocument();
    });

    it('closes modal on cancel', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      await user.click(screen.getByText(/re-import from source/i));
      // The modal has its own Cancel button
      const modalCancelButtons = screen.getAllByText(/^cancel$/i);
      await user.click(modalCancelButtons[modalCancelButtons.length - 1]);

      expect(screen.queryByText(/re-import recipe from source\?/i)).not.toBeInTheDocument();
    });

    it('calls reimport API and shows success toast', async () => {
      recipeAPI.reimport.mockResolvedValue({
        data: {
          ...validRecipeData,
          name: 'Updated Recipe Name',
          ingredients: [{ id: 'new-1', ingredient_name: 'new flour', quantity: 3, unit: 'cup', order: 0 }],
          instructions: [{ id: 'new-inst', step_number: 1, description: 'New step' }],
        }
      });
      const user = userEvent.setup();
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      await user.click(screen.getByText(/re-import from source/i));
      await user.click(screen.getByText(/^re-import recipe$/i));

      await waitFor(() => {
        expect(recipeAPI.reimport).toHaveBeenCalledWith('recipe-123');
        expect(screen.getByText(/successfully re-imported/i)).toBeInTheDocument();
      });
    });
  });
});
