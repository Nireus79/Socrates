/**
 * ConversationHistory Component - Scrollable list of past Q&A pairs
 */

import React from 'react';
import { ChevronDown, Trash2 } from 'lucide-react';
import { Card, Button, EmptyState, Input } from '../common';

export interface ConversationItem {
  id: string;
  questionNumber: number;
  category: string;
  question: string;
  answer: string;
  timestamp: Date;
  confidence?: number;
}

interface ConversationHistoryProps {
  items: ConversationItem[];
  isLoading?: boolean;
  onSelectItem?: (item: ConversationItem) => void;
  onDeleteItem?: (id: string) => void;
  onClearHistory?: () => void;
  searchable?: boolean;
}

export const ConversationHistory: React.FC<ConversationHistoryProps> = ({
  items,
  isLoading = false,
  onSelectItem,
  onDeleteItem,
  onClearHistory,
  searchable = true,
}) => {
  const [expandedId, setExpandedId] = React.useState<string | null>(null);
  const [searchTerm, setSearchTerm] = React.useState('');

  const filteredItems = items.filter(
    (item) =>
      item.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.answer.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Card className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Conversation History
        </h3>
        {onClearHistory && items.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearHistory}
            className="text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900"
          >
            Clear All
          </Button>
        )}
      </div>

      {/* Search */}
      {searchable && items.length > 0 && (
        <Input
          placeholder="Search conversation..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          disabled={isLoading}
        />
      )}

      {/* List */}
      {filteredItems.length === 0 ? (
        <EmptyState
          icon={<ChevronDown className="h-12 w-12" />}
          title={items.length === 0 ? 'No conversation yet' : 'No matching items'}
          description={
            items.length === 0
              ? 'Your conversation history will appear here as you answer questions'
              : 'Try a different search term'
          }
        />
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {filteredItems.map((item) => {
            const isExpanded = expandedId === item.id;

            return (
              <div
                key={item.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
              >
                <button
                  onClick={() => setExpandedId(isExpanded ? null : item.id)}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex justify-between items-start gap-3"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-1 rounded">
                        Q{item.questionNumber}
                      </span>
                      <span className="text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-2 py-1 rounded">
                        {item.category}
                      </span>
                      {item.confidence && (
                        <span className="text-xs font-medium bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-1 rounded">
                          {item.confidence}% confidence
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {item.question}
                    </p>
                  </div>

                  <ChevronDown
                    className={`h-4 w-4 text-gray-400 flex-shrink-0 transition-transform ${
                      isExpanded ? 'rotate-180' : ''
                    }`}
                  />
                </button>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-3 bg-gray-50 dark:bg-gray-800 space-y-3">
                    <div>
                      <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                        Question:
                      </p>
                      <p className="text-sm text-gray-900 dark:text-gray-100">
                        {item.question}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                        Your Answer:
                      </p>
                      <p className="text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
                        {item.answer}
                      </p>
                    </div>

                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {item.timestamp.toLocaleString()}
                    </div>

                    <div className="flex gap-2">
                      {onSelectItem && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => onSelectItem(item)}
                          fullWidth
                        >
                          View Details
                        </Button>
                      )}
                      {onDeleteItem && (
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Trash2 className="h-3 w-3" />}
                          onClick={() => onDeleteItem(item.id)}
                        />
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
};

ConversationHistory.displayName = 'ConversationHistory';
