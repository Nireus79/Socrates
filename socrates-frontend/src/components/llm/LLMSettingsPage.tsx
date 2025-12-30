/**
 * LLM Settings Page - Configure LLM providers and models
 *
 * Features:
 * - Provider list and status
 * - API key management
 * - Model selection per provider
 * - Usage statistics
 */

import React from 'react';
import {
  Settings,
  Key,
  Zap,
  Check,
  AlertCircle,
  Loader,
  Eye,
  EyeOff,
} from 'lucide-react';
import { useLLMStore } from '../../stores';
import { Button } from '../common';
import { Input } from '../common';
import { Card } from '../common';
import { Alert } from '../common';
import { LLMProviderCard } from './LLMProviderCard';
import { APIKeyManager } from './APIKeyManager';
import { LLMUsageChart } from './LLMUsageChart';

export const LLMSettingsPage: React.FC = () => {
  const {
    providers,
    config,
    usageStats,
    isLoading,
    error,
    listProviders,
    getConfig,
    getUsageStats,
    clearError,
  } = useLLMStore();

  // Load data on mount
  React.useEffect(() => {
    Promise.all([
      listProviders().catch(console.error),
      getConfig().catch(console.error),
      getUsageStats().catch(console.error),
    ]);
  }, [listProviders, getConfig, getUsageStats]);

  const providersList = Array.from(providers.values());

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Zap className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            LLM Providers
          </h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          Configure language model providers and manage API keys
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert type="error" closeable onClose={clearError}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && !config && (
        <Card className="text-center py-12">
          <Loader className="h-8 w-8 text-blue-600 dark:text-blue-400 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600 dark:text-gray-400">Loading providers...</p>
        </Card>
      )}

      {/* Current Configuration */}
      {config && !isLoading && (
        <Card>
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Current Configuration
            </h2>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Default Provider
                </label>
                <div className="px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-md text-sm font-semibold text-gray-900 dark:text-white">
                  {config.default_provider}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Default Model
                </label>
                <div className="px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-md text-sm font-semibold text-gray-900 dark:text-white">
                  {config.default_model}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Temperature
                </label>
                <div className="px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-md text-sm">
                  {config.temperature}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Max Tokens
                </label>
                <div className="px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-md text-sm">
                  {config.max_tokens ? config.max_tokens.toLocaleString() : 'N/A'}
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Usage Statistics */}
      {usageStats && !isLoading && (
        <LLMUsageChart stats={usageStats} />
      )}

      {/* Providers Grid */}
      {!isLoading && providersList.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Available Providers
          </h2>

          <div className="grid gap-4">
            {providersList.map((provider) => (
              <div key={provider.name}>
                <LLMProviderCard provider={provider} />
                <APIKeyManager provider={provider.name} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Box */}
      <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <div className="space-y-2">
          <h3 className="font-semibold text-blue-900 dark:text-blue-200 flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Tips
          </h3>
          <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1 ml-7">
            <li>• Set API keys to enable providers for code generation</li>
            <li>• The default provider is used when generating code</li>
            <li>• You can switch providers at any time</li>
            <li>• Usage statistics help track API costs</li>
          </ul>
        </div>
      </Card>
    </div>
  );
};
