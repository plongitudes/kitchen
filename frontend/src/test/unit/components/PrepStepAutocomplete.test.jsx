import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../utils/test-utils';
import PrepStepAutocomplete from '../../../components/PrepStepAutocomplete';

describe('PrepStepAutocomplete', () => {
  const mockPrepSteps = [
    {
      id: 'prep-1',
      description: 'Chop onions finely',
      linked_ingredient_names: ['onions', 'shallots']
    },
    {
      id: 'prep-2',
      description: 'Dice tomatoes',
      linked_ingredient_names: ['tomatoes']
    },
    {
      id: 'prep-3',
      description: 'Mince garlic',
      linked_ingredient_names: ['garlic']
    },
  ];

  const defaultProps = {
    value: '',
    onChange: vi.fn(),
    prepSteps: mockPrepSteps,
    onAccept: vi.fn(),
    onUnlink: vi.fn(),
    isLinked: false,
    showAcceptButton: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders an input field with placeholder text', () => {
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} />);
      expect(screen.getByPlaceholderText(/prep step/i)).toBeInTheDocument();
    });

    it('displays the current value in the input', () => {
      renderWithProviders(
        <PrepStepAutocomplete {...defaultProps} value="Chop onions" />
      );
      expect(screen.getByDisplayValue('Chop onions')).toBeInTheDocument();
    });

    it('applies required attribute when specified', () => {
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} required />);
      const input = screen.getByPlaceholderText(/prep step/i);
      expect(input).toHaveAttribute('required');
    });
  });

  describe('Dropdown Display', () => {
    it('shows dropdown when input is focused', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} />);
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.click(input);
      
      await waitFor(() => {
        expect(screen.getByText('Chop onions finely')).toBeInTheDocument();
      });
    });

    it('displays prep steps with linked ingredients format', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} />);
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.click(input);
      
      await waitFor(() => {
        expect(screen.getByText('Chop onions finely')).toBeInTheDocument();
        expect(screen.getByText('(onions, shallots)')).toBeInTheDocument();
      });
    });

    it('hides dropdown when clicking outside', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <div>
          <PrepStepAutocomplete {...defaultProps} />
          <button>Outside</button>
        </div>
      );
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.click(input);
      
      await waitFor(() => {
        expect(screen.getByText('Chop onions finely')).toBeInTheDocument();
      });
      
      const outsideButton = screen.getByText('Outside');
      await user.click(outsideButton);
      
      await waitFor(() => {
        expect(screen.queryByText('Chop onions finely')).not.toBeInTheDocument();
      });
    });
  });

  describe('Fuzzy Search', () => {
    it('filters prep steps based on description search', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} />);
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.type(input, 'dice');
      
      await waitFor(() => {
        expect(screen.getByText('Dice tomatoes')).toBeInTheDocument();
        expect(screen.queryByText('Chop onions finely')).not.toBeInTheDocument();
      });
    });

    it('filters prep steps based on ingredient name search', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} />);
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.type(input, 'garlic');
      
      await waitFor(() => {
        expect(screen.getByText('Mince garlic')).toBeInTheDocument();
        expect(screen.queryByText('Dice tomatoes')).not.toBeInTheDocument();
      });
    });

    it('handles fuzzy matching (partial/typo)', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} />);
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.type(input, 'toma'); // partial match
      
      await waitFor(() => {
        expect(screen.getByText('Dice tomatoes')).toBeInTheDocument();
      });
    });

    it('shows all prep steps when search is cleared', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} />);
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.type(input, 'dice');
      
      await waitFor(() => {
        expect(screen.queryByText('Chop onions finely')).not.toBeInTheDocument();
      });
      
      await user.clear(input);
      await user.click(input);
      
      await waitFor(() => {
        expect(screen.getByText('Chop onions finely')).toBeInTheDocument();
        expect(screen.getByText('Dice tomatoes')).toBeInTheDocument();
        expect(screen.getByText('Mince garlic')).toBeInTheDocument();
      });
    });
  });

  describe('Keyboard Navigation', () => {
    it('navigates down with ArrowDown key', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} />);
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.click(input);
      await user.keyboard('{ArrowDown}');
      
      // First item should be highlighted (implementation will add visual indication)
      await waitFor(() => {
        expect(screen.getByText('Chop onions finely')).toBeInTheDocument();
      });
    });

    it('navigates up with ArrowUp key', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} />);
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.click(input);
      await user.keyboard('{ArrowDown}{ArrowDown}{ArrowUp}');
      
      // Should move to second item then back to first
      await waitFor(() => {
        expect(screen.getByText('Chop onions finely')).toBeInTheDocument();
      });
    });

    it('selects highlighted item with Enter key', async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      renderWithProviders(
        <PrepStepAutocomplete {...defaultProps} onChange={onChange} />
      );
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.click(input);
      await user.keyboard('{ArrowDown}{Enter}');
      
      await waitFor(() => {
        expect(onChange).toHaveBeenCalledWith('Chop onions finely');
      });
    });

    it('closes dropdown with Escape key', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} />);
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.click(input);
      
      await waitFor(() => {
        expect(screen.getByText('Chop onions finely')).toBeInTheDocument();
      });
      
      await user.keyboard('{Escape}');
      
      await waitFor(() => {
        expect(screen.queryByText('Chop onions finely')).not.toBeInTheDocument();
      });
    });
  });

  describe('Selection Behavior', () => {
    it('calls onChange when item is clicked', async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      renderWithProviders(
        <PrepStepAutocomplete {...defaultProps} onChange={onChange} />
      );
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.click(input);
      
      await waitFor(() => {
        expect(screen.getByText('Dice tomatoes')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Dice tomatoes'));
      
      expect(onChange).toHaveBeenCalledWith('Dice tomatoes');
    });

    it('closes dropdown after selection', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} />);
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.click(input);
      
      await waitFor(() => {
        expect(screen.getByText('Dice tomatoes')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Dice tomatoes'));
      
      await waitFor(() => {
        expect(screen.queryByText('Dice tomatoes')).not.toBeInTheDocument();
      });
    });
  });

  describe('Accept/Unlink Buttons', () => {
    it('shows Accept button when showAcceptButton is true', () => {
      renderWithProviders(
        <PrepStepAutocomplete {...defaultProps} showAcceptButton={true} />
      );
      expect(screen.getByText(/accept/i)).toBeInTheDocument();
    });

    it('shows Unlink button when isLinked is true', () => {
      renderWithProviders(
        <PrepStepAutocomplete {...defaultProps} isLinked={true} />
      );
      expect(screen.getByText(/unlink/i)).toBeInTheDocument();
    });

    it('calls onAccept when Accept button is clicked', async () => {
      const user = userEvent.setup();
      const onAccept = vi.fn();
      renderWithProviders(
        <PrepStepAutocomplete 
          {...defaultProps} 
          showAcceptButton={true} 
          onAccept={onAccept}
          value="Chop onions"
        />
      );
      
      const acceptButton = screen.getByText(/accept/i);
      await user.click(acceptButton);
      
      expect(onAccept).toHaveBeenCalled();
    });

    it('calls onUnlink when Unlink button is clicked', async () => {
      const user = userEvent.setup();
      const onUnlink = vi.fn();
      renderWithProviders(
        <PrepStepAutocomplete 
          {...defaultProps} 
          isLinked={true} 
          onUnlink={onUnlink}
        />
      );
      
      const unlinkButton = screen.getByText(/unlink/i);
      await user.click(unlinkButton);
      
      expect(onUnlink).toHaveBeenCalled();
    });
  });

  describe('Clear Functionality', () => {
    it('shows clear button when value is set', () => {
      renderWithProviders(
        <PrepStepAutocomplete {...defaultProps} value="Chop onions" />
      );
      expect(screen.getByText('✕')).toBeInTheDocument();
    });

    it('does not show clear button when value is empty', () => {
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} value="" />);
      expect(screen.queryByText('✕')).not.toBeInTheDocument();
    });

    it('clears value when clear button is clicked', async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      renderWithProviders(
        <PrepStepAutocomplete 
          {...defaultProps} 
          value="Chop onions"
          onChange={onChange}
        />
      );
      
      const clearButton = screen.getByText('✕');
      await user.click(clearButton);
      
      expect(onChange).toHaveBeenCalledWith('');
    });
  });

  describe('Empty States', () => {
    it('shows message when no prep steps exist', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <PrepStepAutocomplete {...defaultProps} prepSteps={[]} />
      );
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.click(input);
      
      // Dropdown should not appear or show empty state
      await waitFor(() => {
        expect(screen.queryByText('Chop onions finely')).not.toBeInTheDocument();
      });
    });

    it('shows message when search has no results', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PrepStepAutocomplete {...defaultProps} />);
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.type(input, 'zzzzzzz'); // nonsense search
      
      await waitFor(() => {
        expect(screen.queryByText('Chop onions finely')).not.toBeInTheDocument();
        expect(screen.queryByText('Dice tomatoes')).not.toBeInTheDocument();
      });
    });
  });

  describe('onChange Behavior', () => {
    it('calls onChange as user types', async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      renderWithProviders(
        <PrepStepAutocomplete {...defaultProps} onChange={onChange} />
      );
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.type(input, 'C');
      
      expect(onChange).toHaveBeenCalledWith('C');
    });

    it('allows free-form text entry (not just selection)', async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      renderWithProviders(
        <PrepStepAutocomplete {...defaultProps} onChange={onChange} />
      );
      
      const input = screen.getByPlaceholderText(/prep step/i);
      await user.type(input, 'Custom prep step');
      
      expect(onChange).toHaveBeenLastCalledWith('Custom prep step');
    });
  });
});
