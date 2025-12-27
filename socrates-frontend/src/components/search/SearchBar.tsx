/**
 * SearchBar - Search input with type selector and filter options
 */

import React, { useState } from 'react';
import { Search, X, ChevronDown } from 'lucide-react';
import { Button } from '../common';

type SearchType = 'all' | 'conversations' | 'knowledge' | 'notes';

interface SearchBarProps {
  onSearch: (query: string, type: SearchType) => void;
  isLoading?: boolean;
  placeholder?: string;
}

const SEARCH_TYPES: { value: SearchType; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'conversations', label: 'Conversations' },
  { value: 'knowledge', label: 'Knowledge' },
  { value: 'notes', label: 'Notes' },
];

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  isLoading = false,
  placeholder = 'Search projects, conversations, knowledge...',
}) => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<SearchType>('all');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const handleSearch = () => {
    if (query.trim()) {
      onSearch(query, searchType);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleClear = () => {
    setQuery('');
  };

  const selectedTypeLabel = SEARCH_TYPES.find(t => t.value === searchType)?.label || 'All';

  return (
    <div className="w-full">
      <div className="flex flex-col sm:flex-row gap-2">
        {/* Search Type Selector */}
        <div className="relative min-w-max">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          >
            {selectedTypeLabel}
            <ChevronDown className="h-4 w-4" />
          </button>

          {/* Dropdown Menu */}
          {isDropdownOpen && (
            <div className="absolute top-full mt-1 left-0 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg z-10 min-w-max">
              {SEARCH_TYPES.map(type => (
                <button
                  key={type.value}
                  onClick={() => {
                    setSearchType(type.value);
                    setIsDropdownOpen(false);
                  }}
                  className={`w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors ${
                    searchType === type.value
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                      : 'text-gray-900 dark:text-white'
                  } first:rounded-t-lg last:rounded-b-lg`}
                >
                  {type.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Search Input */}
        <div className="flex-1 flex items-center gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 dark:text-gray-500" />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
              disabled={isLoading}
            />
            {query && (
              <button
                onClick={handleClear}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>

          {/* Search Button */}
          <Button
            onClick={handleSearch}
            disabled={!query.trim() || isLoading}
            isLoading={isLoading}
            icon={<Search className="h-5 w-5" />}
          >
            <span className="hidden sm:inline">Search</span>
          </Button>
        </div>
      </div>
    </div>
  );
};
