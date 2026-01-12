/**
 * SearchPage - Full-text search across projects, conversations, knowledge, and notes
 */

import React, { useEffect, useState } from 'react';
import { useSearchStore } from '../../stores/searchStore';
import { useProjectStore } from '../../stores/projectStore';
import { SearchBar, SearchResultsGrid, SearchFilters } from '../../components/search';
import { MainLayout, PageHeader } from '../../components/layout';
import { Card } from '../../components/common';
import type { SearchFilterType, DateFilter } from '../../components/search/SearchFilters';

export const SearchPage: React.FC = () => {
  const searchStore = useSearchStore();
  const { projects, listProjects } = useProjectStore();
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<SearchFilterType>('all');
  const [dateFilter, setDateFilter] = useState<DateFilter>('any');

  useEffect(() => {
    // Load projects on mount
    listProjects();
    // Clear search on page load
    searchStore.clear();
  }, [listProjects]);

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
    <MainLayout>
      {/* Header */}
      <PageHeader
        title="Search"
        description="Find projects, conversations, knowledge, and notes"
      />

      {/* Project Selector */}
      {projects.length > 0 && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 dark:from-blue-900 dark:to-indigo-900 dark:border-blue-800">
            <div className="flex items-center gap-3">
              <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">
                Select Project:
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="">-- Choose a Project --</option>
                {projects.map((project) => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
          </Card>
        </div>
      )}

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
    </MainLayout>
  );
};
