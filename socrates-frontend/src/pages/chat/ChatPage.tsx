/**
 * ChatPage - Main dialogue interface for Socratic conversations
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { useChatStore, useProjectStore } from '../../stores';
import { MainLayout, PageHeader } from '../../components/layout';
import {
  QuestionDisplay,
  ResponseInput,
  ConversationHistory,
  PhaseIndicator,
  DialogueMode,
  HintDisplay,
  ChatMessage,
} from '../../components/chat';
import type { ConversationItem } from '../../components/chat';
import { Card, LoadingSpinner, Alert } from '../../components/common';

interface DialogueQuestion {
  id: string;
  number: number;
  category: string;
  question: string;
  context?: string;
  hints?: string[];
}

export const ChatPage: React.FC = () => {
  const { projectId } = useParams<{ projectId?: string }>();
  const { messages, mode, isLoading: chatLoading, error: chatError, loadHistory, switchMode, sendMessage, requestHint, clearError } = useChatStore();
  const { currentProject, isLoading: projectLoading, getProject } = useProjectStore();

  const [response, setResponse] = React.useState('');
  const [showHint, setShowHint] = React.useState(false);
  const [selectedMessage, setSelectedMessage] = React.useState<ConversationItem | null>(null);

  // Load project and chat history
  React.useEffect(() => {
    if (projectId) {
      getProject(projectId);
      loadHistory(projectId);
    }
  }, [projectId, getProject, loadHistory]);

  const handleSubmitResponse = async () => {
    if (!response.trim()) return;
    if (!projectId) return;

    try {
      await sendMessage(response);
      setResponse('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleSkipQuestion = async () => {
    if (!projectId) return;
    try {
      // In a real implementation, this would skip to the next question
      // For now, we just clear the response
      setResponse('');
    } catch (error) {
      console.error('Failed to skip question:', error);
    }
  };

  const handleSwitchMode = async (newMode: 'socratic' | 'direct') => {
    if (!projectId) return;
    try {
      await switchMode(projectId, newMode);
    } catch (error) {
      console.error('Failed to switch mode:', error);
    }
  };

  const handleRequestHint = async () => {
    if (!projectId) return;
    try {
      await requestHint(projectId);
      setShowHint(true);
    } catch (error) {
      console.error('Failed to get hint:', error);
    }
  };

  const isLoading = chatLoading || projectLoading;

  if (isLoading && !currentProject) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <LoadingSpinner size="lg" />
        </div>
      </MainLayout>
    );
  }

  const phases = [
    {
      number: 1,
      name: 'Discovery',
      description: 'Understand requirements and context',
      isComplete: currentProject?.phase !== 'discovery',
      isCurrent: currentProject?.phase === 'discovery',
      isLocked: false,
    },
    {
      number: 2,
      name: 'Analysis',
      description: 'Analyze the problem and identify solutions',
      isComplete: ['design', 'implementation'].includes(currentProject?.phase || ''),
      isCurrent: currentProject?.phase === 'analysis',
      isLocked: currentProject?.phase === 'discovery',
    },
    {
      number: 3,
      name: 'Design',
      description: 'Design the solution architecture',
      isComplete: currentProject?.phase === 'implementation',
      isCurrent: currentProject?.phase === 'design',
      isLocked: !['analysis', 'design', 'implementation'].includes(currentProject?.phase || ''),
    },
    {
      number: 4,
      name: 'Implementation',
      description: 'Implement and iterate on the solution',
      isComplete: false,
      isCurrent: currentProject?.phase === 'implementation',
      isLocked: currentProject?.phase !== 'implementation',
    },
  ];

  if (chatError) {
    return (
      <MainLayout>
        <Alert type="error" title="Error Loading Dialogue">
          <p className="mb-3">{chatError}</p>
          <button
            onClick={() => clearError()}
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            Dismiss
          </button>
        </Alert>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel - Question Display and Mode */}
        <div className="lg:col-span-1 space-y-6">
          <PageHeader
            title="Dialogue"
            description={currentProject ? `${currentProject.name}` : 'Loading...'}
          />

          {currentProject && (
            <>
              <Card>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Current Phase
                </h3>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {phases.find((p) => p.isCurrent)?.name || 'Unknown'}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                  {phases.find((p) => p.isCurrent)?.description}
                </p>
              </Card>

              <DialogueMode
                mode={mode}
                onModeChange={handleSwitchMode}
              />
            </>
          )}
        </div>

        {/* Center Panel - Response Input and History */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Your Response
            </h2>
            <ResponseInput
              value={response}
              onChange={setResponse}
              onSubmit={handleSubmitResponse}
              onSkip={handleSkipQuestion}
              onRequestHint={handleRequestHint}
              isLoading={chatLoading}
              minLength={1}
              maxLength={5000}
            />
          </Card>

          {/* ConversationHistory requires structured Q&A pairs, not raw chat messages */}
        </div>

        {/* Right Panel - Phase and Maturity Tracking */}
        <div className="lg:col-span-1 space-y-6">
          <PhaseIndicator
            phases={phases}
            currentPhase={phases.findIndex((p) => p.isCurrent) + 1}
            maturityByPhase={{
              1: 0,
              2: 0,
              3: 0,
              4: 0,
            }}
            onAdvance={() => {
              // Phase advancement would be handled by store
            }}
            canAdvance={false}
          />

          {/* Chat Messages Display */}
          {messages.length > 0 && (
            <Card>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Recent Messages
              </h3>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {messages.slice(-3).map((msg) => (
                  <ChatMessage
                    key={msg.id}
                    role={msg.role}
                    content={msg.content}
                    timestamp={msg.timestamp ? new Date(msg.timestamp) : new Date()}
                  />
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Hint Modal */}
      <HintDisplay
        isOpen={showHint}
        onClose={() => setShowHint(false)}
        hint="Check the project context for hints"
        questionNumber={1}
      />
    </MainLayout>
  );
};
