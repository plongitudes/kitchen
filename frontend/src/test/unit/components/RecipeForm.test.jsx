import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
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

describe('RecipeForm - Navigation State', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.state = null;
  });

  const validRecipeData = {
    id: 'recipe-123',
    name: 'Test Recipe',
    recipe_type: 'dinner',
    description: 'A test recipe',
    ingredients: [
      { id: 'ing-1', ingredient_name: 'flour', quantity: 2, unit: 'cup', order: 1 }
    ],
    instructions: [
      { id: 'inst-1', step_number: 1, description: 'Mix ingredients' }
    ],
  };

  describe('when returnTo state is provided', () => {
    it('navigates to returnTo location after updating recipe', async () => {
      // ARRANGE: Set up location state with returnTo
      mockLocation.state = {
        returnTo: '/ingredients',
        tab: 'unmapped'
      };

      recipeAPI.update.mockResolvedValue({ data: validRecipeData });

      const user = userEvent.setup();

      // ACT: Render form and submit
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      const submitButton = screen.getByText(/update recipe/i);
      await user.click(submitButton);

      // ASSERT: Should navigate to returnTo with tab state preserved
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/ingredients', {
          state: { tab: 'unmapped' }
        });
      });
    });
  });

  describe('when returnTo state is NOT provided', () => {
    it('falls back to /recipes after updating recipe', async () => {
      // ARRANGE: No returnTo in state
      mockLocation.state = null;

      recipeAPI.update.mockResolvedValue({ data: validRecipeData });

      const user = userEvent.setup();

      // ACT
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      const submitButton = screen.getByText(/update recipe/i);
      await user.click(submitButton);

      // ASSERT: Should use default /recipes
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/recipes');
      });
    });
  });

  describe('Cancel button navigation', () => {
    it('navigates to returnTo location when canceling with state provided', async () => {
      // ARRANGE: Set up location state with returnTo
      mockLocation.state = {
        returnTo: '/ingredients',
        tab: 'unmapped'
      };

      const user = userEvent.setup();

      // ACT: Render form and click cancel
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      const cancelButton = screen.getByText(/cancel/i);
      await user.click(cancelButton);

      // ASSERT: Should navigate to returnTo with tab state preserved
      expect(mockNavigate).toHaveBeenCalledWith('/ingredients', {
        state: { tab: 'unmapped' }
      });
    });

    it('falls back to /recipes when canceling without returnTo state', async () => {
      // ARRANGE: No returnTo in state
      mockLocation.state = null;

      const user = userEvent.setup();

      // ACT: Render form and click cancel
      renderWithProviders(
        <RecipeForm recipeId="recipe-123" initialData={validRecipeData} />
      );

      const cancelButton = screen.getByText(/cancel/i);
      await user.click(cancelButton);

      // ASSERT: Should use default /recipes
      expect(mockNavigate).toHaveBeenCalledWith('/recipes');
    });
  });
});
