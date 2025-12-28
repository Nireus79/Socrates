/**
 * LLM Provider API client
 *
 * Provides centralized methods for LLM provider management:
 * - Provider configuration
 * - Model selection
 * - API key management
 * - Usage statistics
 */

import { apiClient } from './client';

// Type definitions for LLM API

export interface LLMProvider {
  name: string;
  label: string;
  models: string[];
  is_configured: boolean;
}

export interface LLMModel {
  id: string;
  name: string;
  context: number;
}

export interface LLMConfig {
  default_provider: string;
  default_model: string;
  temperature: number;
  max_tokens: number;
}

export interface UsageStats {
  total_requests: number;
  total_tokens: {
    input: number;
    output: number;
  };
  by_provider: Record<
    string,
    {
      requests: number;
      tokens: number;
      cost: number;
    }
  >;
  by_model: Record<string, any>;
  cost_summary: {
    estimated: number;
    period: string;
  };
}

export interface ListProvidersResponse {
  providers: LLMProvider[];
  total: number;
}

export interface ListModelsResponse {
  provider: string;
  models: LLMModel[];
  total: number;
}

/**
 * LLM Provider API client
 */
export const llmAPI = {
  /**
   * List all available LLM providers
   */
  async listProviders(): Promise<ListProvidersResponse> {
    const response = await apiClient.get<{ providers: LLMProvider[]; total: number }>(
      '/llm/providers'
    );
    return response;
  },

  /**
   * Get current LLM configuration
   */
  async getConfig(): Promise<LLMConfig> {
    const response = await apiClient.get<LLMConfig>('/llm/config');
    return response;
  },

  /**
   * Set default LLM provider
   */
  async setDefaultProvider(provider: string): Promise<{ provider: string }> {
    const params = new URLSearchParams();
    params.append('provider', provider);
    return apiClient.put<{ provider: string }>(
      `/llm/default-provider?${params.toString()}`,
      {}
    );
  },

  /**
   * Set LLM model for a provider
   */
  async setProviderModel(
    provider: string,
    model: string
  ): Promise<{ provider: string; model: string }> {
    const params = new URLSearchParams();
    params.append('provider', provider);
    params.append('model', model);
    return apiClient.put<{ provider: string; model: string }>(
      `/llm/model?${params.toString()}`,
      {}
    );
  },

  /**
   * Add or update API key for provider
   */
  async addAPIKey(provider: string, apiKey: string): Promise<{ provider: string; key_last_4: string }> {
    const params = new URLSearchParams();
    params.append('provider', provider);
    params.append('api_key', apiKey);
    return apiClient.post<{ provider: string; key_last_4: string }>(
      `/llm/api-key?${params.toString()}`,
      {}
    );
  },

  /**
   * Remove API key for provider
   */
  async removeAPIKey(provider: string): Promise<{ provider: string }> {
    return apiClient.delete<{ provider: string }>(`/llm/api-key/${provider}`);
  },

  /**
   * List models for a provider
   */
  async listProviderModels(provider: string): Promise<ListModelsResponse> {
    const response = await apiClient.get<ListModelsResponse>(`/llm/models/${provider}`);
    return response;
  },

  /**
   * Get usage statistics
   */
  async getUsageStats(timePeriod: string = 'month'): Promise<UsageStats> {
    const params = new URLSearchParams();
    params.append('time_period', timePeriod);
    return apiClient.get<UsageStats>(
      `/llm/usage-stats?${params.toString()}`
    );
  },
};
