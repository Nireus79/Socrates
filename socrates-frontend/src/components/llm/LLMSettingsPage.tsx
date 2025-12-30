/**
 * LLM Settings Page - Complete Multi-Provider Management
 *
 * Full-featured interface for managing multiple language model providers:
 * - 4 providers (Claude, OpenAI, Gemini, Ollama)
 * - API key management (add/update/remove)
 * - Model selection for each provider
 * - Set default provider
 * - Usage & cost tracking
 * - Provider comparison
 */

import React, { useState } from 'react';
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
  Plus,
  Trash2,
  Save,
  X,
  DollarSign,
} from 'lucide-react';
import { useLLMStore } from '../../stores';
import { Button } from '../common';
import { Card } from '../common';
import { Alert } from '../common';
import { Badge } from '../common';
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
    setDefaultProvider,
    setProviderModel,
    addAPIKey,
    removeAPIKey,
    clearError,
  } = useLLMStore();

  const [expandedProvider, setExpandedProvider] = useState<string | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState<{ [key: string]: string }>({});
  const [showApiKey, setShowApiKey] = useState<{ [key: string]: boolean }>({});
  const [selectedModels, setSelectedModels] = useState<{ [key: string]: string }>({});
  const [isSaving, setIsSaving] = useState(false);
  const [savingProvider, setSavingProvider] = useState<string | null>(null);

  // Load data on mount
  React.useEffect(() => {
    Promise.all([
      listProviders().catch(console.error),
      getConfig().catch(console.error),
      getUsageStats().catch(console.error),
    ]);
  }, [listProviders, getConfig, getUsageStats]);

  const providersList = Array.from(providers.values());

  const handleAddApiKey = async (providerName: string) => {
    const key = apiKeyInput[providerName]?.trim();
    if (!key) {
      alert('Please enter an API key');
      return;
    }
    setSavingProvider(providerName);
    try {
      await addAPIKey(providerName, key);
      setApiKeyInput({ ...apiKeyInput, [providerName]: '' });
    } catch (err) {
      console.error('Error adding API key:', err);
    } finally {
      setSavingProvider(null);
    }
  };

  const handleRemoveApiKey = async (providerName: string) => {
    if (!window.confirm(`Remove API key for ${providerName}?`)) return;
    setSavingProvider(providerName);
    try {
      await removeAPIKey(providerName);
    } catch (err) {
      console.error('Error removing API key:', err);
    } finally {
      setSavingProvider(null);
    }
  };

  const handleSetAsDefault = async (providerName: string, model: string) => {
    setSavingProvider(providerName);
    try {
      await setDefaultProvider(providerName);
      await setProviderModel(providerName, model);
    } catch (err) {
      console.error('Error setting default:', err);
    } finally {
      setSavingProvider(null);
    }
  };

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
          Manage 4 LLM providers, add API keys, select models, and configure your preferences
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
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Current Configuration
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Default Provider</p>
              <p className="text-lg font-bold text-gray-900 dark:text-white">{config.default_provider}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Default Model</p>
              <p className="text-sm text-gray-900 dark:text-white font-mono">{config.default_model.split('-').slice(-1)[0]}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Temperature</p>
              <p className="text-lg font-bold text-gray-900 dark:text-white">{config.temperature}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Max Tokens</p>
              <p className="text-lg font-bold text-gray-900 dark:text-white">{config.max_tokens?.toLocaleString() || 'N/A'}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Usage & Costs */}
      {usageStats && !isLoading && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Usage & Costs</h2>
          <LLMUsageChart stats={usageStats} />
        </div>
      )}

      {/* Provider Type Legend */}
      <Card className="bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-800">
        <div className="space-y-3">
          <p className="font-semibold text-amber-900 dark:text-amber-100">Provider Types:</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start gap-3">
              <CreditCard className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-1" />
              <div>
                <p className="font-medium text-amber-900 dark:text-amber-100">API-Based</p>
                <p className="text-sm text-amber-800 dark:text-amber-200">Requires your own API key (OpenAI, Gemini)</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Plug className="h-5 w-5 text-green-600 dark:text-green-400 mt-1" />
              <div>
                <p className="font-medium text-green-900 dark:text-green-100">Built-in</p>
                <p className="text-sm text-green-800 dark:text-green-200">No API key needed (Claude, Ollama)</p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Providers Grid */}
      {!isLoading && providersList.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">All Providers (4)</h2>

          <div className="grid gap-6">
            {providersList.map((provider) => {
              const isApiRequired = provider.requires_api_key;
              const isConfigured = provider.is_configured || (!isApiRequired && provider.models?.length > 0);
              const isDefault = config?.default_provider === provider.name;
              const selectedModel = selectedModels[provider.name] || provider.models?.[0] || '';
              const isExpanded = expandedProvider === provider.name;

              return (
                <Card
                  key={provider.name}
                  className={`transition-all ${
                    isDefault
                      ? 'border-green-400 dark:border-green-600 bg-green-50/40 dark:bg-green-900/15'
                      : 'border-gray-300 dark:border-gray-600'
                  }`}
                >
                  <div className="space-y-4">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                          <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                            {provider.label}
                          </h3>
                          {isDefault && (
                            <Badge variant="success">
                              <Check className="h-3 w-3 mr-1" /> Default
                            </Badge>
                          )}
                          {isConfigured && (
                            <Badge variant="success">
                              <Check className="h-3 w-3 mr-1" /> Active
                            </Badge>
                          )}
                          <Badge variant={isApiRequired ? 'info' : 'secondary'}>
                            {isApiRequired ? (
                              <>
                                <CreditCard className="h-3 w-3 mr-1" /> API-Based
                              </>
                            ) : (
                              <>
                                <Plug className="h-3 w-3 mr-1" /> Built-in
                              </>
                            )}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {provider.description || 'Language model provider'}
                        </p>
                        {provider.context_window && (
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                            {provider.models?.length || 0} models • {provider.context_window.toLocaleString()} token context
                          </p>
                        )}
                      </div>
                      <button
                        onClick={() => setExpandedProvider(isExpanded ? null : provider.name)}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
                      >
                        {isExpanded ? (
                          <X className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                        ) : (
                          <Plus className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                        )}
                      </button>
                    </div>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <>
                        {/* API Key Section (for API-based providers) */}
                        {isApiRequired && (
                          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">API Key</h4>
                            {!isConfigured ? (
                              <div className="space-y-2">
                                <div className="relative">
                                  <input
                                    type={showApiKey[provider.name] ? 'text' : 'password'}
                                    placeholder="Paste your API key here"
                                    value={apiKeyInput[provider.name] || ''}
                                    onChange={(e) =>
                                      setApiKeyInput({
                                        ...apiKeyInput,
                                        [provider.name]: e.target.value,
                                      })
                                    }
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
                                  />
                                  <button
                                    onClick={() =>
                                      setShowApiKey({
                                        ...showApiKey,
                                        [provider.name]: !showApiKey[provider.name],
                                      })
                                    }
                                    className="absolute right-3 top-2.5 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                                  >
                                    {showApiKey[provider.name] ? (
                                      <EyeOff className="h-4 w-4" />
                                    ) : (
                                      <Eye className="h-4 w-4" />
                                    )}
                                  </button>
                                </div>
                                <Button
                                  variant="primary"
                                  fullWidth
                                  onClick={() => handleAddApiKey(provider.name)}
                                  disabled={savingProvider === provider.name}
                                  icon={<Save className="h-4 w-4" />}
                                >
                                  {savingProvider === provider.name ? 'Saving...' : 'Save API Key'}
                                </Button>
                              </div>
                            ) : (
                              <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                                <span className="text-sm text-green-700 dark:text-green-300">
                                  <Check className="h-4 w-4 inline mr-2" />
                                  API Key Configured
                                </span>
                                <Button
                                  variant="secondary"
                                  size="sm"
                                  onClick={() => handleRemoveApiKey(provider.name)}
                                  disabled={savingProvider === provider.name}
                                  icon={<Trash2 className="h-4 w-4" />}
                                  className="text-red-600 hover:text-red-700"
                                >
                                  Remove
                                </Button>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Model Selection */}
                        {isConfigured && provider.models && provider.models.length > 0 && (
                          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Select Model</h4>
                            <select
                              value={selectedModel}
                              onChange={(e) =>
                                setSelectedModels({
                                  ...selectedModels,
                                  [provider.name]: e.target.value,
                                })
                              }
                              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                              {provider.models.map((model) => (
                                <option key={model} value={model}>
                                  {model}
                                </option>
                              ))}
                            </select>
                          </div>
                        )}

                        {/* Pricing */}
                        {provider.cost_per_1k_input_tokens !== undefined && (
                          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                            <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                              <DollarSign className="h-4 w-4" />
                              Pricing
                            </h4>
                            {provider.cost_per_1k_input_tokens === 0 ? (
                              <p className="text-sm text-green-700 dark:text-green-300 font-medium">FREE (Local)</p>
                            ) : (
                              <div className="space-y-1 text-sm">
                                <p className="text-gray-600 dark:text-gray-400">
                                  Input: ${(provider.cost_per_1k_input_tokens * 1000).toFixed(4)}/1M tokens
                                </p>
                                <p className="text-gray-600 dark:text-gray-400">
                                  Output: ${(provider.cost_per_1k_output_tokens * 1000).toFixed(4)}/1M tokens
                                </p>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Action Buttons */}
                        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 flex gap-2">
                          {isConfigured && selectedModel && !isDefault && (
                            <Button
                              variant="primary"
                              fullWidth
                              onClick={() => handleSetAsDefault(provider.name, selectedModel)}
                              disabled={savingProvider === provider.name}
                            >
                              {savingProvider === provider.name ? 'Setting...' : 'Set as Default'}
                            </Button>
                          )}
                          {isDefault && (
                            <div className="flex-1 text-center py-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                              <p className="text-sm font-semibold text-green-700 dark:text-green-300">
                                ✓ Currently Using
                              </p>
                            </div>
                          )}
                          {!isConfigured && isApiRequired && (
                            <div className="flex-1 text-center py-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                              <p className="text-sm font-semibold text-amber-700 dark:text-amber-300">
                                Add API Key Above
                              </p>
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Help Section */}
      <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-3 flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          How to Use
        </h3>
        <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-300">
          <li>
            <strong>Claude:</strong> Built-in, click expand to see models and set as default
          </li>
          <li>
            <strong>OpenAI:</strong> Expand, paste your API key, select model, set as default
          </li>
          <li>
            <strong>Gemini:</strong> Expand, paste your API key, select model, set as default
          </li>
          <li>
            <strong>Ollama:</strong> Built-in (requires Ollama running on localhost:11434), select model and set as default
          </li>
          <li>
            <strong>Usage:</strong> Track your costs by provider in the Usage & Costs section above
          </li>
        </ul>
      </Card>
    </div>
  );
};
