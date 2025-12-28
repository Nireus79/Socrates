/**
 * DocumentFilters Component
 *
 * Provides advanced filtering and sorting for knowledge base documents:
 * - Document type filter (text/file/url)
 * - Full-text search with debouncing
 * - Sort by (uploaded_at, title, document_type)
 * - Sort order (asc/desc)
 * - Clear all filters button
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useKnowledgeStore } from '../../stores/knowledgeStore';
import type { DocumentListFilters } from '../../types/models';

interface DocumentFiltersProps {
  onFiltersChange?: (filters: DocumentListFilters) => void;
}

export default function DocumentFilters({ onFiltersChange }: DocumentFiltersProps) {
  const { filters, setFilters, resetFilters, loadDocuments } = useKnowledgeStore();

  const [searchInput, setSearchInput] = useState(filters.searchQuery || '');
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);

  // Debounced search
  useEffect(() => {
    // Clear previous timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    // Set new timeout for search
    const timeout = setTimeout(() => {
      if (searchInput !== filters.searchQuery) {
        setFilters({ searchQuery: searchInput });
      }
    }, 300);

    setSearchTimeout(timeout);

    return () => {
      if (timeout) clearTimeout(timeout);
    };
  }, [searchInput, filters.searchQuery, setFilters]);

  const handleDocumentTypeChange = (value: string) => {
    setFilters({
      documentType: (value as any) || undefined,
    });
  };

  const handleSortByChange = (value: string) => {
    setFilters({
      sortBy: value as 'uploaded_at' | 'title' | 'document_type',
    });
  };

  const handleSortOrderChange = (value: string) => {
    setFilters({
      sortOrder: value as 'asc' | 'desc',
    });
  };

  const handleClearFilters = () => {
    setSearchInput('');
    resetFilters();
  };

  const hasActiveFilters =
    filters.searchQuery || filters.documentType || filters.sortBy !== 'uploaded_at' || filters.sortOrder !== 'desc';

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="space-y-4">
        {/* Search Input */}
        <div>
          <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Search Documents
          </label>
          <div className="relative">
            <input
              id="search"
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by title or source..."
              className="w-full px-4 py-2 pl-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white transition-colors"
            />
            <svg
              className="absolute left-3 top-2.5 h-5 w-5 text-gray-400 dark:text-gray-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>

        {/* Filter Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Document Type Filter */}
          <div>
            <label htmlFor="type" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Document Type
            </label>
            <select
              id="type"
              value={filters.documentType || ''}
              onChange={(e) => handleDocumentTypeChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white bg-white transition-colors"
            >
              <option value="">All Types</option>
              <option value="text">Text</option>
              <option value="file">File</option>
              <option value="url">URL</option>
            </select>
          </div>

          {/* Sort By */}
          <div>
            <label htmlFor="sortby" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Sort By
            </label>
            <select
              id="sortby"
              value={filters.sortBy || 'uploaded_at'}
              onChange={(e) => handleSortByChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white bg-white transition-colors"
            >
              <option value="uploaded_at">Upload Date</option>
              <option value="title">Title</option>
              <option value="document_type">Type</option>
            </select>
          </div>

          {/* Sort Order */}
          <div>
            <label htmlFor="order" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Sort Order
            </label>
            <select
              id="order"
              value={filters.sortOrder || 'desc'}
              onChange={(e) => handleSortOrderChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white bg-white transition-colors"
            >
              <option value="desc">Newest First</option>
              <option value="asc">Oldest First</option>
            </select>
          </div>
        </div>

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <div className="flex justify-end">
            <button
              onClick={handleClearFilters}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
            >
              <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Clear All Filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
