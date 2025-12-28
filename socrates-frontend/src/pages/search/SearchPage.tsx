/**
 * SearchPage - Full-text search across projects, conversations, knowledge, and notes
 */

import React, { useEffect, useState } from 'react';
import { useSearchStore } from '../../stores/searchStore';
import { SearchBar, SearchResultsGrid, SearchFilters } from '../../components/search';
import { PageHeader } from '../../components/layout';
import type { SearchFilterType, DateFilter } from '../../components/search/SearchFilters';

export const SearchPage: React.FC = () => {
  const searchStore = useSearchStore();
  const [typeFilter, setTypeFilter] = useState<SearchFilterType>('all');
  const [dateFilter, setDateFilter] = useState<DateFilter>('any');

  useEffect(() => {
    // Clear search on page load
    searchStore.clear();
  }, []);

  const handleSearch = async (query: string, searchType: 'all' | 'conversations' | 'knowledge' | 'notes') => {
    // Convert search type to filter type if needed
    await searchStore.search(query, searchType);
  };

  const handleClearFilters = () => {
    setTypeFilter('all');
    setDateFilter('any');
  };

  // Filter results based on selected filters
  const filteredResults = searchStore.results.filter(result => {
    if (typeFilter !== 'all' && result.type !== typeFilter) {
      return false;
    }
    // Date filter could be applied here if backend supports it
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <PageHeader
        title="Search"
        description="Find projects, conversations, knowledge, and notes"
      />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Bar */}
        <div className="mb-6">
          <SearchBar
            onSearch={handleSearch}
            isLoading={searchStore.isLoading}
            placeholder="Search across all your projects and content..."
          />
        </div>

        {/* Error Display */}
        {searchStore.error && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-700 dark:text-red-400">{searchStore.error}</p>
            <button
              onClick={() => searchStore.clearError()}
              className="text-xs text-red-600 dark:text-red-500 underline mt-2"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Show filters only when there are results or an active search */}
        {(searchStore.results.length > 0 || searchStore.query) && (
          <SearchFilters
            selectedType={typeFilter}
            selectedDate={dateFilter}
            resultCount={filteredResults.length}
            onTypeChange={setTypeFilter}
            onDateChange={setDateFilter}
            onClear={handleClearFilters}
          />
        )}

        {/* Results */}
        <SearchResultsGrid
          results={filteredResults}
          isLoading={searchStore.isLoading}
          query={searchStore.query}
          onResultClick={result => {
            // In a real implementation, this would navigate to the result
            console.log('Clicked result:', result);
          }}
        />

        {/* Statistics */}
        {searchStore.results.length > 0 && !searchStore.isLoading && (
          <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
              Found <span className="font-semibold">{filteredResults.length}</span> result{filteredResults.length !== 1 ? 's' : ''}
              {searchStore.query && ` for "${searchStore.query}"`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
