/**
 * Search Panel - Knowledge base search interface
 *
 * Features:
 * - Full-text search query input
 * - Adjustable result count (top-k)
 * - Project filtering
 * - Real-time search execution
 */

import React from 'react';
import { Search, X } from 'lucide-react';
import { useKnowledgeStore } from '../../stores';
import { Input } from '../common';
import { Button } from '../common';
import { Card } from '../common';

interface SearchPanelProps {
  projectId?: string;
  onSearch?: () => void;
  onClear?: () => void;
}

export const SearchPanel: React.FC<SearchPanelProps> = ({
  projectId,
  onSearch,
  onClear,
}) => {
  const { searchKnowledge, searchResults, isSearching, currentQuery } =
    useKnowledgeStore();

  const [query, setQuery] = React.useState('');
  const [topK, setTopK] = React.useState(10);
  const [hasSearched, setHasSearched] = React.useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    try {
      await searchKnowledge(query.trim(), projectId, topK);
      setHasSearched(true);
      onSearch?.();
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  const handleClear = () => {
    setQuery('');
    setHasSearched(false);
    onClear?.();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <Card>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
            Search Knowledge Base
          </label>
          <div className="flex gap-2">
            <Input
              type="text"
              placeholder="Enter search query..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isSearching}
              icon={<Search className="h-4 w-4" />}
              className="flex-1"
            />
            <Button
              onClick={handleSearch}
              disabled={isSearching || !query.trim()}
              isLoading={isSearching}
            >
              Search
            </Button>
            {hasSearched && (
              <Button
                variant="secondary"
                onClick={handleClear}
                icon={<X className="h-4 w-4" />}
              >
                Clear
              </Button>
            )}
          </div>
        </div>

        {/* Results per page selector */}
        <div className="flex items-center gap-4">
          <label className="text-sm text-gray-600 dark:text-gray-400">
            Results per page:
          </label>
          <select
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white"
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
        </div>

        {/* Search info */}
        {hasSearched && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Found <span className="font-semibold">{searchResults.length}</span>{' '}
            result{searchResults.length !== 1 ? 's' : ''} for "{currentQuery}"
          </div>
        )}
      </div>
    </Card>
  );
};
