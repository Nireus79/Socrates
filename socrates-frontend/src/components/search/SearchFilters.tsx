/**
 * SearchFilters - Filter options for search results
 */

import React from 'react';
import { X } from 'lucide-react';

export type SearchFilterType = 'all' | 'project' | 'conversation' | 'knowledge' | 'note';
export type DateFilter = 'any' | 'week' | 'month' | 'year';

interface SearchFiltersProps {
  selectedType?: SearchFilterType;
  selectedDate?: DateFilter;
  resultCount?: number;
  onTypeChange?: (type: SearchFilterType) => void;
  onDateChange?: (date: DateFilter) => void;
  onClear?: () => void;
}

const FILTER_TYPES: { value: SearchFilterType; label: string }[] = [
  { value: 'all', label: 'All Types' },
  { value: 'project', label: 'Projects' },
  { value: 'conversation', label: 'Conversations' },
  { value: 'knowledge', label: 'Knowledge' },
  { value: 'note', label: 'Notes' },
];

const DATE_FILTERS: { value: DateFilter; label: string }[] = [
  { value: 'any', label: 'Any Time' },
  { value: 'week', label: 'Past Week' },
  { value: 'month', label: 'Past Month' },
  { value: 'year', label: 'Past Year' },
];

export const SearchFilters: React.FC<SearchFiltersProps> = ({
  selectedType = 'all',
  selectedDate = 'any',
  resultCount = 0,
  onTypeChange,
  onDateChange,
  onClear,
}) => {
  const hasActiveFilters = selectedType !== 'all' || selectedDate !== 'any';

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex flex-col sm:flex-row gap-4 flex-1">
          {/* Type Filter */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Type
            </label>
            <select
              value={selectedType}
              onChange={e => onTypeChange?.(e.target.value as SearchFilterType)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
            >
              {FILTER_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Date Filter */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Date
            </label>
            <select
              value={selectedDate}
              onChange={e => onDateChange?.(e.target.value as DateFilter)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
            >
              {DATE_FILTERS.map(date => (
                <option key={date.value} value={date.value}>
                  {date.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Clear Filters */}
        <div className="flex items-center gap-4 flex-1 sm:flex-none justify-between sm:justify-end">
          {resultCount > 0 && (
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <span className="font-semibold">{resultCount}</span> results
            </div>
          )}
          {hasActiveFilters && (
            <button
              onClick={onClear}
              className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            >
              <X className="h-4 w-4" />
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="mt-3 flex flex-wrap gap-2">
          {selectedType !== 'all' && (
            <span className="inline-flex items-center gap-2 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs rounded">
              Type: {FILTER_TYPES.find(t => t.value === selectedType)?.label}
              <button
                onClick={() => onTypeChange?.('all')}
                className="hover:text-blue-900 dark:hover:text-blue-200"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
          {selectedDate !== 'any' && (
            <span className="inline-flex items-center gap-2 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs rounded">
              Date: {DATE_FILTERS.find(d => d.value === selectedDate)?.label}
              <button
                onClick={() => onDateChange?.('any')}
                className="hover:text-blue-900 dark:hover:text-blue-200"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  );
};
