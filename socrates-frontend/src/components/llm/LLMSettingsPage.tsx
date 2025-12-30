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
            {providersList.map((provider) => {
              const isApiRequired = provider.requires_api_key;
              const isConfigured =
                provider.is_configured ||
                (!isApiRequired && provider.models && provider.models.length > 0);
              const isDefault = config?.default_provider === provider.name;

              return (
                <Card
                  key={provider.name}
                  className={`transition-all ${
                    isConfigured
                      ? 'border-green-300 dark:border-green-700 bg-green-50/30 dark:bg-green-900/10'
                      : 'border-gray-200 dark:border-gray-700'
                  }`}
                >
                  <div className="space-y-4">
                    {/* Provider Header with Controls */}
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2 flex-wrap">
                          <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                            {provider.label}
                          </h3>

                          {isDefault && (
                            <Badge variant="success">
                              <Check className="h-3 w-3 mr-1" />
                              Default
                            </Badge>
                          )}

                          {provider.is_configured && !isApiRequired && (
                            <Badge variant="success">
                              <Check className="h-3 w-3 mr-1" />
                              Ready
                            </Badge>
                          )}

                          {provider.is_configured && isApiRequired && (
                            <Badge variant="success">
                              <Check className="h-3 w-3 mr-1" />
                              Configured
                            </Badge>
                          )}

                          {!provider.is_configured && isApiRequired && (
                            <Badge variant="warning">
                              Needs Setup
                            </Badge>
                          )}

                          <Badge
                            variant={isApiRequired ? 'info' : 'secondary'}
                          >
                            {isApiRequired ? (
                              <>
                                <CreditCard className="h-3 w-3 mr-1" />
                                API-Based
                              </>
                            ) : (
                              <>
                                <Plug className="h-3 w-3 mr-1" />
                                Built-in
                              </>
                            )}
                          </Badge>
                        </div>

                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {provider.description || 'Language model provider'}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          {provider.models && provider.models.length > 0
                            ? `${provider.models.length} model${
                                provider.models.length !== 1 ? 's' : ''
                              } available • ${provider.context_window?.toLocaleString()} token context`
                            : 'No models available'}
                        </p>
                      </div>
                    </div>

                    {/* API Key Management (only for API-based providers) */}
                    {isApiRequired && (
                      <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                          API Key Configuration
                        </h4>
                        <APIKeyManager provider={provider.name} />
                      </div>
                    )}

                    {/* Model Selection and Provider Controls (always show) */}
                    <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                        Model & Settings
                      </h4>

                      {isConfigured ? (
                        <div className="space-y-3">
                          {/* Model Selection Dropdown */}
                          {provider.models && provider.models.length > 0 && (
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Select Model
                              </label>
                              <div className="relative">
                                <select
                                  defaultValue={provider.models[0]}
                                  onChange={(e) => {
                                    if (provider.name !== config?.default_provider) {
                                      // Automatically set as default when selecting model
                                      // This will be handled by clicking "Use This Provider" button
                                    }
                                  }}
                                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                  {provider.models.map((model) => (
                                    <option key={model} value={model}>
                                      {model}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            </div>
                          )}

                          {/* Action Buttons */}
                          <div className="flex gap-2 pt-2">
                            {!isDefault && (
                              <Button
                                variant="primary"
                                fullWidth
                                onClick={() => {
                                  const select = document.querySelector(
                                    `[name="model-${provider.name}"]`
                                  ) as HTMLSelectElement;
                                  const selectedModel = select?.value || provider.models?.[0];
                                  if (selectedModel) {
                                    // Call both setDefaultProvider and setProviderModel
                                    config?.default_provider &&
                                      config.default_provider !==
                                        provider.name &&
                                      (async () => {
                                        const { setDefaultProvider, setProviderModel } =
                                          useLLMStore.getState();
                                        await setDefaultProvider(provider.name).catch(
                                          console.error
                                        );
                                        await setProviderModel(
                                          provider.name,
                                          selectedModel
                                        ).catch(console.error);
                                      })();
                                  }
                                }}
                              >
                                Use This Provider
                              </Button>
                            )}

                            {isDefault && (
                              <div className="flex-1 text-center py-2 bg-green-50 dark:bg-green-900/20 rounded-md">
                                <p className="text-sm font-semibold text-green-700 dark:text-green-300">
                                  ✓ Currently Active
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 space-y-3">
                          <p className="text-sm text-amber-800 dark:text-amber-200">
                            <AlertCircle className="h-4 w-4 inline mr-2" />
                            {isApiRequired
                              ? 'Add an API key above to enable this provider'
                              : 'This provider requires setup'}
                          </p>
                          {isApiRequired && (
                            <div className="text-xs text-amber-700 dark:text-amber-300">
                              Once you add your API key, you'll be able to select models
                              and set this as your default provider.
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Provider Info */}
                    {provider.cost_per_1k_input_tokens && (
                      <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          <span className="font-medium">Estimated Cost:</span> $
                          {(provider.cost_per_1k_input_tokens * 1000).toFixed(4)}/1M input tokens
                          • ${(provider.cost_per_1k_output_tokens * 1000).toFixed(4)}/1M output tokens
                        </p>
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}
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
