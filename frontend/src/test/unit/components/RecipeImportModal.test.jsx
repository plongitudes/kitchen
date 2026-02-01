import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../utils/test-utils';
import RecipeImportModal from '../../../components/RecipeImportModal';
import { recipeAPI } from '../../../services/api';

// Mock the API
vi.mock('../../../services/api', () => ({
  recipeAPI: {
    importPreview: vi.fn(),
    create: vi.fn(),
  },
}));

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockScrapedData = {
  name: 'Spaghetti Carbonara',
  description: 'A classic Italian pasta dish',
  recipe_type: 'dinner',
  prep_time_minutes: 10,
  cook_time_minutes: 20,
  source_url: 'https://example.com/carbonara',
  ingredients: [
    { ingredient_name: 'spaghetti', quantity: 400, unit: 'g' },
    { ingredient_name: 'guanciale', quantity: 200, unit: 'g' },
    { ingredient_name: 'eggs', quantity: 4, unit: '' },
    { ingredient_name: 'pecorino', quantity: 100, unit: 'g' },
  ],
  instructions: [
    { step_number: 1, description: 'Boil pasta in salted water' },
    { step_number: 2, description: 'Crisp the guanciale' },
    { step_number: 3, description: 'Mix eggs with cheese' },
    { step_number: 4, description: 'Combine everything off heat' },
  ],
};

describe('RecipeImportModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── Open/Close ──

  describe('Open/Close', () => {
    it('renders nothing when closed', () => {
      const { container } = renderWithProviders(
        <RecipeImportModal isOpen={false} onClose={vi.fn()} />
      );
      expect(container.innerHTML).toBe('');
    });

    it('renders modal when open', () => {
      renderWithProviders(<RecipeImportModal {...defaultProps} />);
      expect(screen.getByText('Import Recipe from URL')).toBeInTheDocument();
    });

    it('resets state on close', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      renderWithProviders(<RecipeImportModal isOpen={true} onClose={onClose} />);

      // Type something in the URL field
      const urlInput = screen.getByPlaceholderText(/allrecipes/);
      await user.type(urlInput, 'https://example.com');

      // Click Cancel
      await user.click(screen.getByText('Cancel'));

      expect(onClose).toHaveBeenCalled();
    });
  });

  // ── URL Input Phase ──

  describe('URL Input Phase', () => {
    it('shows URL input and Import button', () => {
      renderWithProviders(<RecipeImportModal {...defaultProps} />);
      expect(screen.getByPlaceholderText(/allrecipes/)).toBeInTheDocument();
      expect(screen.getByText('Import')).toBeInTheDocument();
    });

    it('disables Import button when URL is empty', () => {
      renderWithProviders(<RecipeImportModal {...defaultProps} />);
      expect(screen.getByText('Import')).toBeDisabled();
    });

    it('enables Import button when URL is entered', async () => {
      const user = userEvent.setup();
      renderWithProviders(<RecipeImportModal {...defaultProps} />);

      await user.type(screen.getByPlaceholderText(/allrecipes/), 'https://example.com');

      expect(screen.getByText('Import')).not.toBeDisabled();
    });

    it('triggers scrape on Enter key', async () => {
      recipeAPI.importPreview.mockResolvedValue({ data: mockScrapedData });
      const user = userEvent.setup();
      renderWithProviders(<RecipeImportModal {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/allrecipes/);
      await user.type(urlInput, 'https://example.com{enter}');

      await waitFor(() => {
        expect(recipeAPI.importPreview).toHaveBeenCalledWith('https://example.com');
      });
    });

    it('shows error when scrape fails', async () => {
      recipeAPI.importPreview.mockRejectedValue({
        response: { data: { detail: 'Could not parse recipe from URL' } },
      });
      const user = userEvent.setup();
      renderWithProviders(<RecipeImportModal {...defaultProps} />);

      await user.type(screen.getByPlaceholderText(/allrecipes/), 'https://bad.com');
      await user.click(screen.getByText('Import'));

      await waitFor(() => {
        expect(screen.getByText('Could not parse recipe from URL')).toBeInTheDocument();
      });
    });

    it('keeps Import button disabled for whitespace-only URL', async () => {
      const user = userEvent.setup();
      renderWithProviders(<RecipeImportModal {...defaultProps} />);

      const urlInput = screen.getByPlaceholderText(/allrecipes/);
      await user.type(urlInput, '   ');

      expect(screen.getByText('Import')).toBeDisabled();
    });
  });

  // ── Preview Phase ──

  describe('Preview Phase', () => {
    const renderWithPreview = async () => {
      recipeAPI.importPreview.mockResolvedValue({ data: mockScrapedData });
      const user = userEvent.setup();
      renderWithProviders(<RecipeImportModal {...defaultProps} />);

      await user.type(screen.getByPlaceholderText(/allrecipes/), 'https://example.com');
      await user.click(screen.getByText('Import'));

      await waitFor(() => {
        expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
      });

      return user;
    };

    it('displays recipe name and description', async () => {
      await renderWithPreview();

      expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
      expect(screen.getByText('A classic Italian pasta dish')).toBeInTheDocument();
    });

    it('displays prep and cook times', async () => {
      await renderWithPreview();

      expect(screen.getByText('Prep: 10 min')).toBeInTheDocument();
      expect(screen.getByText('Cook: 20 min')).toBeInTheDocument();
    });

    it('displays ingredient and instruction counts', async () => {
      await renderWithPreview();

      expect(screen.getByText('Ingredients (4)')).toBeInTheDocument();
      expect(screen.getByText('Instructions (4 steps)')).toBeInTheDocument();
    });

    it('displays ingredients list', async () => {
      await renderWithPreview();

      const ingredientItems = screen.getAllByRole('listitem');
      const ingredientTexts = ingredientItems.map(li => li.textContent);
      expect(ingredientTexts.some(t => t.includes('spaghetti'))).toBe(true);
      expect(ingredientTexts.some(t => t.includes('guanciale'))).toBe(true);
    });

    it('shows Save Recipe and Save & Edit buttons', async () => {
      await renderWithPreview();

      expect(screen.getByText('Save Recipe')).toBeInTheDocument();
      expect(screen.getByText('Save & Edit')).toBeInTheDocument();
    });

    it('shows Back button to return to URL input', async () => {
      const user = await renderWithPreview();

      await user.click(screen.getByText('Back'));

      // Should return to URL input phase
      expect(screen.getByPlaceholderText(/allrecipes/)).toBeInTheDocument();
    });

    it('shows source URL', async () => {
      await renderWithPreview();

      expect(screen.getByText(/example\.com\/carbonara/)).toBeInTheDocument();
    });
  });

  // ── Save Flows ──

  describe('Save Flows', () => {
    const setupPreviewAndSave = async () => {
      recipeAPI.importPreview.mockResolvedValue({ data: mockScrapedData });
      recipeAPI.create.mockResolvedValue({ data: { id: 'new-recipe-1' } });
      const user = userEvent.setup();
      renderWithProviders(<RecipeImportModal {...defaultProps} />);

      await user.type(screen.getByPlaceholderText(/allrecipes/), 'https://example.com');
      await user.click(screen.getByText('Import'));
      await waitFor(() => {
        expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
      });

      return user;
    };

    it('Save Recipe creates and navigates to detail view', async () => {
      const user = await setupPreviewAndSave();

      await user.click(screen.getByText('Save Recipe'));

      await waitFor(() => {
        expect(recipeAPI.create).toHaveBeenCalledWith(
          expect.objectContaining({ name: 'Spaghetti Carbonara' })
        );
        expect(mockNavigate).toHaveBeenCalledWith('/recipes/new-recipe-1');
      });
    });

    it('Save & Edit creates and navigates to edit view', async () => {
      const user = await setupPreviewAndSave();

      await user.click(screen.getByText('Save & Edit'));

      await waitFor(() => {
        expect(recipeAPI.create).toHaveBeenCalled();
        expect(mockNavigate).toHaveBeenCalledWith('/recipes/new-recipe-1/edit');
      });
    });

    it('shows error when save fails', async () => {
      recipeAPI.importPreview.mockResolvedValue({ data: mockScrapedData });
      recipeAPI.create.mockRejectedValue({
        response: { data: { detail: 'Duplicate recipe name' } },
      });
      const user = userEvent.setup();
      renderWithProviders(<RecipeImportModal {...defaultProps} />);

      await user.type(screen.getByPlaceholderText(/allrecipes/), 'https://example.com');
      await user.click(screen.getByText('Import'));
      await waitFor(() => {
        expect(screen.getByText('Spaghetti Carbonara')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Save Recipe'));

      await waitFor(() => {
        expect(screen.getByText('Duplicate recipe name')).toBeInTheDocument();
      });
    });
  });
});
