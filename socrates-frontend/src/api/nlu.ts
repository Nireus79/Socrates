/**
 * NLU (Natural Language Understanding) API client
 *
 * Provides methods for interpreting natural language input and getting command suggestions.
 * Used for pre-session chat, command discovery, and natural interaction.
 */

import { apiClient } from './client';

// Type definitions for NLU API

export interface CommandSuggestion {
  command: string;
  confidence: number;
  reasoning: string;
  args?: string[];
}

export interface NLUInterpretRequest {
  input: string;
  context?: Record<string, any>;
}

export interface NLUInterpretResponse {
  status: 'success' | 'suggestions' | 'no_match' | 'error';
  command?: string;
  suggestions?: CommandSuggestion[];
  message: string;
}

export interface CommandInfo {
  name: string;
  usage: string;
  description: string;
  aliases: string[];
}

export interface AvailableCommandsResponse {
  commands: Record<string, CommandInfo[]>;
}

/**
 * NLU API methods for natural language interpretation
 */
export const nluAPI = {
  /**
   * Interpret natural language input and get command suggestions
   *
   * @param input - Natural language input to interpret
   * @param context - Optional context (project_id, user info, etc.)
   * @returns Promise with interpretation result
   *
   * Example:
   * ```
   * const result = await nluAPI.interpret('Show me the project analysis');
   * if (result.status === 'success') {
   *   executeCommand(result.command);
   * } else if (result.status === 'suggestions') {
   *   showSuggestions(result.suggestions);
   * }
   * ```
   */
  async interpret(input: string, context?: Record<string, any>) {
    try {
      const response = await apiClient.post<any>(
        '/nlu/interpret',
        {
          input,
          context,
        } as NLUInterpretRequest
      );

      // apiClient.post returns SuccessResponse which has data field containing NLU result
      const nluResult = response.data;

      if (!nluResult || !nluResult.status) {
        console.error('Invalid NLU response structure:', response);
        return {
          status: 'error' as const,
          message: 'Failed to interpret your input. Please try rephrasing.',
        };
      }

      return nluResult as NLUInterpretResponse;
    } catch (error) {
      console.error('NLU interpretation failed:', error);
      return {
        status: 'error' as const,
        message: 'Failed to interpret your input. Please try rephrasing.',
      };
    }
  },

  /**
   * Get list of available commands organized by category
   *
   * Useful for command discovery and help functionality.
   *
   * @returns Promise with available commands grouped by category
   *
   * Example:
   * ```
   * const commands = await nluAPI.getAvailableCommands();
   * // commands = {
   * //   "system": [
   * //     { name: "help", usage: "help", description: "...", aliases: [] }
   * //   ],
   * //   "project": [
   * //     { name: "project create", usage: "project create [name]", ... }
   * //   ]
   * // }
   * ```
   */
  async getAvailableCommands() {
    try {
      const response = await apiClient.get<any>(
        '/nlu/commands'
      );

      // apiClient.get returns SuccessResponse which has data field containing commands
      const commandsData = response.data;
      return commandsData?.commands || {};
    } catch (error) {
      console.error('Failed to fetch available commands:', error);
      return {};
    }
  },
};
