import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithRouter } from '../../utils/test-utils';
import Home from '../../../pages/Home';

describe('Home Page', () => {
  it('renders welcome heading', () => {
    renderWithRouter(<Home />);

    expect(screen.getByText("Welcome to Roane's Kitchen")).toBeInTheDocument();
  });

  it('renders description text', () => {
    renderWithRouter(<Home />);

    expect(screen.getByText(/meal planning and grocery management system/i)).toBeInTheDocument();
  });

  it('renders all feature cards', () => {
    renderWithRouter(<Home />);

    expect(screen.getByText('Recipes')).toBeInTheDocument();
    expect(screen.getByText('Manage your recipe collection')).toBeInTheDocument();

    expect(screen.getByText('Schedules')).toBeInTheDocument();
    expect(screen.getByText('Plan your weekly meals')).toBeInTheDocument();

    expect(screen.getByText('Meal Plans')).toBeInTheDocument();
    expect(screen.getByText('View current and upcoming meal plans')).toBeInTheDocument();
  });

  it('displays feature cards in a grid layout', () => {
    const { container } = renderWithRouter(<Home />);

    const grid = container.querySelector('.grid');
    expect(grid).toBeInTheDocument();
  });
});
