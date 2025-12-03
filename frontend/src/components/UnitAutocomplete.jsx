import { useState, useEffect, useRef } from 'react';
import Fuse from 'fuse.js';
import { useTheme } from '../context/ThemeContext';
import { getAllUnits, formatUnitLabel, getGroupedUnits, getCategoryOrder } from '../utils/ingredientUnits';

/**
 * Autocomplete component for ingredient unit selection.
 * 
 * Features:
 * - Fuzzy search with fuse.js
 * - Grouped by category (Volume, Weight, Count, Special)
 * - Sorted alphabetically within groups
 * - Keyboard navigation (arrow keys, enter, escape)
 * - Theme-aware styling
 */
const UnitAutocomplete = ({ value, onChange, onBlur, required }) => {
  const { isDark } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [filteredUnits, setFilteredUnits] = useState([]);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);

  // Initialize fuse.js for fuzzy search
  const fuse = useRef(null);
  useEffect(() => {
    const allUnits = getAllUnits();
    fuse.current = new Fuse(allUnits, {
      keys: ['label', 'value'], // Only search label and value, not category
      threshold: 0.3,           // 0 = exact match, 1 = match anything
      ignoreLocation: true,
      distance: 100,            // How far to search for a match
      minMatchCharLength: 2,    // Minimum match length for better results
    });
  }, []);

  // Update filtered units when search term changes
  useEffect(() => {
    if (!searchTerm.trim()) {
      // No search term - show all units grouped
      const grouped = getGroupedUnits();
      const categoryOrder = getCategoryOrder();
      const flattened = [];
      
      categoryOrder.forEach((category) => {
        if (grouped[category]) {
          grouped[category].forEach((unit) => {
            flattened.push(unit);
          });
        }
      });
      
      setFilteredUnits(flattened);
      setHighlightedIndex(-1);
    } else {
      // Search with fuse.js
      const results = fuse.current.search(searchTerm);
      const filtered = results.map((result) => result.item);
      setFilteredUnits(filtered);
      // Auto-highlight first result for quick Enter selection
      setHighlightedIndex(filtered.length > 0 ? 0 : -1);
    }
  }, [searchTerm]);

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
    if (value) {
      setSearchTerm(formatUnitLabel(value));
    } else {
      setSearchTerm('');
    }
  }, [value]);

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    setSearchTerm(newValue);
    setIsOpen(true);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  const handleInputBlur = () => {
    // Delay to allow click on dropdown item
    setTimeout(() => {
      if (onBlur) {
        onBlur();
      }
    }, 200);
  };

  const handleSelectUnit = (unit) => {
    onChange(unit.value);
    setSearchTerm(unit.label);
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
          prev < filteredUnits.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && filteredUnits[highlightedIndex]) {
          handleSelectUnit(filteredUnits[highlightedIndex]);
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

  // Group filtered units by category for display
  const groupedFiltered = {};
  const categoryOrder = getCategoryOrder();
  
  if (!searchTerm.trim()) {
    // When not searching, show groups with headers
    filteredUnits.forEach((unit) => {
      if (!groupedFiltered[unit.category]) {
        groupedFiltered[unit.category] = [];
      }
      groupedFiltered[unit.category].push(unit);
    });
  }

  return (
    <div className="relative">
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          onKeyDown={handleKeyDown}
          required={required}
          placeholder="Select unit..."
          className={`w-full p-2 rounded border ${
            isDark
              ? 'bg-gruvbox-dark-bg border-gruvbox-dark-gray text-gruvbox-dark-fg focus:border-gruvbox-dark-orange-bright'
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

      {isOpen && filteredUnits.length > 0 && (
        <div
          ref={dropdownRef}
          className={`absolute z-10 w-full mt-1 max-h-60 overflow-y-auto rounded border shadow-lg ${
            isDark
              ? 'bg-gruvbox-dark-bg-soft border-gruvbox-dark-gray'
              : 'bg-gruvbox-light-bg border-gruvbox-light-gray'
          }`}
        >
          {!searchTerm.trim() ? (
            // Grouped display when not searching
            categoryOrder.map((category) =>
              groupedFiltered[category] && groupedFiltered[category].length > 0 ? (
                <div key={category}>
                  <div
                    className={`px-3 py-1 text-xs font-semibold sticky top-0 ${
                      isDark
                        ? 'bg-gruvbox-dark-bg-soft text-gruvbox-dark-gray'
                        : 'bg-gruvbox-light-bg text-gruvbox-light-gray'
                    }`}
                  >
                    {category}
                  </div>
                  {groupedFiltered[category].map((unit, index) => {
                    const globalIndex = filteredUnits.indexOf(unit);
                    return (
                      <div
                        key={unit.value}
                        onClick={() => handleSelectUnit(unit)}
                        className={`px-3 py-2 cursor-pointer ${
                          globalIndex === highlightedIndex
                            ? isDark
                              ? 'bg-gruvbox-dark-orange text-gruvbox-dark-bg'
                              : 'bg-gruvbox-light-orange text-gruvbox-light-bg'
                            : isDark
                            ? 'hover:bg-gruvbox-dark-bg'
                            : 'hover:bg-gruvbox-light-bg-soft'
                        }`}
                      >
                        {unit.label}
                      </div>
                    );
                  })}
                </div>
              ) : null
            )
          ) : (
            // Flat list when searching
            filteredUnits.map((unit, index) => (
              <div
                key={unit.value}
                onClick={() => handleSelectUnit(unit)}
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
                <div>{unit.label}</div>
                <div
                  className={`text-xs ${
                    index === highlightedIndex
                      ? isDark
                        ? 'text-gruvbox-dark-bg-soft'
                        : 'text-gruvbox-light-bg-soft'
                      : isDark
                      ? 'text-gruvbox-dark-gray'
                      : 'text-gruvbox-light-gray'
                  }`}
                >
                  {unit.category}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default UnitAutocomplete;
