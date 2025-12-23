/**
 * ProjectHeader Component - Project title, type, status with quick actions
 */

import React from 'react';
import { MessageSquare, Code, TrendingUp, Settings } from 'lucide-react';
import { Badge, Button } from '../common';

interface ProjectHeaderProps {
  name: string;
  type: string;
  phase: number;
  maturity: number;
  onContinueDialogue?: () => void;
  onGenerateCode?: () => void;
  onViewAnalytics?: () => void;
  onSettings?: () => void;
}

const typeVariants: Record<string, string> = {
  'software': 'blue',
  'business': 'green',
  'creative': 'purple',
  'research': 'pink',
  'marketing': 'orange',
  'educational': 'indigo',
};

const phaseNames = [
  'Discovery',
  'Analysis',
  'Design',
  'Implementation',
];

export const ProjectHeader: React.FC<ProjectHeaderProps> = ({
  name,
  type,
  phase,
  maturity,
  onContinueDialogue,
  onGenerateCode,
  onViewAnalytics,
  onSettings,
}) => {
  return (
    <div className="space-y-6">
      {/* Title and Type */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white truncate">
            {name}
          </h1>
          <div className="flex flex-wrap gap-2 mt-3">
            <Badge variant={typeVariants[type.toLowerCase()] as any}>
              {type}
            </Badge>
            <Badge variant="secondary">
              Phase {phase}: {phaseNames[phase - 1]}
            </Badge>
          </div>
        </div>

        {onSettings && (
          <Button
            variant="secondary"
            icon={<Settings className="h-4 w-4" />}
            onClick={onSettings}
            className="flex-shrink-0"
          >
            Settings
          </Button>
        )}
      </div>

      {/* Maturity and Progress */}
      <div className="flex items-center gap-8 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900 dark:to-indigo-900 rounded-lg">
        <div className="flex-1">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            Project Maturity
          </p>
          <div className="flex items-center gap-3">
            <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              {maturity}%
            </div>
            <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-300"
                style={{ width: `${maturity}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Action Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {onContinueDialogue && (
          <Button
            variant="primary"
            fullWidth
            icon={<MessageSquare className="h-4 w-4" />}
            onClick={onContinueDialogue}
          >
            Continue Dialogue
          </Button>
        )}
        {onGenerateCode && (
          <Button
            variant="secondary"
            fullWidth
            icon={<Code className="h-4 w-4" />}
            onClick={onGenerateCode}
          >
            Generate Code
          </Button>
        )}
        {onViewAnalytics && (
          <Button
            variant="outline"
            fullWidth
            icon={<TrendingUp className="h-4 w-4" />}
            onClick={onViewAnalytics}
          >
            View Analytics
          </Button>
        )}
      </div>
    </div>
  );
};

ProjectHeader.displayName = 'ProjectHeader';
