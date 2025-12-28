/**
 * ProgressTracker - Display project progress metrics
 */

import React from 'react';
import { MessageSquare, Code2, FileText, BookOpen, TrendingUp } from 'lucide-react';

interface ProgressItem {
  label: string;
  count: number;
  icon: React.ReactNode;
  color: string;
}

interface ProgressTrackerProps {
  conversationCount?: number;
  codeGenerationCount?: number;
  documentationCount?: number;
  knowledgeEntriesCount?: number;
  trendStatus?: string;
  isLoading?: boolean;
}

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  conversationCount = 0,
  codeGenerationCount = 0,
  documentationCount = 0,
  knowledgeEntriesCount = 0,
  trendStatus = 'stable',
  isLoading = false,
}) => {
  const items: ProgressItem[] = [
    {
      label: 'Conversations',
      count: conversationCount,
      icon: <MessageSquare className="h-5 w-5" />,
      color: 'text-blue-600 dark:text-blue-400',
    },
    {
      label: 'Generated Code',
      count: codeGenerationCount,
      icon: <Code2 className="h-5 w-5" />,
      color: 'text-green-600 dark:text-green-400',
    },
    {
      label: 'Documentation',
      count: documentationCount,
      icon: <FileText className="h-5 w-5" />,
      color: 'text-purple-600 dark:text-purple-400',
    },
    {
      label: 'Knowledge Entries',
      count: knowledgeEntriesCount,
      icon: <BookOpen className="h-5 w-5" />,
      color: 'text-orange-600 dark:text-orange-400',
    },
  ];

  const getTrendIcon = () => {
    if (trendStatus === 'improving') {
      return <TrendingUp className="h-5 w-5 text-green-600 dark:text-green-400" />;
    } else if (trendStatus === 'declining') {
      return <TrendingUp className="h-5 w-5 text-red-600 dark:text-red-400 rotate-180" />;
    }
    return <TrendingUp className="h-5 w-5 text-gray-400 dark:text-gray-600" />;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-500 dark:text-gray-400">Loading progress data...</div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Project Progress
        </h3>
        <div className="flex items-center gap-2 text-sm font-medium">
          <span className="text-gray-600 dark:text-gray-400 capitalize">{trendStatus}</span>
          {getTrendIcon()}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {items.map((item) => (
          <div
            key={item.label}
            className="p-4 rounded-lg bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <div className={`${item.color} mb-2`}>
              {item.icon}
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {item.count}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {item.label}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
