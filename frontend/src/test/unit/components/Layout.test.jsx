import { describe, it, expect, vi } from 'vitest';
import { screen, render } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
  it('renders the menu bar with page name', () => {
    renderLayout();

    expect(screen.getByText('Home')).toBeInTheDocument();
  });

  it('opens app menu dropdown with navigation links', async () => {
    const user = userEvent.setup();
    renderLayout();

    // Click the menu button (contains ☰)
    const menuButton = screen.getByRole('button', { name: /☰/i });
    await user.click(menuButton);

    expect(screen.getByRole('link', { name: 'Recipes' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Schedules' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Meal Plans' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Grocery Lists' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ingredients' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Settings' })).toBeInTheDocument();
  });

  it('displays username in dropdown', async () => {
    const user = userEvent.setup();
    renderLayout();

    const menuButton = screen.getByRole('button', { name: /☰/i });
    await user.click(menuButton);

    expect(screen.getByText(mockUser.username)).toBeInTheDocument();
  });

  it('renders theme toggle in dropdown', async () => {
    const user = userEvent.setup();
    renderLayout();

    const menuButton = screen.getByRole('button', { name: /☰/i });
    await user.click(menuButton);

    expect(screen.getByText(/Light Mode/i)).toBeInTheDocument();
  });

  it('renders logout button in dropdown', async () => {
    const user = userEvent.setup();
    renderLayout();

    const menuButton = screen.getByRole('button', { name: /☰/i });
    await user.click(menuButton);

    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('has no sidebar', () => {
    renderLayout();

    expect(screen.queryByText("Roane's Kitchen")).not.toBeInTheDocument();
    expect(screen.queryByText(`Logged in as: ${mockUser.username}`)).not.toBeInTheDocument();
  });

  it('renders navigation links with correct hrefs in dropdown', async () => {
    const user = userEvent.setup();
    renderLayout();

    const menuButton = screen.getByRole('button', { name: /☰/i });
    await user.click(menuButton);

    const homeLink = screen.getByRole('link', { name: 'Home' });
    const recipesLink = screen.getByRole('link', { name: 'Recipes' });

    expect(homeLink).toHaveAttribute('href', '/');
    expect(recipesLink).toHaveAttribute('href', '/recipes');
  });
});
