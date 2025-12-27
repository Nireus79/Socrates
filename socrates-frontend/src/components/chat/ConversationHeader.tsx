/**
 * ConversationHeader - Compact header bar for chat interface
 * Shows project name, phase progress, mode toggle, and action buttons
 */

import React from 'react';
import { Search, MessageSquare } from 'lucide-react';
import { Button } from '../common';
import { CompactPhaseIndicator } from './CompactPhaseIndicator';
import { DialogueMode } from './DialogueMode';
import type { ChatMode } from '../../types/models';

interface Phase {
  number: number;
  name: string;
  isComplete: boolean;
  isCurrent: boolean;
  description: string;
  isLocked: boolean;
}

interface ConversationHeaderProps {
  projectName: string;
  mode: ChatMode;
  currentPhase: number;
  phases: Phase[];
  onModeChange: (mode: ChatMode) => void;
  onSearch: () => void;
  onSummary: () => void;
}

export const ConversationHeader: React.FC<ConversationHeaderProps> = ({
  projectName,
  mode,
  currentPhase,
  phases,
  onModeChange,
  onSearch,
  onSummary,
}) => {
  // Simplify phases for CompactPhaseIndicator
  const simplePhases = phases.map((p) => ({
    number: p.number,
    name: p.name,
    isComplete: p.isComplete,
    isCurrent: p.isCurrent,
  }));

  return (
    <div className="flex items-center justify-between border-b border-gray-200 px-6 py-3 bg-white dark:bg-gray-950 dark:border-gray-800">
      {/* Left: Project name + Phase dots */}
      <div className="flex items-center gap-4 min-w-0">
        <h1 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
          {projectName || 'Project'}
        </h1>
        <CompactPhaseIndicator
          currentPhase={currentPhase}
          phases={simplePhases}
        />
      </div>

      {/* Center: Mode toggle */}
      <div className="flex items-center gap-2">
        <div className="text-sm text-gray-600 dark:text-gray-400">Mode:</div>
        <DialogueMode
          mode={mode}
          onModeChange={onModeChange}
          variant="compact"
        />
      </div>

      {/* Right: Action buttons */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onSearch}
          title="Search conversation"
          className="p-2"
        >
          <Search size={18} />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onSummary}
          title="Get conversation summary"
          className="p-2"
        >
          <MessageSquare size={18} />
        </Button>
      </div>
    </div>
  );
};

ConversationHeader.displayName = 'ConversationHeader';
