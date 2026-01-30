import { useState, useEffect, useRef } from 'react';
import Fuse from 'fuse.js';
import { useTheme } from '../context/ThemeContext';

/**
 * Autocomplete component for recipe prep step selection and linking.
 * 
 * Features:
 * - Fuzzy search with fuse.js (searches both description and linked ingredients)
 * - Displays prep steps in format: "description (ingredient1, ingredient2)"
 * - Keyboard navigation (arrow keys, enter, escape)
 * - Accept button: Update all ingredients linked to this prep step
 * - Unlink button: Break the link between this ingredient and prep step
 * - Free-form text entry for new prep steps
 * - Theme-aware styling
 */
const PrepStepAutocomplete = ({ 
  value, 
  onChange, 
  onBlur,
  prepSteps = [],
  onAccept,
  onUnlink,
  isLinked = false,
  showAcceptButton = false,
  required 
}) => {
  const { isDark } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState(value ?? '');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [filteredSteps, setFilteredSteps] = useState([]);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);

  // Initialize fuse.js for fuzzy search
  const fuse = useRef(null);
  useEffect(() => {
    // Build searchable items from prep steps
    // Each prep step includes description and linked ingredient names
    const searchableSteps = prepSteps.map(step => ({
      id: step.id,
      description: step.description,
      linked_ingredient_names: step.linked_ingredient_names || [],
      // Create a combined search string for better fuzzy matching
      searchText: `${step.description} ${(step.linked_ingredient_names || []).join(' ')}`,
    }));

    fuse.current = new Fuse(searchableSteps, {
      keys: ['description'], // Only search description, not ingredient names
      threshold: 0.4,        // Slightly more lenient than units
      ignoreLocation: true,
      distance: 100,
      minMatchCharLength: 2,
    });
  }, [prepSteps]);

  // Update filtered steps when search term changes
  useEffect(() => {
    if (!searchTerm.trim()) {
      // No search term - show all steps
      setFilteredSteps(prepSteps);
      setHighlightedIndex(-1);
    } else {
      // Search with fuse.js
      const results = fuse.current.search(searchTerm);
      const filtered = results.map((result) => result.item);
      setFilteredSteps(filtered);
      // Auto-highlight first result for quick Enter selection
      setHighlightedIndex(filtered.length > 0 ? 0 : -1);
    }
  }, [searchTerm, prepSteps]);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target) &&
        !inputRef.current.contains(event.target)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Set initial search term when value changes (from outside)
  useEffect(() => {
    setSearchTerm(value ?? '');
  }, [value]);

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    setSearchTerm(newValue);
    onChange(newValue);
    setIsOpen(true);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  const handleInputBlur = () => {
    // Delay to allow click on dropdown item or buttons
    setTimeout(() => {
      if (onBlur) {
        onBlur();
      }
    }, 200);
  };

  const handleSelectStep = (step) => {
    onChange(step.description);
    setSearchTerm(step.description);
    setIsOpen(false);
    setHighlightedIndex(-1);
  };

  const handleClear = () => {
    onChange('');
    setSearchTerm('');
    setIsOpen(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown') {
        setIsOpen(true);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex((prev) =>
          prev < filteredSteps.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && filteredSteps[highlightedIndex]) {
          handleSelectStep(filteredSteps[highlightedIndex]);
        }
        break;
      case 'Tab':
        // Close dropdown on Tab - don't prevent default to allow natural tab navigation
        setIsOpen(false);
        setHighlightedIndex(-1);
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setHighlightedIndex(-1);
        break;
      default:
        break;
    }
  };

  // Scroll highlighted item into view
  useEffect(() => {
    if (highlightedIndex >= 0 && dropdownRef.current) {
      const highlightedElement = dropdownRef.current.children[highlightedIndex];
      if (highlightedElement) {
        highlightedElement.scrollIntoView({
          block: 'nearest',
        });
      }
    }
  }, [highlightedIndex]);

  const formatPrepStepDisplay = (step) => {
    if (!step.linked_ingredient_names || step.linked_ingredient_names.length === 0) {
      return step.description;
    }
    return `${step.description} (${step.linked_ingredient_names.join(', ')})`;
  };

  return (
    <div className="relative">
      <div className="relative flex gap-2">
        <div className="relative flex-1">
          {/* Link icon indicator when linked */}
          {isLinked && (
            <span
              className={`absolute left-2 top-1/2 -translate-y-1/2 text-sm ${
                isDark ? 'text-gruvbox-dark-aqua' : 'text-gruvbox-light-aqua'
              }`}
              title="Linked to prep step"
            >
              🔗
            </span>
          )}
          <input
            ref={inputRef}
            type="text"
            value={searchTerm}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            onBlur={handleInputBlur}
            onKeyDown={handleKeyDown}
            required={required}
            placeholder="Prep step (optional)..."
            className={`w-full p-2 rounded border ${isLinked ? 'pl-7' : ''} ${
              isDark
                ? isLinked
                  ? 'bg-gruvbox-dark-bg border-gruvbox-dark-aqua text-gruvbox-dark-fg focus:border-gruvbox-dark-aqua-bright'
                  : 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg focus:border-gruvbox-dark-orange-bright'
                : isLinked
                ? 'bg-gruvbox-light-bg border-gruvbox-light-aqua text-gruvbox-light-fg focus:border-gruvbox-light-aqua-bright'
                : 'bg-gruvbox-light-bg border-gruvbox-light-gray text-gruvbox-light-fg focus:border-gruvbox-light-orange-bright'
            } focus:outline-none`}
          />
          {value && (
            <button
              type="button"
              onClick={handleClear}
              className={`absolute right-2 top-1/2 -translate-y-1/2 ${
                isDark ? 'text-gruvbox-dark-gray hover:text-gruvbox-dark-fg' : 'text-gruvbox-light-gray hover:text-gruvbox-light-fg'
              }`}
            >
              ✕
            </button>
          )}
        </div>

        {/* Accept button - shown when user has typed/modified prep text */}
        {showAcceptButton && (
          <button
            type="button"
            onClick={onAccept}
            className={`px-3 py-2 rounded text-sm font-medium ${
              isDark
                ? 'bg-gruvbox-dark-green text-gruvbox-dark-bg hover:bg-gruvbox-dark-green-bright'
                : 'bg-gruvbox-light-green text-gruvbox-light-bg hover:bg-gruvbox-light-green-bright'
            }`}
          >
            Accept
          </button>
        )}

        {/* Unlink button - shown when ingredient is linked to a prep step */}
        {isLinked && (
          <button
            type="button"
            onClick={onUnlink}
            className={`px-3 py-2 rounded text-sm font-medium ${
              isDark
                ? 'bg-gruvbox-dark-red text-gruvbox-dark-bg hover:bg-gruvbox-dark-red-bright'
                : 'bg-gruvbox-light-red text-gruvbox-light-bg hover:bg-gruvbox-light-red-bright'
            }`}
          >
            Unlink
          </button>
        )}
      </div>

      {isOpen && filteredSteps.length > 0 && (
        <div
          ref={dropdownRef}
          className={`absolute z-10 w-full mt-1 max-h-60 overflow-y-auto rounded border shadow-lg ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
              : 'bg-gruvbox-light-bg border-gruvbox-light-gray'
          }`}
        >
          {filteredSteps.map((step, index) => (
            <div
              key={step.id}
              onClick={() => handleSelectStep(step)}
              className={`px-3 py-2 cursor-pointer ${
                index === highlightedIndex
                  ? isDark
                    ? 'bg-gruvbox-dark-orange text-gruvbox-dark-bg'
                    : 'bg-gruvbox-light-orange text-gruvbox-light-bg'
                  : isDark
                  ? 'hover:bg-gruvbox-dark-bg'
                  : 'hover:bg-gruvbox-light-bg-soft'
              }`}
            >
              <div className="font-medium">{step.description}</div>
              {step.linked_ingredient_names && step.linked_ingredient_names.length > 0 && (
                <div
                  className={`text-xs mt-1 ${
                    index === highlightedIndex
                      ? isDark
                        ? 'text-gruvbox-dark-bg-soft'
                        : 'text-gruvbox-light-bg-soft'
                      : isDark
                      ? 'text-gruvbox-dark-gray'
                      : 'text-gruvbox-light-gray'
                  }`}
                >
                  ({step.linked_ingredient_names.join(', ')})
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PrepStepAutocomplete;
