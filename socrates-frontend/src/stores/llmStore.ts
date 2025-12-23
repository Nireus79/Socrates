/**
 * LLM Provider Store - Zustand state management
 *
 * Manages:
 * - Provider list and configuration
 * - Model selection per provider
 * - API key management
 * - Usage statistics
 */

import { create } from 'zustand';
import { llmAPI } from '../api/llm';
import type {
  LLMProvider,
  LLMConfig,
  LLMModel,
  UsageStats,
} from '../api/llm';

interface LLMState {
  // State
  providers: Map<string, LLMProvider>;
  models: Map<string, LLMModel[]>;
  config: LLMConfig | null;
  usageStats: UsageStats | null;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;

  // Actions
  listProviders: () => Promise<void>;
  getConfig: () => Promise<void>;
  setDefaultProvider: (provider: string) => Promise<void>;
  setProviderModel: (provider: string, model: string) => Promise<void>;
  addAPIKey: (provider: string, apiKey: string) => Promise<void>;
  removeAPIKey: (provider: string) => Promise<void>;
  listProviderModels: (provider: string) => Promise<void>;
  getUsageStats: (timePeriod?: string) => Promise<void>;
  clearError: () => void;
}

export const useLLMStore = create<LLMState>((set, get) => ({
  // Initial state
  providers: new Map(),
  models: new Map(),
  config: null,
  usageStats: null,
  isLoading: false,
  isSaving: false,
  error: null,

  /**
   * List all available LLM providers
   */
  listProviders: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await llmAPI.listProviders();
      const providersMap = new Map<string, LLMProvider>();

      response.providers.forEach((provider) => {
        providersMap.set(provider.name, provider);
      });

      set({ providers: providersMap, isLoading: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to list providers';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  /**
   * Get current LLM configuration
   */
  getConfig: async () => {
    set({ isLoading: true, error: null });
    try {
      const config = await llmAPI.getConfig();
      set({ config, isLoading: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to get configuration';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  /**
   * Set default LLM provider
   */
  setDefaultProvider: async (provider: string) => {
    set({ isSaving: true, error: null });
    try {
      await llmAPI.setDefaultProvider(provider);

      // Update config
      const config = get().config;
      if (config) {
        set({ config: { ...config, default_provider: provider } });
      }

      set({ isSaving: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to set provider';
      set({ error: message, isSaving: false });
      throw err;
    }
  },

  /**
   * Set LLM model for provider
   */
  setProviderModel: async (provider: string, model: string) => {
    set({ isSaving: true, error: null });
    try {
      await llmAPI.setProviderModel(provider, model);

      // Update config
      const config = get().config;
      if (config && config.default_provider === provider) {
        set({ config: { ...config, default_model: model } });
      }

      set({ isSaving: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to set model';
      set({ error: message, isSaving: false });
      throw err;
    }
  },

  /**
   * Add or update API key for provider
   */
  addAPIKey: async (provider: string, apiKey: string) => {
    set({ isSaving: true, error: null });
    try {
      await llmAPI.addAPIKey(provider, apiKey);

      // Update provider configuration status
      const providers = new Map(get().providers);
      const providerData = providers.get(provider);
      if (providerData) {
        providers.set(provider, {
          ...providerData,
          is_configured: true,
        });
        set({ providers });
      }

      set({ isSaving: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to add API key';
      set({ error: message, isSaving: false });
      throw err;
    }
  },

  /**
   * Remove API key for provider
   */
  removeAPIKey: async (provider: string) => {
    set({ isSaving: true, error: null });
    try {
      await llmAPI.removeAPIKey(provider);

      // Update provider configuration status
      const providers = new Map(get().providers);
      const providerData = providers.get(provider);
      if (providerData) {
        providers.set(provider, {
          ...providerData,
          is_configured: false,
        });
        set({ providers });
      }

      set({ isSaving: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to remove API key';
      set({ error: message, isSaving: false });
      throw err;
    }
  },

  /**
   * List models for a provider
   */
  listProviderModels: async (provider: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await llmAPI.listProviderModels(provider);
      const models = new Map(get().models);
      models.set(provider, response.models);
      set({ models, isLoading: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to list models';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  /**
   * Get usage statistics
   */
  getUsageStats: async (timePeriod: string = 'month') => {
    set({ isLoading: true, error: null });
    try {
      const stats = await llmAPI.getUsageStats(timePeriod);
      set({ usageStats: stats, isLoading: false });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to get usage stats';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  /**
   * Clear error message
   */
  clearError: () => {
    set({ error: null });
  },
}));
