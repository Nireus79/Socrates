/**
 * ChatPage - Main dialogue interface for Socratic conversations
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { Search, MessageSquare, Wifi, WifiOff } from 'lucide-react';
import { useChatStore, useProjectStore } from '../../stores';
import { apiClient } from '../../api';
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
import { Card, LoadingSpinner, Alert, Button, Input } from '../../components/common';

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
  const {
    messages,
    searchResults,
    mode,
    isLoading: chatLoading,
    isSearching,
    isConnected,
    error: chatError,
    loadHistory,
    switchMode,
    sendMessage,
    requestHint,
    searchConversations,
    getSummary,
    connectWebSocket,
    disconnectWebSocket,
    handleWebSocketResponse,
    clearError,
    clearSearch,
  } = useChatStore();
  const { currentProject, isLoading: projectLoading, getProject } = useProjectStore();

  const [response, setResponse] = React.useState('');
  const [showHint, setShowHint] = React.useState(false);
  const [showSummary, setShowSummary] = React.useState(false);
  const [summaryData, setSummaryData] = React.useState<{ summary: string; key_points: string[] } | null>(null);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [selectedMessage, setSelectedMessage] = React.useState<ConversationItem | null>(null);
  const wsRef = React.useRef<WebSocket | null>(null);

  // Load project and chat history
  React.useEffect(() => {
    if (projectId) {
      getProject(projectId);
      loadHistory(projectId);
    }
  }, [projectId, getProject, loadHistory]);

  // WebSocket connection effect
  React.useEffect(() => {
    if (!projectId) return;

    const accessToken = apiClient.getAccessToken();
    if (!accessToken) return;

    const connectWS = async () => {
      try {
        await connectWebSocket(projectId, accessToken);
        // Get WebSocket URL from chat API
        const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const protocol = baseURL.startsWith('https') ? 'wss' : 'ws';
        const wsBaseURL = baseURL.replace(/^https?/, protocol);
        const wsURL = `${wsBaseURL}/ws/chat/${projectId}?token=${accessToken}`;

        wsRef.current = new WebSocket(wsURL);

        wsRef.current.onopen = () => {
          console.log('WebSocket connected');
        };

        wsRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            handleWebSocketResponse(data);
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        wsRef.current.onclose = () => {
          console.log('WebSocket disconnected');
          disconnectWebSocket();
        };
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
      }
    };

    connectWS();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      disconnectWebSocket();
    };
  }, [projectId, connectWebSocket, disconnectWebSocket, handleWebSocketResponse]);

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

  const handleSearchConversations = async () => {
    if (!searchQuery.trim() || !projectId) return;
    try {
      await searchConversations(projectId, searchQuery);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const handleGetSummary = async () => {
    if (!projectId) return;
    try {
      const summary = await getSummary(projectId);
      setSummaryData(summary);
      setShowSummary(true);
    } catch (error) {
      console.error('Failed to get summary:', error);
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
          <div className="flex justify-between items-start">
            <PageHeader
              title="Dialogue"
              description={currentProject ? `${currentProject.name}` : 'Loading...'}
            />
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
              isConnected
                ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-400'
            }`}>
              {isConnected ? (
                <>
                  <Wifi size={16} />
                  <span className="text-xs font-medium">Live</span>
                </>
              ) : (
                <>
                  <WifiOff size={16} />
                  <span className="text-xs font-medium">Offline</span>
                </>
              )}
            </div>
          </div>

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

              <Card>
                <div className="space-y-3">
                  <Button
                    onClick={handleGetSummary}
                    disabled={chatLoading || messages.length === 0}
                    variant="outline"
                    className="w-full flex items-center justify-center gap-2"
                  >
                    <MessageSquare size={18} />
                    Get Summary
                  </Button>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Search conversation..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') handleSearchConversations();
                      }}
                      disabled={isSearching}
                    />
                    <Button
                      onClick={handleSearchConversations}
                      disabled={isSearching || !searchQuery.trim()}
                      variant="primary"
                      className="flex items-center gap-2"
                    >
                      <Search size={18} />
                      Search
                    </Button>
                  </div>
                </div>
              </Card>
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

      {/* Summary Modal */}
      {showSummary && summaryData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="max-w-2xl w-full">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                Conversation Summary
              </h3>
              <button
                onClick={() => setShowSummary(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Summary
                </h4>
                <p className="text-gray-700 dark:text-gray-300">
                  {summaryData.summary}
                </p>
              </div>

              {summaryData.key_points && summaryData.key_points.length > 0 && (
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    Key Points
                  </h4>
                  <ul className="space-y-2">
                    {summaryData.key_points.map((point, index) => (
                      <li
                        key={`point-${index}-${point.substring(0, 20)}`}
                        className="flex gap-2 text-gray-700 dark:text-gray-300"
                      >
                        <span className="text-blue-600 dark:text-blue-400 font-bold">
                          •
                        </span>
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                Search Results ({searchResults.length})
              </h3>
              <button
                onClick={() => clearSearch()}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              {searchResults.map((result) => (
                <div
                  key={result.id}
                  className="border-l-4 border-blue-500 pl-4 py-2"
                >
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                    {result.role === 'user' ? 'You' : 'Assistant'}
                  </p>
                  <p className="text-gray-900 dark:text-gray-100">
                    {result.content.substring(0, 200)}
                    {result.content.length > 200 ? '...' : ''}
                  </p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

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
