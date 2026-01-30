import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../utils/test-utils';
import RecipeList from '../../../pages/RecipeList';
import { recipeAPI } from '../../../services/api';

// Mock the API
vi.mock('../../../services/api', () => ({
  recipeAPI: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('RecipeList - Index View', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockIndexData = {
    index: {
      A: [
        {
          type: 'ingredient',
          name: 'Apple',
          recipes: [
            { id: '1', name: 'Apple Pie' },
            { id: '2', name: 'Apple Crisp' },
          ],
        },
      ],
      C: [
        {
          type: 'ingredient',
          name: 'Chicken',
          recipes: [
            { id: '3', name: 'Chicken Soup' },
            { id: '4', name: 'Chicken Burritos' },
          ],
        },
        {
          type: 'recipe',
          name: 'Chocolate Cake',
          id: '5',
          indexed_ingredients: [],
        },
      ],
    },
  };

  it('renders loading state initially', () => {
    recipeAPI.get.mockReturnValue(new Promise(() => {})); // Never resolves
    renderWithProviders(<RecipeList />);

    expect(screen.getByText('Loading recipe index...')).toBeInTheDocument();
  });

  it('renders index with alphabet navigation', async () => {
    recipeAPI.get.mockResolvedValue({ data: mockIndexData });
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      expect(screen.getByText('Recipe Index')).toBeInTheDocument();
    });

    // Check alphabet navigation exists
    expect(screen.getByRole('button', { name: 'A' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'C' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Z' })).toBeInTheDocument();
  });

  it('highlights available letters in alphabet nav', async () => {
    recipeAPI.get.mockResolvedValue({ data: mockIndexData });
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      const aButton = screen.getByRole('button', { name: 'A' });
      const cButton = screen.getByRole('button', { name: 'C' });
      const zButton = screen.getByRole('button', { name: 'Z' });

      expect(aButton).not.toBeDisabled();
      expect(cButton).not.toBeDisabled();
      expect(zButton).toBeDisabled(); // No entries for Z
    });
  });

  it('displays ingredient entries with indented recipe links', async () => {
    recipeAPI.get.mockResolvedValue({ data: mockIndexData });
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      // Check ingredient name is displayed
      expect(screen.getByText('Apple')).toBeInTheDocument();
      
      // Check recipe links under the ingredient
      expect(screen.getByRole('link', { name: 'Apple Pie' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Apple Crisp' })).toBeInTheDocument();
    });
  });

  it('displays standalone recipe entries', async () => {
    recipeAPI.get.mockResolvedValue({ data: mockIndexData });
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      expect(screen.getByRole('link', { name: 'Chocolate Cake' })).toBeInTheDocument();
    });
  });

  it('displays letter section headers', async () => {
    recipeAPI.get.mockResolvedValue({ data: mockIndexData });
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      // Check for section headers (they're h2 elements)
      const headers = screen.getAllByRole('heading', { level: 2 });
      const headerTexts = headers.map((h) => h.textContent);
      
      expect(headerTexts).toContain('A');
      expect(headerTexts).toContain('C');
    });
  });

  it('filters index based on search query', async () => {
    recipeAPI.get.mockResolvedValue({ data: mockIndexData });
    const user = userEvent.setup();
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      expect(screen.getByText('Apple')).toBeInTheDocument();
    });

    // Type in search box
    const searchInput = screen.getByPlaceholderText('Search recipes or ingredients...');
    await user.type(searchInput, 'soup');

    // Only Chicken Soup should be visible
    await waitFor(() => {
      expect(screen.getByText('Chicken Soup')).toBeInTheDocument();
      expect(screen.queryByText('Apple Pie')).not.toBeInTheDocument();
      expect(screen.queryByText('Chocolate Cake')).not.toBeInTheDocument();
    });
  });

  it('shows no results message when search has no matches', async () => {
    recipeAPI.get.mockResolvedValue({ data: mockIndexData });
    const user = userEvent.setup();
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      expect(screen.getByText('Apple')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search recipes or ingredients...');
    await user.type(searchInput, 'nonexistent');

    await waitFor(() => {
      expect(screen.getByText(/No recipes match "nonexistent"/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Clear search' })).toBeInTheDocument();
    });
  });

  it('clears search when clear button is clicked', async () => {
    recipeAPI.get.mockResolvedValue({ data: mockIndexData });
    const user = userEvent.setup();
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      expect(screen.getByText('Apple')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search recipes or ingredients...');
    await user.type(searchInput, 'nonexistent');

    await waitFor(() => {
      expect(screen.getByText(/No recipes match/)).toBeInTheDocument();
    });

    const clearButton = screen.getByRole('button', { name: 'Clear search' });
    await user.click(clearButton);

    await waitFor(() => {
      expect(searchInput.value).toBe('');
      expect(screen.getByText('Apple')).toBeInTheDocument();
    });
  });

  it('shows empty state when no recipes exist', async () => {
    recipeAPI.get.mockResolvedValue({ data: { index: {} } });
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      expect(screen.getByText('No recipes yet.')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Create your first recipe' })).toBeInTheDocument();
    });
  });

  it('navigates to new recipe page when create button is clicked', async () => {
    recipeAPI.get.mockResolvedValue({ data: { index: {} } });
    const user = userEvent.setup();
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      const createButton = screen.getByRole('button', { name: 'Create your first recipe' });
      expect(createButton).toBeInTheDocument();
    });

    const createButton = screen.getByRole('button', { name: 'Create your first recipe' });
    await user.click(createButton);

    expect(mockNavigate).toHaveBeenCalledWith('/recipes/new');
  });

  it('toggles include retired filter', async () => {
    recipeAPI.get.mockResolvedValue({ data: mockIndexData });
    const user = userEvent.setup();
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      expect(screen.getByText('Apple')).toBeInTheDocument();
    });

    // Should be called once on mount
    expect(recipeAPI.get).toHaveBeenCalledWith('index?include_retired=false');

    const checkbox = screen.getByRole('checkbox', { name: 'Show retired' });
    await user.click(checkbox);

    // Should be called again with include_retired=true
    await waitFor(() => {
      expect(recipeAPI.get).toHaveBeenCalledWith('index?include_retired=true');
    });
  });

  it('renders error state when API fails', async () => {
    recipeAPI.get.mockRejectedValue({
      response: { data: { detail: 'API Error' } },
    });
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      expect(screen.getByText('Error: API Error')).toBeInTheDocument();
    });
  });

  it('renders error state with fallback message', async () => {
    recipeAPI.get.mockRejectedValue(new Error('Network error'));
    renderWithProviders(<RecipeList />);

    await waitFor(() => {
      expect(screen.getByText('Error: Failed to load recipe index')).toBeInTheDocument();
    });
  });

  it('has sticky alphabet navigation', async () => {
    recipeAPI.get.mockResolvedValue({ data: mockIndexData });
    const { container } = renderWithProviders(<RecipeList />);

    await waitFor(() => {
      expect(screen.getByText('Apple')).toBeInTheDocument();
    });

    const alphabetNav = container.querySelector('.sticky');
    expect(alphabetNav).toBeInTheDocument();
  });
});
