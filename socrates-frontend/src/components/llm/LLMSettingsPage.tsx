/**
 * LLM Settings Page - Configure LLM providers and models
 *
 * Features:
 * - Multi-LLM provider management
 * - Provider grid with subscription vs API designation
 * - Enable/disable providers
 * - Model selection per provider
 * - Pricing comparison
 * - API key management
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
  CreditCard,
  Plug,
  ToggleLeft,
  ToggleRight,
  DollarSign,
  Cpu,
} from 'lucide-react';
import { useLLMStore } from '../../stores';
import { Button } from '../common';
import { Input } from '../common';
import { Card } from '../common';
import { Alert } from '../common';
import { Badge } from '../common';
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
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Zap className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Language Model Providers
          </h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          Manage multiple LLM providers, select models, and configure your preferred options
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

      {/* Current Configuration Summary */}
      {config && !isLoading && (
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800">
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Current Configuration
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-2">
                  Default Provider
                </p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {config.default_provider}
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-2">
                  Default Model
                </p>
                <p className="text-sm text-gray-900 dark:text-white font-mono truncate">
                  {config.default_model}
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-2">
                  Temperature
                </p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {config.temperature}
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-2">
                  Max Tokens
                </p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {config.max_tokens ? config.max_tokens.toLocaleString() : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Usage Statistics */}
      {usageStats && !isLoading && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Usage & Costs
          </h2>
          <LLMUsageChart stats={usageStats} />
        </div>
      )}

      {/* Charge Type Legend */}
      <Card className="bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-800">
        <div className="flex flex-wrap gap-6">
          <div className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            <span className="text-sm text-amber-800 dark:text-amber-200">
              <span className="font-semibold">API-Based:</span> Requires API key to use
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Plug className="h-5 w-5 text-green-600 dark:text-green-400" />
            <span className="text-sm text-green-800 dark:text-green-200">
              <span className="font-semibold">Subscription:</span> Built-in, no API key needed
            </span>
          </div>
        </div>
      </Card>

      {/* Multi-LLM Provider Grid */}
      {!isLoading && providersList.length > 0 && (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
              Available Providers
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Choose which LLMs you want to use and configure their models
            </p>
          </div>

          {/* Provider Cards */}
          <div className="grid gap-4">
            {providersList.map((provider) => (
              <Card
                key={provider.name}
                className={`transition-all ${
                  provider.is_configured
                    ? 'border-green-300 dark:border-green-700'
                    : 'border-gray-200 dark:border-gray-700'
                }`}
              >
                <div className="space-y-4">
                  {/* Provider Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                          {provider.label}
                        </h3>
                        {provider.is_configured && (
                          <Badge variant="success">
                            <Check className="h-3 w-3 mr-1" />
                            Configured
                          </Badge>
                        )}
                        {!provider.is_configured && (
                          <Badge variant="warning">
                            Not Configured
                          </Badge>
                        )}
                        <Badge
                          variant={
                            provider.models && provider.models[0]?.includes('api')
                              ? 'info'
                              : 'secondary'
                          }
                        >
                          {provider.is_configured === undefined ||
                          (Array.isArray(provider.models) &&
                            provider.models[0]?.includes('openai')) ||
                          provider.name === 'openai' ||
                          provider.name === 'gemini' ? (
                            <>
                              <CreditCard className="h-3 w-3 mr-1" />
                              API-Based
                            </>
                          ) : (
                            <>
                              <Plug className="h-3 w-3 mr-1" />
                              Subscription
                            </>
                          )}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                        {provider.models && provider.models.length > 0
                          ? `${provider.models.length} model${
                              provider.models.length !== 1 ? 's' : ''
                            } available`
                          : 'No models available'}
                      </p>
                    </div>
                  </div>

                  {/* API Key Management Section */}
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                    <APIKeyManager provider={provider.name} />
                  </div>

                  {/* Provider Details and Model Selection */}
                  {provider.is_configured && (
                    <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                      <LLMProviderCard provider={provider} />
                    </div>
                  )}

                  {/* Not Configured Message */}
                  {!provider.is_configured && (
                    <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3 text-sm text-amber-800 dark:text-amber-200">
                      <AlertCircle className="h-4 w-4 inline mr-2" />
                      Add an API key above to enable this provider and select models
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Tips and Information */}
      <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <div className="space-y-3">
          <h3 className="font-semibold text-blue-900 dark:text-blue-200 flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Quick Guide
          </h3>
          <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-2 ml-7">
            <li>
              <span className="font-medium">API-Based Providers:</span> You need to provide your own API key (OpenAI, Google Gemini, etc.)
            </li>
            <li>
              <span className="font-medium">Subscription Providers:</span> These providers are managed through your account (Claude, Ollama)
            </li>
            <li>
              <span className="font-medium">Default Provider:</span> The primary provider used when generating code
            </li>
            <li>
              <span className="font-medium">Model Selection:</span> Choose which model variant to use for each provider
            </li>
            <li>
              <span className="font-medium">Cost Tracking:</span> Monitor your usage and costs above
            </li>
          </ul>
        </div>
      </Card>
    </div>
  );
};
