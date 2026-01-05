/**
 * ChatPage - Main dialogue interface for Socratic conversations
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Search, MessageSquare, Send } from 'lucide-react';
import { useChatStore, useProjectStore, useSubscriptionStore } from '../../stores';
import { apiClient, chatAPI, nluAPI } from '../../api';
import type { NLUInterpretResponse } from '../../api/nlu';
import { MainLayout, PageHeader } from '../../components/layout';
import {
  ResponseInput,
  HintDisplay,
  ChatMessage,
  ConversationHeader,
  ConflictResolutionModal,
  SkippedQuestionsPanel,
  AnswerSuggestionsModal,
} from '../../components/chat';
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
    error: chatError,
    conflicts,
    pendingConflicts,
    loadHistory,
    switchMode,
    sendMessage,
    addMessage: addChatMessage,
    addSystemMessage,
    requestHint,
    searchConversations,
    getSummary,
    getQuestion,
    resolveConflict,
    clearConflicts,
    clearError,
    clearSearch,
    reset: resetChat,
    getSuggestions,
  } = useChatStore();
  const {
    projects,
    currentProject,
    isLoading: projectLoading,
    getProject,
    listProjects,
  } = useProjectStore();

  const [response, setResponse] = React.useState('');
  const [showHint, setShowHint] = React.useState(false);
  const [showSuggestions, setShowSuggestions] = React.useState(false);
  const [suggestions, setSuggestions] = React.useState<string[]>([]);
  const [suggestionsQuestion, setSuggestionsQuestion] = React.useState('');
  const [showSummary, setShowSummary] = React.useState(false);
  const [summaryData, setSummaryData] = React.useState<{ summary: string; key_points: string[] } | null>(null);
  const [showSearchModal, setShowSearchModal] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [searchInput, setSearchInput] = React.useState('');
  const [isSearchingModal, setIsSearchingModal] = React.useState(false);
  const [showDebugModal, setShowDebugModal] = React.useState(false);
  const [debugInfo, setDebugInfo] = React.useState<{ debugEnabled: boolean; timestamp: string } | null>(null);
  const [showTestingModeModal, setShowTestingModeModal] = React.useState(false);
  const [testingModeStatus, setTestingModeStatus] = React.useState<{ enabled: boolean; message: string } | null>(null);
  const [selectedProjectId, setSelectedProjectId] = React.useState(projectId || '');
  const [isSwitchingProject, setIsSwitchingProject] = React.useState(false);
  const [sessionStartTime, setSessionStartTime] = React.useState<Date | null>(null);

  // Pre-session NLU chat state
  const [freeSessionInput, setFreeSessionInput] = React.useState('');
  const [freeSessionResponses, setFreeSessionResponses] = React.useState<Array<{ role: 'user' | 'assistant'; content: string; type?: 'command' | 'suggestion' | 'message' }>>([]);
  const [isInterpretingNLU, setIsInterpretingNLU] = React.useState(false);

  // Refs for auto-scroll
  const messagesContainerRef = React.useRef<HTMLDivElement>(null);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const freeSessionEndRef = React.useRef<HTMLDivElement>(null);

  // Track if we've already loaded initial question for this project
  const initialQuestionLoadedRef = React.useRef<string | null>(null);
  const isLoadingHistoryRef = React.useRef<boolean>(false);

  // Load projects list on mount
  React.useEffect(() => {
    listProjects();
  }, [listProjects]);

  // Update selectedProjectId when URL projectId changes
  React.useEffect(() => {
    if (projectId) {
      setSelectedProjectId(projectId);
    }
  }, [projectId]);

  // Load project and chat history
  React.useEffect(() => {
    if (!selectedProjectId) return;

    // Skip if we've already loaded initial question for this project
    if (initialQuestionLoadedRef.current === selectedProjectId) {
      return;
    }

    // Skip if already loading history (prevent race condition)
    if (isLoadingHistoryRef.current) {
      return;
    }

    isLoadingHistoryRef.current = true;

    getProject(selectedProjectId);

    // Load history and then check for initial question
    loadHistory(selectedProjectId).then(() => {
      // Mark that we've loaded initial question for this project FIRST
      initialQuestionLoadedRef.current = selectedProjectId;
      isLoadingHistoryRef.current = false;

      // After history is loaded, check for unanswered questions
      const { messages: currentMessages, mode: currentMode, getQuestion: storeGetQuestion } = useChatStore.getState();

      // Mark session start time ONLY if not already set for this project
      // This prevents hiding messages when switching modes
      if (!sessionStartTime) {
        setSessionStartTime(new Date());
      }

      if (currentMode === 'socratic') {
        // Check if there's an unanswered question (last assistant message with no user answer after)
        let hasUnansweredQuestion = false;
        if (currentMessages.length > 0) {
          // Find the last assistant message
          for (let i = currentMessages.length - 1; i >= 0; i--) {
            if (currentMessages[i].role === 'assistant') {
              // Check if there's a user message after this assistant message
              const hasAnswerAfter = currentMessages.slice(i + 1).some(m => m.role === 'user');
              if (!hasAnswerAfter) {
                hasUnansweredQuestion = true;
              }
              break;
            }
          }
        }

        // Only generate new question if there's no unanswered question
        if (!hasUnansweredQuestion) {
          storeGetQuestion(selectedProjectId);
        }
      }
    }).catch(error => {
      console.error('Failed to load history:', error);
      isLoadingHistoryRef.current = false;
      // Mark that we've attempted to load for this project
      initialQuestionLoadedRef.current = selectedProjectId;

      // Still try to get initial question even if history load fails
      if (!sessionStartTime) {
        setSessionStartTime(new Date());
      }
      const { mode: currentMode, getQuestion: storeGetQuestion } = useChatStore.getState();
      if (currentMode === 'socratic') {
        storeGetQuestion(selectedProjectId);
      }
    });
  }, [selectedProjectId]);

  // Auto-scroll to bottom when messages change
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  // Auto-scroll for pre-session messages
  React.useEffect(() => {
    freeSessionEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [freeSessionResponses.length]);

  /**
   * Handle pre-session input with NLU command interpretation
   * Uses NLU system to interpret commands and natural language
   */
  const handleFreeSessionInput = async () => {
    if (!freeSessionInput.trim()) return;

    const userInput = freeSessionInput.trim();

    // Add user message
    setFreeSessionResponses(prev => [...prev, { role: 'user', content: userInput }]);
    setFreeSessionInput('');

    setIsInterpretingNLU(true);
    try {
      // Use NLU to interpret the input (handles both /commands and natural language)
      const nluResult = await nluAPI.interpret(userInput, {});

      if (nluResult.status === 'success' && nluResult.command) {
        // High confidence command match
        await handleNLUCommand(nluResult.command);
      } else if (nluResult.status === 'suggestions' && nluResult.suggestions?.length) {
        // Medium confidence - show suggestions
        const suggestionText = nluResult.suggestions
          .slice(0, 3)
          .map((s, i) => `${i + 1}. \`${s.command}\` (${Math.round(s.confidence * 100)}%) - ${s.reasoning}`)
          .join('\n');
        setFreeSessionResponses(prev => [...prev, {
          role: 'assistant',
          content: `I found a few possibilities:\n\n${suggestionText}\n\nTry typing one of these commands or rephrase your question!`,
          type: 'suggestion'
        }]);
      } else {
        // No command match - treat as free-form question for Claude
        await handleFreeFormQuestion(userInput);
      }
    } catch (error) {
      console.error('Pre-session input error:', error);
      setFreeSessionResponses(prev => [...prev, {
        role: 'assistant',
        content: "Sorry, I encountered an error. Please try again.",
        type: 'message'
      }]);
    } finally {
      setIsInterpretingNLU(false);
    }
  };

  /**
   * Handle NLU-interpreted commands
   */
  const handleNLUCommand = async (command: string) => {
    // Show command being executed
    setFreeSessionResponses(prev => [...prev, {
      role: 'assistant',
      content: `Understood! Executing: \`${command}\``,
      type: 'command'
    }]);

    // Extract command name for routing
    const cmdLower = command.toLowerCase();
    const cmdParts = cmdLower.split(/\s+/);
    const baseCmd = cmdParts[0]; // e.g., '/help', '/docs', '/subscription'

    // Commands that can be handled in pre-session (no project required)
    const freeSessionCommands = [
      '/help', '/info', '/docs', '/status', '/debug', '/menu', '/clear',
      '/exit', '/back', '/model', '/mode', '/nlu', '/subscription'
    ];

    // Check if this is a pre-session compatible command
    const isFreeSessionCommand = freeSessionCommands.includes(baseCmd);

    if (isFreeSessionCommand) {
      // Handle pre-session commands
      if (baseCmd === '/help') {
        handleFreeSessionCommand('/help');
      } else if (baseCmd === '/info') {
        handleFreeSessionCommand('/info');
      } else if (baseCmd === '/docs') {
        await handleFreeSessionCommand(command);
      } else if (baseCmd === '/status') {
        handleFreeSessionCommand('/status');
      } else if (baseCmd === '/subscription') {
        // Handle subscription commands (e.g., /subscription testing-mode on/off)
        await handleFreeSessionSubscriptionCommand(command);
      } else {
        // For other pre-session commands, show a generic message
        setFreeSessionResponses(prev => [...prev, {
          role: 'assistant',
          content: `Command \`${command}\` has been recognized. This feature may require project context or additional setup.`,
          type: 'message'
        }]);
      }
    } else {
      // Commands that require a project
      setFreeSessionResponses(prev => [...prev, {
        role: 'assistant',
        content: `This command requires an active project or workspace. Create or select a project to use this feature!`,
        type: 'message'
      }]);
    }
  };

  const handleFreeSessionSubscriptionCommand = async (command: string) => {
    // Import subscription store to update testing mode
    const { setTestingMode, refreshSubscription } = useSubscriptionStore.getState();

    // Parse subscription command for pre-session
    const parts = command.split(/\s+/);

    if (parts.length >= 3 && parts[1].toLowerCase() === 'testing-mode') {
      const mode = parts[2].toLowerCase(); // 'on' or 'off'
      const enabled = mode === 'on';

      try {
        const response = await apiClient.put<any>(
          `/auth/me/testing-mode?enabled=${enabled}`
        );

        const result = response?.data || response;
        const message = (result && result.message) || `Testing mode has been turned ${enabled ? 'ON' : 'OFF'}. All restrictions bypassed!`;

        // Update the store to reflect testing mode change
        setTestingMode(enabled);
        // Refresh subscription to ensure consistency
        await refreshSubscription();

        setFreeSessionResponses(prev => [...prev, {
          role: 'assistant',
          content: message,
          type: 'message'
        }]);
      } catch (error) {
        console.error('Subscription command error:', error);
        setFreeSessionResponses(prev => [...prev, {
          role: 'assistant',
          content: `Failed to execute subscription command. Please try again.`,
          type: 'message'
        }]);
      }
    } else {
      setFreeSessionResponses(prev => [...prev, {
        role: 'assistant',
        content: `Usage: /subscription testing-mode [on|off]`,
        type: 'message'
      }]);
    }
  };

  /**
   * Handle free-form questions without command match
   */
  const handleFreeFormQuestion = async (question: string) => {
    try {
      const response = await apiClient.post<any>(
        '/free_session/ask',
        {
          question,
          context: {}
        }
      );

      const result = response.data;
      if (result?.answer) {
        setFreeSessionResponses(prev => [...prev, {
          role: 'assistant',
          content: result.answer,
          type: 'message'
        }]);
      } else {
        setFreeSessionResponses(prev => [...prev, {
          role: 'assistant',
          content: "I couldn't process that question. Please try again or use a command like /help.",
          type: 'message'
        }]);
      }
    } catch (error) {
      console.error('Free-form question error:', error);
      setFreeSessionResponses(prev => [...prev, {
        role: 'assistant',
        content: "Sorry, I encountered an error. Please try again.",
        type: 'message'
      }]);
    }
  };

  const handleFreeSessionCommand = async (command: string) => {
    const parts = command.split(' ');
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1).join(' ');

    // Handle pre-session specific commands
    switch (cmd) {
      case '/help':
        // Fetch available commands from backend
        setIsInterpretingNLU(true);
        try {
          const commands = await nluAPI.getAvailableCommands();

          let helpText = `## Available Commands\n\n`;

          if (Object.keys(commands).length > 0) {
            // Group commands by category
            for (const [category, commandList] of Object.entries(commands)) {
              helpText += `### ${category.toUpperCase()}\n`;
              for (const cmd of (commandList as any)) {
                helpText += `**${cmd.usage}** - ${cmd.description}\n`;
              }
              helpText += '\n';
            }
          } else {
            // Fallback to basic commands if fetch fails
            helpText += `**/help** - Show this help message\n` +
              `**/info** - Show system information\n` +
              `**/docs** [topic] - Get documentation on a topic\n` +
              `**/status** - Show system status\n` +
              `**/debug** - Debug information\n` +
              `**/subscription testing-mode [on|off]** - Toggle testing mode\n\n`;
          }

          helpText += `**Or just type a question** to chat with Claude about anything!`;

          setFreeSessionResponses(prev => [...prev, {
            role: 'assistant',
            content: helpText,
            type: 'command'
          }]);
        } catch (error) {
          console.error('Error fetching commands:', error);
          // Fallback help text
          const fallbackHelp = `## Available Commands\n\n` +
            `**/help** - Show this help message\n` +
            `**/info** - Show system information\n` +
            `**/docs** [topic] - Get documentation on a topic\n` +
            `**/status** - Show system status\n` +
            `**/subscription testing-mode [on|off]** - Toggle testing mode\n\n` +
            `**Or just type a question** to chat with Claude about anything!`;
          setFreeSessionResponses(prev => [...prev, {
            role: 'assistant',
            content: fallbackHelp,
            type: 'command'
          }]);
        } finally {
          setIsInterpretingNLU(false);
        }
        break;

      case '/info':
        const infoText = `# Socrates - AI-Powered Socratic Tutoring System\n\n` +
          `**Version:** 8.0.0 | **Status:** Ready\n\n` +
          `## Features\n` +
          `- 🎓 Socratic method learning\n` +
          `- 💬 Interactive dialogue\n` +
          `- 💻 Code generation and analysis\n` +
          `- 📚 Knowledge base & documentation\n` +
          `- 👥 Team collaboration\n\n` +
          `## Get Started\n` +
          `- Ask questions to explore\n` +
          `- Use /docs to learn more\n` +
          `- Create a project for guided learning`;
        setFreeSessionResponses(prev => [...prev, {
          role: 'assistant',
          content: infoText,
          type: 'command'
        }]);
        break;

      case '/docs':
        // Handle /docs command by asking Claude for documentation
        setIsInterpretingNLU(true);
        try {
          const topic = args || 'Socrates';
          const docQuestion = `Provide a brief guide on: ${topic}. Focus on key features and how to use it.`;

          const response = await apiClient.post<any>(
            '/free_session/ask',
            {
              question: docQuestion,
              context: {}
            }
          );

          const result = response.data;
          if (result?.answer) {
            setFreeSessionResponses(prev => [...prev, {
              role: 'assistant',
              content: result.answer,
              type: 'message'
            }]);
          } else {
            setFreeSessionResponses(prev => [...prev, {
              role: 'assistant',
              content: `Could not retrieve documentation for "${topic}". Try asking a question instead!`,
              type: 'command'
            }]);
          }
        } catch (error) {
          console.error('Docs error:', error);
          setFreeSessionResponses(prev => [...prev, {
            role: 'assistant',
            content: `Error retrieving documentation. Please try again.`,
            type: 'command'
          }]);
        } finally {
          setIsInterpretingNLU(false);
        }
        break;

      case '/status':
        setFreeSessionResponses(prev => [...prev, {
          role: 'assistant',
          content: `The /status command requires an active project. Create or select a project to see its status.`,
          type: 'command'
        }]);
        break;

      default:
        setFreeSessionResponses(prev => [...prev, {
          role: 'assistant',
          content: `Unknown command: \`${cmd}\`. Type /help for available commands.`,
          type: 'command'
        }]);
    }
  };

  const handleSubmitResponse = async () => {
    if (!response.trim()) return;

    // Handle slash commands
    const trimmedResponse = response.trim();
    if (trimmedResponse.startsWith('/')) {
      handleSlashCommand(trimmedResponse);
      setResponse('');
      return;
    }

    if (!selectedProjectId) return;

    try {
      await sendMessage(response);
      setResponse('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  /**
   * Handle switching to a different project
   * If a project is already loaded, calls /done before switching
   */
  const handleProjectSwitch = async (newProjectId: string) => {
    if (!newProjectId || newProjectId === selectedProjectId) return;

    setIsSwitchingProject(true);
    try {
      // If a project is currently loaded, finish the session first
      if (currentProject && currentProject.project_id !== newProjectId) {
        try {
          await chatAPI.finishSession(currentProject.project_id);
          addSystemMessage(`Session finished for "${currentProject.name}"`);
        } catch (error) {
          console.error('Failed to finish previous session:', error);
          addSystemMessage('Warning: Could not properly finish previous session');
        }
      }

      // Clear old chat state before loading new project
      resetChat();

      // Load the new project
      setSelectedProjectId(newProjectId);
      addSystemMessage(`Switched to project`);
    } catch (error) {
      console.error('Failed to switch project:', error);
      addSystemMessage('Failed to switch project');
    } finally {
      setIsSwitchingProject(false);
    }
  };

  const handleSlashCommand = async (command: string) => {
    const parts = command.split(' ');
    const cmd = parts[0].toLowerCase();
    const subCmd = parts[1]?.toLowerCase();

    switch (cmd) {
      case '/help':
        handleHelpCommand();
        break;
      case '/status':
        if (selectedProjectId) handleStatusCommand(selectedProjectId);
        else addSystemMessage('No project selected');
        break;
      case '/stats':
        if (selectedProjectId) handleStatsCommand(selectedProjectId);
        else addSystemMessage('No project selected');
        break;
      case '/info':
        handleInfoCommand();
        break;
      case '/logs':
        handleLogsCommand(parts[1]);
        break;
      case '/knowledge':
        if (selectedProjectId) handleKnowledgeCommand(selectedProjectId, subCmd, parts.slice(2));
        else addSystemMessage('No project selected');
        break;
      case '/analytics':
        if (selectedProjectId) handleAnalyticsCommand(selectedProjectId, subCmd);
        else addSystemMessage('No project selected');
        break;
      case '/maturity':
        if (selectedProjectId) handleMaturityCommand(selectedProjectId, subCmd);
        else addSystemMessage('No project selected');
        break;
      case '/debug':
        handleDebugCommand(subCmd || 'toggle');
        break;
      case '/subscription':
        handleSubscriptionCommand(subCmd, parts.slice(2));
        break;
      case '/note':
        if (selectedProjectId) handleNoteCommand(selectedProjectId, subCmd, parts.slice(2));
        else addSystemMessage('No project selected');
        break;
      case '/advance':
        if (selectedProjectId) handleAdvanceCommand(selectedProjectId);
        else addSystemMessage('No project selected');
        break;
      case '/done':
        if (selectedProjectId) handleDoneCommand(selectedProjectId);
        else addSystemMessage('No project selected');
        break;
      case '/ask':
        if (selectedProjectId) handleAskCommand(selectedProjectId, parts.slice(1));
        else addSystemMessage('No project selected');
        break;
      case '/explain':
        handleExplainCommand(parts.slice(1));
        break;
      case '/hint':
        if (selectedProjectId) handleHintCommand(selectedProjectId);
        else addSystemMessage('No project selected');
        break;
      case '/skipped':
        if (selectedProjectId) handleSkippedQuestionsCommand(selectedProjectId, subCmd, parts.slice(2));
        else addSystemMessage('No project selected');
        break;
      case '/project':
        if (selectedProjectId) handleProjectCommand(selectedProjectId, subCmd, parts.slice(2));
        else addSystemMessage('No project selected');
        break;
      case '/docs':
        handleDocsCommand(subCmd, parts.slice(2));
        break;
      case '/code':
        if (selectedProjectId) handleCodeCommand(selectedProjectId, subCmd, parts.slice(2));
        else addSystemMessage('No project selected');
        break;
      case '/finalize':
        if (selectedProjectId) handleFinalizeCommand(selectedProjectId, subCmd);
        else addSystemMessage('No project selected');
        break;
      case '/collab':
        if (selectedProjectId) handleCollabCommand(selectedProjectId, subCmd, parts.slice(2));
        else addSystemMessage('No project selected');
        break;
      case '/skills':
        if (selectedProjectId) handleSkillsCommand(selectedProjectId, subCmd, parts.slice(2));
        else addSystemMessage('No project selected');
        break;
      case '/github':
        if (selectedProjectId) handleGithubCommand(selectedProjectId, subCmd);
        else addSystemMessage('No project selected');
        break;
      case '/conversation':
        if (selectedProjectId) handleConversationCommand(selectedProjectId, subCmd, parts.slice(2));
        else addSystemMessage('No project selected');
        break;
      default:
        addSystemMessage(`Unknown command: ${cmd}. Type /help for available commands.`);
    }
  };

  const handleDebugCommand = async (action: string) => {
    try {
      // Call backend endpoint to toggle debug mode
      let url = '/system/debug/toggle';

      // Normalize action: trim and lowercase
      const normalizedAction = action.trim().toLowerCase();

      // Add enabled parameter if action is 'on' or 'off'
      if (normalizedAction === 'on') {
        url += '?enabled=true';
      } else if (normalizedAction === 'off') {
        url += '?enabled=false';
      }
      // If no action or 'toggle', don't add enabled param to toggle state

      const response = await apiClient.post<any>(url);

      // apiClient.post() returns response.data directly (SuccessResponse object)
      const isEnabled = response?.data?.debug_enabled ?? false;

      setDebugInfo({
        debugEnabled: isEnabled,
        timestamp: new Date().toISOString(),
      });
      setShowDebugModal(true);

      addSystemMessage(`Debug mode ${isEnabled ? 'enabled' : 'disabled'}`);
    } catch (error) {
      console.error('Failed to toggle debug mode:', error);
      addSystemMessage('Failed to toggle debug mode');
    }
  };

  const handleTestingModeCommand = async (action: string) => {
    if (!action || (action !== 'on' && action !== 'off')) {
      addSystemMessage('Usage: /subscription testing-mode on|off');
      return;
    }

    try {
      // Call API to toggle testing mode (enabled is a query parameter)
      const enabled = action === 'on';
      await apiClient.put(`/auth/me/testing-mode?enabled=${enabled}`);
      setTestingModeStatus({
        enabled,
        message: enabled
          ? 'Testing mode enabled - all restrictions bypassed'
          : 'Testing mode disabled - normal restrictions apply',
      });
      setShowTestingModeModal(true);

      addSystemMessage(`Testing mode ${enabled ? 'enabled' : 'disabled'}`);
    } catch (error) {
      console.error('Failed to toggle testing mode:', error);
      addSystemMessage('Failed to toggle testing mode');
    }
  };

  const handleHelpCommand = () => {
    const helpText = `Available Commands:

SYSTEM:
  /help - Show this help message
  /status - Show project status
  /stats - Show project statistics
  /info - Show system information
  /logs [lines] - View system logs (default: 20 lines)
  /debug [on|off] - Toggle debug mode

CHAT & PHASES:
  /advance - Advance to next project phase
  /done - Finish current session
  /ask <question> - Ask direct question (not Socratic mode)
  /explain <topic> - Explain a concept
  /hint - Get hint for current question
  /skipped - View and reopen skipped questions

PROJECT ANALYSIS:
  /project analyze - Analyze code structure
  /project test - Run project tests
  /project fix - Apply automated fixes
  /project validate - Validate project
  /project review - Get code review

NOTES & KNOWLEDGE:
  /note add <text> - Add project note
  /note list - List all notes
  /note search <query> - Search notes
  /note delete <id> - Delete note
  /knowledge add|list|search - Knowledge management

DOCUMENTATION & CODE:
  /docs import - Import file documentation
  /docs import-url - Import from URL
  /docs paste - Import text content
  /docs list - List all documents
  /code generate - Generate code
  /code docs - Generate documentation
  /finalize generate - Generate final artifacts
  /finalize docs - Generate final documentation

COLLABORATION & SKILLS:
  /collab add <user> - Add collaborator
  /collab list - List collaborators
  /collab remove <user> - Remove collaborator
  /collab role <user> <role> - Change role
  /skills set - Set project skills
  /skills list - List project skills

SUBSCRIPTION & GITHUB:
  /subscription status - Show subscription tier
  /subscription upgrade - Upgrade subscription
  /subscription downgrade - Downgrade subscription
  /subscription compare - Compare subscription tiers
  /subscription testing-mode on|off - Toggle testing mode
  /github import - Import GitHub repository
  /github pull - Pull latest changes
  /github push - Push changes
  /github sync - Bidirectional sync

ANALYTICS & CONVERSATIONS:
  /analytics [breakdown|status] - View analytics data
  /maturity [history|status] - View maturity tracking
  /conversation search <query> - Search conversation history
  /conversation summary - Summarize conversation`;
    addSystemMessage(helpText);
  };

  const handleStatusCommand = async (id: string) => {
    try {
      const response = await apiClient.get(`/projects/${id}/progress`) as any;
      const data = response?.data || response;
      const overall = data?.overall_progress || {};
      const status = overall?.status || 'unknown';
      const progress = overall?.percentage || 0;
      const phase = currentProject?.phase || 'N/A';
      const maturity = data?.maturity_progress?.current_score || 0;

      addSystemMessage(`Project Status: ${status} | Phase: ${phase} | Progress: ${progress}% | Maturity: ${maturity}`);
    } catch (error) {
      addSystemMessage('Could not fetch project status');
    }
  };

  const handleStatsCommand = async (id: string) => {
    try {
      const response = await apiClient.get(`/projects/${id}/stats`) as any;
      const stats = response?.data || response;
      const summary = `Messages: ${stats.message_count || 0} | Insights: ${stats.insight_count || 0} | Questions: ${stats.question_count || 0}`;
      addSystemMessage(`Stats: ${summary}`);
    } catch (error) {
      addSystemMessage('Could not fetch project statistics');
    }
  };

  const handleInfoCommand = () => {
    const info = `System Information:
Project: ${currentProject?.name || 'None selected'}
Phase: ${currentProject?.phase || 'N/A'}
Mode: ${mode}
User: ${currentProject?.owner || 'N/A'}`;
    addSystemMessage(info);
  };

  const handleLogsCommand = async (lines: string) => {
    try {
      const numLines = parseInt(lines) || 20;
      const response = await apiClient.post('/system/logs', { lines: numLines }) as any;
      const logText = response?.logs || 'No logs available';
      addSystemMessage(`Recent logs (${numLines} lines):\n${logText}`);
    } catch (error) {
      addSystemMessage('Could not fetch system logs');
    }
  };

  const handleKnowledgeCommand = async (id: string, action: string, args: string[]) => {
    try {
      if (action === 'add') {
        const text = args.join(' ');
        if (!text) {
          addSystemMessage('Usage: /knowledge add <text>');
          return;
        }
        await apiClient.post(`/projects/${id}/knowledge/add`, { content: text });
        addSystemMessage('Knowledge entry added');
      } else if (action === 'list') {
        const response = await apiClient.get(`/projects/${id}/knowledge/list`) as any;
        const entries = response?.entries || [];
        if (entries.length === 0) {
          addSystemMessage('No knowledge entries found');
        } else {
          const list = entries.map((e: any) => `• ${e.content?.substring(0, 50) || 'N/A'}`).join('\n');
          addSystemMessage(`Knowledge Entries:\n${list}`);
        }
      } else if (action === 'search') {
        const query = args.join(' ');
        if (!query) {
          addSystemMessage('Usage: /knowledge search <query>');
          return;
        }
        const response = await apiClient.post(`/projects/${id}/knowledge/search`, { query }) as any;
        const results = response?.results || [];
        if (results.length === 0) {
          addSystemMessage('No matching knowledge found');
        } else {
          const list = results.map((r: any) => `• ${r.content?.substring(0, 50) || 'N/A'}`).join('\n');
          addSystemMessage(`Search Results:\n${list}`);
        }
      } else {
        addSystemMessage('Usage: /knowledge [add|list|search]');
      }
    } catch (error) {
      console.error('Knowledge command error:', error);
      addSystemMessage('Knowledge command failed');
    }
  };

  const handleAnalyticsCommand = async (id: string, action?: string) => {
    try {
      const response = action === 'breakdown'
        ? (await apiClient.get(`/analytics/projects/${id}`) as any)
        : action === 'status'
        ? (await apiClient.get(`/analytics/projects/${id}`) as any)
        : (await apiClient.get(`/analytics/projects/${id}`) as any);

      const data = response?.data || response;

      // Format analytics data for readable display
      let summary = '📊 Analytics Report\n\n';
      if (data.maturity_score !== undefined) {
        summary += `Overall Maturity: ${data.maturity_score.toFixed(2)}\n`;
      }

      if (data.phase_maturity_scores) {
        summary += '\nPhase Scores:\n';
        Object.entries(data.phase_maturity_scores).forEach(([phase, score]: [string, any]) => {
          summary += `  • ${phase}: ${score.toFixed(2)}\n`;
        });
      }

      if (data.completion_percentage !== undefined) {
        summary += `\nCompletion: ${data.completion_percentage.toFixed(1)}%\n`;
      }

      if (data.total_questions !== undefined) {
        summary += `\nTotal Questions Asked: ${data.total_questions}\n`;
      }

      if (data.average_response_time !== undefined) {
        summary += `Avg Response Time: ${data.average_response_time.toFixed(2)}s\n`;
      }

      // If no formatted data was added, show raw JSON
      if (summary === '📊 Analytics Report\n\n') {
        summary += JSON.stringify(data, null, 2);
      }

      addSystemMessage(summary);
    } catch (error) {
      addSystemMessage('Could not fetch analytics data');
    }
  };

  const handleMaturityCommand = async (id: string, action?: string) => {
    try {
      const response = action === 'history'
        ? (await apiClient.get(`/projects/${id}/maturity/history`) as any)
        : action === 'status'
        ? (await apiClient.get(`/projects/${id}/maturity/status`) as any)
        : (await apiClient.get(`/projects/${id}/maturity`) as any);

      const data = response?.data || response;

      // Format maturity data for readable display
      let summary = '📈 Maturity Report\n\n';

      if (data.overall_maturity !== undefined) {
        summary += `Overall Maturity: ${data.overall_maturity.toFixed(2)}\n`;
      } else if (data.maturity_score !== undefined) {
        summary += `Overall Maturity: ${data.maturity_score.toFixed(2)}\n`;
      }

      if (data.phase_maturity_scores) {
        summary += '\nPhase Scores:\n';
        Object.entries(data.phase_maturity_scores).forEach(([phase, score]: [string, any]) => {
          const displayPhase = phase.charAt(0).toUpperCase() + phase.slice(1);
          summary += `  • ${displayPhase}: ${score.toFixed(2)}\n`;
        });
      }

      if (data.current_phase) {
        summary += `\nCurrent Phase: ${data.current_phase}\n`;
      }

      if (data.readiness_percentage !== undefined) {
        summary += `Phase Readiness: ${data.readiness_percentage.toFixed(1)}%\n`;
      }

      if (data.issues_count !== undefined) {
        summary += `Open Issues: ${data.issues_count}\n`;
      }

      if (data.last_updated) {
        summary += `Last Updated: ${new Date(data.last_updated).toLocaleString()}\n`;
      }

      // If no formatted data was added, show raw JSON
      if (summary === '📈 Maturity Report\n\n') {
        summary += JSON.stringify(data, null, 2);
      }

      addSystemMessage(summary);
    } catch (error) {
      addSystemMessage('Could not fetch maturity data');
    }
  };

  // SUBSCRIPTION COMMANDS
  const handleSubscriptionCommand = async (action: string, args: string[]) => {
    const { refreshSubscription } = useSubscriptionStore.getState();
    try {
      if (action === 'testing-mode') {
        const mode = args[0]?.toLowerCase();
        if (!mode || (mode !== 'on' && mode !== 'off')) {
          addSystemMessage('Usage: /subscription testing-mode on|off');
          return;
        }
        await apiClient.put(`/auth/me/testing-mode?enabled=${mode === 'on'}`);
        // Refresh subscription store to pick up the testing_mode flag
        await refreshSubscription();
        setTestingModeStatus({
          enabled: mode === 'on',
          message: mode === 'on'
            ? 'Testing mode enabled - all restrictions bypassed'
            : 'Testing mode disabled - normal restrictions apply',
        });
        setShowTestingModeModal(true);
        addSystemMessage(`Testing mode ${mode}`);
      } else if (action === 'status') {
        const response = await apiClient.get('/subscription/status') as any;
        const tier = response?.tier || 'free';
        const status = response?.status || 'active';
        addSystemMessage(`📊 Subscription Status\nTier: ${tier}\nStatus: ${status}`);
      } else if (action === 'upgrade') {
        const plan = args[0]?.toLowerCase();
        if (!plan) {
          addSystemMessage('Usage: /subscription upgrade <plan>\nAvailable plans: pro, enterprise');
          return;
        }
        try {
          const response = await apiClient.post('/subscription/upgrade', { plan }) as any;
          addSystemMessage(`✅ Subscription upgraded to ${plan}\n${response?.message || 'Upgrade successful'}`);
        } catch (error) {
          addSystemMessage(`Could not upgrade to ${plan}. Please check the plan name or try again.`);
        }
      } else if (action === 'downgrade') {
        const plan = args[0]?.toLowerCase();
        if (!plan) {
          addSystemMessage('Usage: /subscription downgrade <plan>\nAvailable plans: free, pro');
          return;
        }
        try {
          const response = await apiClient.post('/subscription/downgrade', { plan }) as any;
          addSystemMessage(`✅ Subscription downgraded to ${plan}\n${response?.message || 'Downgrade successful'}`);
        } catch (error) {
          addSystemMessage(`Could not downgrade to ${plan}. Please check the plan name or try again.`);
        }
      } else if (action === 'compare') {
        const response = await apiClient.get('/subscription/plans') as any;
        const plans = response?.plans || [];
        if (plans.length === 0) {
          addSystemMessage('📋 Available Plans\nNo plans available at this time.');
        } else {
          const list = plans.map((p: any) => `• ${p.tier}: ${p.description || 'N/A'}`).join('\n');
          addSystemMessage(`📋 Available Plans\n${list}`);
        }
      } else {
        addSystemMessage('Usage: /subscription [status|upgrade|downgrade|compare|testing-mode on|off]');
      }
    } catch (error) {
      addSystemMessage('Subscription command failed');
    }
  };

  // NOTE COMMANDS
  const handleNoteCommand = async (id: string, action: string, args: string[]) => {
    try {
      if (action === 'add') {
        const text = args.join(' ');
        if (!text) {
          addSystemMessage('Usage: /note add <text>');
          return;
        }
        await apiClient.post(`/projects/${id}/notes`, { content: text });
        addSystemMessage('Note added');
      } else if (action === 'list') {
        const response = await apiClient.get(`/projects/${id}/notes`) as any;
        const notes = response?.notes || [];
        if (notes.length === 0) {
          addSystemMessage('No notes found');
        } else {
          const list = notes.map((n: any) => `• (${n.id}) ${n.content?.substring(0, 50)}`).join('\n');
          addSystemMessage(`Notes:\n${list}`);
        }
      } else if (action === 'search') {
        const query = args.join(' ');
        if (!query) {
          addSystemMessage('Usage: /note search <query>');
          return;
        }
        const response = await apiClient.post(`/projects/${id}/notes/search`, { query }) as any;
        const results = response?.results || [];
        if (results.length === 0) {
          addSystemMessage('No matching notes');
        } else {
          const list = results.map((n: any) => `• ${n.content?.substring(0, 50)}`).join('\n');
          addSystemMessage(`Search Results:\n${list}`);
        }
      } else if (action === 'delete') {
        const noteId = args[0];
        if (!noteId) {
          addSystemMessage('Usage: /note delete <id>');
          return;
        }
        await apiClient.delete(`/projects/${id}/notes/${noteId}`);
        addSystemMessage('Note deleted');
      } else {
        addSystemMessage('Usage: /note [add|list|search|delete]');
      }
    } catch (error) {
      addSystemMessage('Note command failed');
    }
  };

  // CORE CHAT COMMANDS
  const handleAdvanceCommand = async (id: string) => {
    try {
      await apiClient.put(`/projects/${id}/phase`);
      addSystemMessage('Advancing to next phase...');
    } catch (error) {
      addSystemMessage('Could not advance phase');
    }
  };

  const handleDoneCommand = async (id: string) => {
    try {
      await apiClient.post(`/projects/${id}/chat/done`);
      addSystemMessage('Session finished. Great work!');
    } catch (error) {
      addSystemMessage('Could not finish session');
    }
  };

  const handleAskCommand = async (id: string, args: string[]) => {
    const question = args.join(' ');
    if (!question) {
      addSystemMessage('Usage: /ask <question>');
      return;
    }
    try {
      await sendMessage(question);
    } catch (error) {
      addSystemMessage('Failed to send question');
    }
  };

  const handleExplainCommand = async (args: string[]) => {
    const topic = args.join(' ');
    if (!topic) {
      addSystemMessage('Usage: /explain <topic>');
      return;
    }
    try {
      const response = await apiClient.post('/query/explain', { topic }) as any;
      const explanation = response?.explanation || 'No explanation available';
      addSystemMessage(`Explanation of "${topic}":\n${explanation}`);
    } catch (error) {
      addSystemMessage('Could not explain topic');
    }
  };

  const handleHintCommand = async (id: string) => {
    try {
      const response = await apiClient.get(`/projects/${id}/chat/hint`) as any;
      const hint = response?.hint || 'No hint available';
      addSystemMessage(`💡 Hint:\n${hint}`);
    } catch (error) {
      addSystemMessage('Could not get hint');
    }
  };

  const handleSkippedQuestionsCommand = async (id: string, action?: string, args?: string[]) => {
    try {
      // Get all skipped questions
      const result = await chatAPI.getQuestions(id, 'skipped') as any;
      const questions = result?.questions || [];

      if (!questions || questions.length === 0) {
        addSystemMessage('No skipped questions found. All questions answered!');
        return;
      }

      if (action === 'reopen' && args && args.length > 0) {
        // Reopen specific question by index
        const index = parseInt(args[0]) - 1;
        if (index >= 0 && index < questions.length) {
          try {
            await chatAPI.reopenQuestion(id, questions[index].id || '');
            addSystemMessage(`Question reopened: "${questions[index].question}"\n\nYou can now answer it!`);
          } catch (error) {
            addSystemMessage('Failed to reopen question');
          }
        } else {
          addSystemMessage('Invalid question number');
        }
      } else {
        // List all skipped questions
        const listItems = questions
          .map((q: any, i: number) => `${i + 1}. ${q.question}\n   Phase: ${q.phase || 'unknown'}`)
          .join('\n\n');
        addSystemMessage(`Skipped Questions (${questions.length}):\n\n${listItems}\n\nUse "/skipped reopen [number]" to answer a specific question.`);
      }
    } catch (error) {
      addSystemMessage('Could not retrieve skipped questions');
    }
  };

  // PROJECT ANALYSIS COMMANDS
  const handleProjectCommand = async (id: string, action: string, args: string[]) => {
    try {
      switch (action) {
        case 'analyze':
          const analyzeResp = await apiClient.post('/analysis/structure', { project_id: id }) as any;
          addSystemMessage(`Analysis:\n${analyzeResp?.summary || 'Analysis complete'}`);
          break;
        case 'test':
          const testResp = await apiClient.post('/analysis/test', { project_id: id }) as any;
          addSystemMessage(`Tests: ${testResp?.summary || 'Tests executed'}`);
          break;
        case 'fix':
          const fixResp = await apiClient.post('/analysis/fix', { project_id: id }) as any;
          addSystemMessage(`Fixes Applied: ${fixResp?.summary || 'Fixes completed'}`);
          break;
        case 'validate':
          const validateResp = await apiClient.post('/analysis/validate', { project_id: id }) as any;
          addSystemMessage(`Validation: ${validateResp?.summary || 'Valid'}`);
          break;
        case 'review':
          const reviewResp = await apiClient.post('/analysis/review', { project_id: id }) as any;
          addSystemMessage(`Code Review:\n${reviewResp?.summary || 'Review complete'}`);
          break;
        default:
          addSystemMessage('Usage: /project [analyze|test|fix|validate|review]');
      }
    } catch (error) {
      addSystemMessage('Project command failed');
    }
  };

  // DOCUMENTATION COMMANDS
  const handleDocsCommand = async (action: string, args: string[]) => {
    try {
      switch (action) {
        case 'import':
          addSystemMessage('Usage: /docs import <file-path> (File import via form recommended)');
          break;
        case 'import-url':
          const url = args.join(' ');
          if (!url) {
            addSystemMessage('Usage: /docs import-url <url>');
            return;
          }
          const urlResp = await apiClient.post('/knowledge/import/url', { url }) as any;
          addSystemMessage('Document imported from URL');
          break;
        case 'paste':
          if (!selectedProjectId) {
            addSystemMessage('No project selected');
            return;
          }
          addSystemMessage('Usage: /docs paste <text> (Paste content via UI recommended)');
          break;
        case 'list':
          const listResp = await apiClient.get('/knowledge/documents') as any;
          const docs = listResp?.documents || [];
          if (docs.length === 0) {
            addSystemMessage('No documents');
          } else {
            const list = docs.map((d: any) => `• ${d.title || d.name}`).join('\n');
            addSystemMessage(`Documents:\n${list}`);
          }
          break;
        default:
          addSystemMessage('Usage: /docs [import|import-url|paste|list]');
      }
    } catch (error) {
      addSystemMessage('Documentation command failed');
    }
  };

  // CODE COMMANDS
  const handleCodeCommand = async (id: string, action: string, args: string[]) => {
    try {
      if (action === 'generate') {
        const response = await apiClient.post(`/projects/${id}/code/generate`) as any;
        addSystemMessage(`Code generated:\n${response?.code?.substring(0, 200) || 'Code generated'}`);
      } else if (action === 'docs') {
        const response = await apiClient.post(`/projects/${id}/docs/generate`) as any;
        addSystemMessage(`Documentation generated:\n${response?.docs?.substring(0, 200) || 'Docs generated'}`);
      } else {
        addSystemMessage('Usage: /code [generate|docs]');
      }
    } catch (error) {
      addSystemMessage('Code command failed');
    }
  };

  // FINALIZATION COMMANDS
  const handleFinalizeCommand = async (id: string, action: string) => {
    try {
      if (action === 'generate') {
        const response = await apiClient.post(`/projects/${id}/finalize/generate`) as any;
        addSystemMessage(`Artifacts generated:\n${response?.summary || 'Artifacts created'}`);
      } else if (action === 'docs') {
        const response = await apiClient.post(`/projects/${id}/finalize/docs`) as any;
        addSystemMessage(`Final documentation generated:\n${response?.summary || 'Docs created'}`);
      } else {
        addSystemMessage('Usage: /finalize [generate|docs]');
      }
    } catch (error) {
      addSystemMessage('Finalize command failed');
    }
  };

  // COLLABORATION COMMANDS
  const handleCollabCommand = async (id: string, action: string, args: string[]) => {
    try {
      if (action === 'add') {
        const username = args[0];
        if (!username) {
          addSystemMessage('Usage: /collab add <username>');
          return;
        }
        await apiClient.post(`/projects/${id}/collaborators`, { username, role: 'editor' });
        addSystemMessage(`Collaborator ${username} added`);
      } else if (action === 'list') {
        const response = await apiClient.get(`/projects/${id}/collaborators`) as any;
        const collabs = response?.collaborators || [];
        const list = collabs.map((c: any) => `• ${c.username} (${c.role})`).join('\n');
        addSystemMessage(`Collaborators:\n${list}`);
      } else if (action === 'remove') {
        const username = args[0];
        if (!username) {
          addSystemMessage('Usage: /collab remove <username>');
          return;
        }
        await apiClient.delete(`/projects/${id}/collaborators/${username}`);
        addSystemMessage(`Collaborator ${username} removed`);
      } else if (action === 'role') {
        const username = args[0];
        const role = args[1];
        if (!username || !role) {
          addSystemMessage('Usage: /collab role <username> <role>');
          return;
        }
        await apiClient.put(`/projects/${id}/collaborators/${username}/role`, { role });
        addSystemMessage(`Role updated: ${username} -> ${role}`);
      } else {
        addSystemMessage('Usage: /collab [add|list|remove|role]');
      }
    } catch (error) {
      addSystemMessage('Collaboration command failed');
    }
  };

  // SKILLS COMMANDS
  const handleSkillsCommand = async (id: string, action: string, args: string[]) => {
    try {
      if (action === 'set') {
        const skills = args.join(',').split(',').map((s: string) => s.trim());
        await apiClient.post(`/projects/${id}/skills`, { skills });
        addSystemMessage(`Skills updated: ${skills.join(', ')}`);
      } else if (action === 'list') {
        const response = await apiClient.get(`/projects/${id}/skills`) as any;
        const skills = response?.skills || [];
        addSystemMessage(`Skills: ${skills.join(', ')}`);
      } else {
        addSystemMessage('Usage: /skills [set|list]');
      }
    } catch (error) {
      addSystemMessage('Skills command failed');
    }
  };

  // GITHUB COMMANDS
  const handleGithubCommand = async (id: string, action: string) => {
    try {
      if (action === 'import') {
        addSystemMessage('Usage: /github import <repo-url>');
      } else if (action === 'pull') {
        const response = await apiClient.post(`/github/projects/${id}/pull`) as any;
        addSystemMessage('Latest changes pulled');
      } else if (action === 'push') {
        const response = await apiClient.post(`/github/projects/${id}/push`) as any;
        addSystemMessage('Changes pushed');
      } else if (action === 'sync') {
        const response = await apiClient.post(`/github/projects/${id}/sync`) as any;
        addSystemMessage('Repository synced');
      } else {
        addSystemMessage('Usage: /github [import|pull|push|sync]');
      }
    } catch (error) {
      addSystemMessage('GitHub command failed');
    }
  };

  // CONVERSATION COMMANDS
  const handleConversationCommand = async (id: string, action: string, args: string[]) => {
    try {
      if (action === 'search') {
        const query = args.join(' ');
        if (!query) {
          addSystemMessage('Usage: /conversation search <query>');
          return;
        }
        const response = await apiClient.post(`/projects/${id}/chat/search`, { query }) as any;
        const results = response?.results || [];
        if (results.length === 0) {
          addSystemMessage('No matching conversations');
        } else {
          const list = results.map((r: any) => `• ${r.substring(0, 50)}`).join('\n');
          addSystemMessage(`Search Results:\n${list}`);
        }
      } else if (action === 'summary') {
        const response = await apiClient.get(`/projects/${id}/chat/summary`) as any;
        const summary = response?.summary || 'No summary available';
        addSystemMessage(`Conversation Summary:\n${summary}`);
      } else {
        addSystemMessage('Usage: /conversation [search|summary]');
      }
    } catch (error) {
      addSystemMessage('Conversation command failed');
    }
  };

  const handleSkipQuestion = async () => {
    if (!selectedProjectId) return;
    try {
      // Mark question as skipped on backend
      await chatAPI.skipQuestion(selectedProjectId);

      // Add a skip marker message to conversation
      addChatMessage({
        id: `skip_${Date.now()}`,
        role: 'system',
        content: '[Question skipped by user]',
        timestamp: new Date().toISOString(),
      });

      // Clear input and generate next question
      setResponse('');
      await getQuestion(selectedProjectId);
    } catch (error) {
      console.error('Failed to skip question:', error);
      addSystemMessage('Failed to skip question');
    }
  };

  const handleSwitchMode = async (newMode: 'socratic' | 'direct') => {
    if (!selectedProjectId) return;
    try {
      await switchMode(selectedProjectId, newMode);
    } catch (error) {
      console.error('Failed to switch mode:', error);
    }
  };

  const handleRequestHint = async () => {
    if (!selectedProjectId) return;
    try {
      await requestHint(selectedProjectId);
      setShowHint(true);
    } catch (error) {
      console.error('Failed to get hint:', error);
    }
  };

  const handleRequestSuggestions = async () => {
    if (!selectedProjectId) return;
    try {
      const result = await getSuggestions(selectedProjectId);
      setSuggestions(result || []);
      setSuggestionsQuestion('Current question');
      setShowSuggestions(true);
    } catch (error) {
      console.error('Failed to get suggestions:', error);
    }
  };

  const handleSearchConversations = async () => {
    if (!searchQuery.trim() || !selectedProjectId) return;
    try {
      await searchConversations(selectedProjectId, searchQuery);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const handleGetSummary = async () => {
    if (!selectedProjectId) return;
    try {
      const summary = await getSummary(selectedProjectId);
      setSummaryData(summary);
      setShowSummary(true);
    } catch (error) {
      console.error('Failed to get summary:', error);
    }
  };

  const handleOpenSearch = () => {
    setShowSearchModal(true);
    setSearchInput('');
  };

  const handlePerformSearch = async () => {
    if (!searchInput.trim() || !selectedProjectId) return;

    setIsSearchingModal(true);
    try {
      await searchConversations(selectedProjectId, searchInput);
      // Search results are stored in store's searchResults
    } catch (error) {
      console.error('Search failed:', error);
      addSystemMessage('Search failed');
    } finally {
      setIsSearchingModal(false);
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
      <div className="flex flex-col h-[calc(100vh-4rem)] max-w-5xl mx-auto w-full">
        {/* Project Selector Dropdown */}
        <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 dark:from-blue-900 dark:to-indigo-900 dark:border-blue-800">
          <div className="flex items-center gap-3">
            <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">
              Active Project:
            </label>
            <select
              value={selectedProjectId}
              onChange={(e) => handleProjectSwitch(e.target.value)}
              disabled={isSwitchingProject}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="">-- Choose a Project --</option>
              {projects.length > 0 ? (
                projects.map((project) => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.name} {selectedProjectId === project.project_id ? '(Current)' : ''}
                  </option>
                ))
              ) : (
                <option disabled>No projects available</option>
              )}
            </select>
            {isSwitchingProject && (
              <div className="text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
                Switching...
              </div>
            )}
            {currentProject && (
              <div className="text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">
                Phase: <span className="font-semibold capitalize">{currentProject.phase || 'N/A'}</span>
              </div>
            )}
          </div>
        </Card>

        {/* Pre-Session Chat (when no project selected) */}
        {!selectedProjectId ? (
          <>
            {/* Pre-Session Header */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900 dark:to-blue-900">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Welcome to Socrates
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Ask me anything or describe what you'd like to do. I'll help guide you through the system.
              </p>
            </div>

            {/* Pre-Session Messages Area */}
            <div
              className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50 dark:bg-gray-900"
              ref={messagesContainerRef}
            >
              {freeSessionResponses.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-gray-500 dark:text-gray-400">
                    <MessageSquare className="mx-auto mb-4 text-gray-400" size={48} />
                    <p className="text-lg font-medium">Start a conversation</p>
                    <p className="text-sm mt-2">Type your question, describe what you want, or use commands like /help</p>
                  </div>
                </div>
              ) : (
                freeSessionResponses.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs px-4 py-3 rounded-lg ${
                        msg.role === 'user'
                          ? 'bg-blue-600 text-white rounded-br-none'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-bl-none'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                    </div>
                  </div>
                ))
              )}
              <div ref={freeSessionEndRef} />
            </div>

            {/* Pre-Session Input Area */}
            <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 p-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={freeSessionInput}
                  onChange={(e) => setFreeSessionInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleFreeSessionInput();
                    }
                  }}
                  disabled={isInterpretingNLU}
                  placeholder="Ask anything or try /help for commands..."
                  className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50"
                />
                <button
                  onClick={handleFreeSessionInput}
                  disabled={isInterpretingNLU || !freeSessionInput.trim()}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isInterpretingNLU ? (
                    <>
                      <LoadingSpinner size="sm" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Send size={18} />
                      Send
                    </>
                  )}
                </button>
              </div>
            </div>
          </>
        ) : (
          <>
            {/* Project-Specific Chat */}
            {/* Conversation Header */}
            <ConversationHeader
              projectName={currentProject?.name || 'Project'}
              mode={mode}
              currentPhase={phases.findIndex((p) => p.isCurrent) + 1}
              phases={phases}
              onModeChange={handleSwitchMode}
              onSearch={handleOpenSearch}
              onSummary={handleGetSummary}
            />

            {/* Messages Area - Full Height, Scrollable */}
            <div
              className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50 dark:bg-gray-900"
              ref={messagesContainerRef}
            >
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-gray-500 dark:text-gray-400">
                    <p className="text-lg">Conversation will start here...</p>
                    <p className="text-sm mt-2">The initial question will appear as the first message.</p>
                  </div>
                </div>
              ) : (
                messages.map((msg) => {
                  const messageTime = msg.timestamp ? new Date(msg.timestamp) : new Date();
                  const isPrevious = sessionStartTime ? messageTime < sessionStartTime : false;

                  // Only show current session messages (not previous conversation)
                  if (isPrevious) {
                    return null;
                  }

                  return (
                    <ChatMessage
                      key={msg.id || `msg-${msg.role}-${msg.timestamp}`}
                      role={msg.role}
                      content={msg.content}
                      timestamp={messageTime}
                      isFaded={false}
                    />
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area - Fixed at Bottom */}
            <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 p-4">
              <ResponseInput
                value={response}
                onChange={setResponse}
                onSubmit={handleSubmitResponse}
                onSkip={mode === 'socratic' ? handleSkipQuestion : undefined}
                onRequestHint={mode === 'socratic' ? handleRequestHint : undefined}
                onRequestSuggestions={mode === 'socratic' ? handleRequestSuggestions : undefined}
                isLoading={chatLoading}
                minLength={1}
                maxLength={5000}
                placeholder={mode === 'socratic' ? 'Type your response...' : 'Ask your question...'}
              />
            </div>
          </>
        )}
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
                    {summaryData.key_points.map((point) => (
                      <li
                        key={`kp-${point.substring(0, 30).replace(/\s/g, '-')}`}
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

      {/* Conflict Resolution Modal */}
      <ConflictResolutionModal
        conflicts={conflicts || []}
        isOpen={pendingConflicts}
        onResolve={async (resolution) => {
          if (selectedProjectId) {
            try {
              await resolveConflict(selectedProjectId, resolution);
            } catch (error) {
              console.error('Failed to resolve conflict:', error);
            }
          }
        }}
        onClose={() => {
          clearConflicts();
        }}
        isLoading={chatLoading}
      />

      {/* Hint Modal */}
      <HintDisplay
        isOpen={showHint}
        onClose={() => setShowHint(false)}
        hint="Check the project context for hints"
        questionNumber={1}
      />

      {/* Answer Suggestions Modal */}
      <AnswerSuggestionsModal
        isOpen={showSuggestions}
        onClose={() => setShowSuggestions(false)}
        suggestions={suggestions}
        question={suggestionsQuestion}
        phase={selectedProjectId ? 'current' : 'discovery'}
        onSelectSuggestion={(suggestion) => setResponse(suggestion)}
      />

      {/* Skipped Questions Panel */}
      {selectedProjectId && <SkippedQuestionsPanel projectId={selectedProjectId} />}

      {/* Debug Modal */}
      {showDebugModal && debugInfo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Debug Mode</h3>
                <button
                  onClick={() => setShowDebugModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              <div className="space-y-4">
                <div className="bg-gray-50 border border-gray-200 rounded p-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">Status:</p>
                  <p className={`text-lg font-bold ${debugInfo.debugEnabled ? 'text-green-600' : 'text-gray-600'}`}>
                    {debugInfo.debugEnabled ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div className="text-sm text-gray-600">
                  <p className="font-medium mb-1">When enabled:</p>
                  <ul className="space-y-1 ml-4">
                    <li>• Detailed logs printed to console</li>
                    <li>• Full request/response details</li>
                    <li>• Performance metrics</li>
                  </ul>
                </div>
              </div>
              <div className="mt-6 flex gap-2">
                <button
                  onClick={() => setShowDebugModal(false)}
                  className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Testing Mode Modal */}
      {showTestingModeModal && testingModeStatus && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Testing Mode</h3>
                <button
                  onClick={() => setShowTestingModeModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              <div className="space-y-4">
                <div className={`border rounded-lg p-4 ${testingModeStatus.enabled ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'}`}>
                  <p className="text-sm font-medium text-gray-700 mb-2">Status:</p>
                  <p className={`text-lg font-bold ${testingModeStatus.enabled ? 'text-blue-600' : 'text-gray-600'}`}>
                    {testingModeStatus.enabled ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
                  <p className="text-sm text-yellow-800">{testingModeStatus.message}</p>
                </div>
                {testingModeStatus.enabled && (
                  <div className="text-sm text-gray-600">
                    <p className="font-medium mb-1">Testing mode grants:</p>
                    <ul className="space-y-1 ml-4">
                      <li>• Unlimited projects</li>
                      <li>• Unlimited team members</li>
                      <li>• All LLM models available</li>
                      <li>• All premium features</li>
                    </ul>
                  </div>
                )}
              </div>
              <div className="mt-6 flex gap-2">
                <button
                  onClick={() => setShowTestingModeModal(false)}
                  className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Search Modal */}
      {showSearchModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Search Conversation
                </h3>
                <button
                  onClick={() => {
                    setShowSearchModal(false);
                    clearSearch();
                  }}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                {/* Search Input */}
                <div className="flex gap-2">
                  <Input
                    type="text"
                    placeholder="Search conversation..."
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handlePerformSearch();
                      }
                    }}
                    disabled={isSearchingModal}
                    className="flex-1"
                  />
                  <Button
                    onClick={handlePerformSearch}
                    disabled={isSearchingModal || !searchInput.trim()}
                    isLoading={isSearchingModal}
                  >
                    Search
                  </Button>
                </div>

                {/* Search Results */}
                {searchResults && searchResults.length > 0 ? (
                  <div className="space-y-3 border-t pt-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Found {searchResults.length} result{searchResults.length !== 1 ? 's' : ''}
                    </p>
                    {searchResults.map((result: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                      >
                        <p className="text-sm font-medium text-gray-900 dark:text-white mb-1">
                          {result.role === 'assistant' ? '🤖 Assistant' : '👤 You'}
                        </p>
                        <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-3">
                          {result.content}
                        </p>
                        {result.timestamp && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                            {new Date(result.timestamp).toLocaleString()}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : isSearchingModal ? (
                  <div className="text-center py-8">
                    <p className="text-gray-600 dark:text-gray-400">Searching...</p>
                  </div>
                ) : searchQuery && searchResults?.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-600 dark:text-gray-400">No results found</p>
                  </div>
                ) : null}
              </div>

              <div className="mt-6 flex gap-2 justify-end">
                <button
                  onClick={() => {
                    setShowSearchModal(false);
                    clearSearch();
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  Close
                </button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </MainLayout>
  );
};
