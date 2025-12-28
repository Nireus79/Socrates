/**
 * SearchResultsGrid - Display search results in grid format
 */

import React from 'react';
import { FileText, MessageSquare, BookOpen, StickyNote, Calendar, Eye } from 'lucide-react';
import type { SearchResult } from '../../api/search';

interface SearchResultsGridProps {
  results: SearchResult[];
  isLoading?: boolean;
  query?: string;
  onResultClick?: (result: SearchResult) => void;
}

const getIconForType = (type: SearchResult['type']) => {
  switch (type) {
    case 'conversation':
      return <MessageSquare className="h-5 w-5" />;
    case 'knowledge':
      return <BookOpen className="h-5 w-5" />;
    case 'note':
      return <StickyNote className="h-5 w-5" />;
    case 'project':
      return <FileText className="h-5 w-5" />;
    default:
      return <FileText className="h-5 w-5" />;
  }
};

const getColorForType = (type: SearchResult['type']) => {
  switch (type) {
    case 'conversation':
      return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400';
    case 'knowledge':
      return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
    case 'note':
      return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400';
    case 'project':
      return 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400';
    default:
      return 'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-400';
  }
};

const formatDate = (dateString?: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

export const SearchResultsGrid: React.FC<SearchResultsGridProps> = ({
  results,
  isLoading = false,
  query = '',
  onResultClick,
}) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Searching...</p>
        </div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Eye className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400">
            {query ? `No results found for "${query}"` : 'Start searching to see results'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {results.map(result => (
        <div
          key={result.id}
          onClick={() => onResultClick?.(result)}
          className="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md dark:hover:shadow-gray-900/50 transition-shadow cursor-pointer"
        >
          {/* Header with Type Badge */}
          <div className="flex items-start justify-between mb-3">
            <div className={`flex items-center gap-2 px-2 py-1 rounded ${getColorForType(result.type)}`}>
              {getIconForType(result.type)}
              <span className="text-xs font-medium capitalize">{result.type}</span>
            </div>
            {result.score !== undefined && (
              <div className="text-xs font-medium text-gray-600 dark:text-gray-400">
                {(result.score * 100).toFixed(0)}%
              </div>
            )}
          </div>

          {/* Title */}
          <h3 className="font-semibold text-gray-900 dark:text-white mb-1 line-clamp-2 text-sm">
            {result.title}
          </h3>

          {/* Description */}
          {result.description && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
              {result.description}
            </p>
          )}

          {/* Content Preview */}
          {result.content && (
            <p className="text-xs text-gray-500 dark:text-gray-500 mb-3 line-clamp-2 bg-gray-50 dark:bg-gray-900/50 p-2 rounded">
              {result.content}
            </p>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            {result.createdAt && (
              <div className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                <span>{formatDate(result.createdAt)}</span>
              </div>
            )}
            {result.projectId && (
              <div className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-gray-700 dark:text-gray-300">
                Project
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
