import { describe, it, expect, vi } from 'vitest';
import { screen, render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { mockUser } from '../../utils/test-utils';
import Layout from '../../../components/Layout';

// Mock the auth context
vi.mock('../../../context/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    logout: vi.fn(),
  }),
}));

// Mock the theme context
vi.mock('../../../context/ThemeContext', () => ({
  useTheme: () => ({
    isDark: true,
    toggleTheme: vi.fn(),
  }),
}));

const renderLayout = () => {
  return render(
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
};

describe('Layout Component', () => {
  it('renders the sidebar navigation', () => {
    renderLayout();

    expect(screen.getByText("Roane's Kitchen")).toBeInTheDocument();
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Recipes')).toBeInTheDocument();
    expect(screen.getByText('Schedules')).toBeInTheDocument();
    expect(screen.getByText('Meal Plans')).toBeInTheDocument();
    expect(screen.getByText('Grocery Lists')).toBeInTheDocument();
  });

  it('displays the logged-in username', () => {
    renderLayout();

    expect(screen.getByText(`Logged in as: ${mockUser.username}`)).toBeInTheDocument();
  });

  it('renders theme toggle button', () => {
    renderLayout();

    expect(screen.getByText(/Light Mode/i)).toBeInTheDocument();
  });

  it('renders logout button', () => {
    renderLayout();

    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('renders navigation links with correct hrefs', () => {
    renderLayout();

    const homeLink = screen.getByRole('link', { name: 'Home' });
    const recipesLink = screen.getByRole('link', { name: 'Recipes' });

    expect(homeLink).toHaveAttribute('href', '/');
    expect(recipesLink).toHaveAttribute('href', '/recipes');
  });
});
