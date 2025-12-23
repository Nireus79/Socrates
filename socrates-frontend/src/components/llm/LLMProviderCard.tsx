/**
 * LLM Provider Card - Display provider information and model selection
 *
 * Shows:
 * - Provider name and status
 * - Available models
 * - Model selector
 */

import React from 'react';
import { Check, AlertCircle, ChevronDown } from 'lucide-react';
import type { LLMProvider } from '../../api/llm';
import { useLLMStore } from '../../stores';
import { Card } from '../common';
import { Button } from '../common';
import { Badge } from '../common';

interface LLMProviderCardProps {
  provider: LLMProvider;
}

export const LLMProviderCard: React.FC<LLMProviderCardProps> = ({ provider }) => {
  const {
    config,
    setDefaultProvider,
    setProviderModel,
    listProviderModels,
    models,
    isSaving,
  } = useLLMStore();

  const [expanded, setExpanded] = React.useState(false);
  const [selectedModel, setSelectedModel] = React.useState<string>(
    provider.models[0]
  );

  // Load models when provider is expanded
  React.useEffect(() => {
    if (expanded && !models.has(provider.name)) {
      listProviderModels(provider.name).catch(console.error);
    }
  }, [expanded, provider.name, models, listProviderModels]);

  const handleSetDefault = async () => {
    try {
      await setDefaultProvider(provider.name);
    } catch (err) {
      console.error('Failed to set default provider:', err);
    }
  };

  const handleSetModel = async () => {
    try {
      await setProviderModel(provider.name, selectedModel);
    } catch (err) {
      console.error('Failed to set model:', err);
    }
  };

  const isDefault = config?.default_provider === provider.name;
  const providerModels = models.get(provider.name) || [];

  return (
    <Card>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {provider.label}
              </h3>
              {isDefault && (
                <Badge variant="success">
                  <span className="flex items-center gap-1">
                    <Check className="h-3 w-3" /> Default
                  </span>
                </Badge>
              )}
              {provider.is_configured ? (
                <Badge variant="success">
                  <span className="flex items-center gap-1">
                    <Check className="h-3 w-3" /> Configured
                  </span>
                </Badge>
              ) : (
                <Badge variant="warning">
                  <span className="flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" /> Not Configured
                  </span>
                </Badge>
              )}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {provider.models.length} model{provider.models.length !== 1 ? 's' : ''}{' '}
              available
            </p>
          </div>

          {provider.is_configured && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              icon={<ChevronDown className={`h-4 w-4 transition-transform ${expanded ? 'rotate-180' : ''}`} />}
            >
              {expanded ? 'Hide' : 'Show'}
            </Button>
          )}
        </div>

        {/* Set as Default */}
        {!isDefault && provider.is_configured && (
          <Button
            variant="secondary"
            fullWidth
            onClick={handleSetDefault}
            disabled={isSaving}
          >
            Set as Default Provider
          </Button>
        )}

        {/* Model Selection */}
        {expanded && providerModels.length > 0 && (
          <div className="space-y-3 border-t border-gray-200 dark:border-gray-700 pt-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
                Select Model
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm"
              >
                {providerModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.context.toLocaleString()} tokens)
                  </option>
                ))}
              </select>
            </div>

            {selectedModel !== config?.default_model && (
              <Button
                variant="primary"
                fullWidth
                onClick={handleSetModel}
                disabled={isSaving}
              >
                Select This Model
              </Button>
            )}

            {selectedModel === config?.default_model && (
              <div className="text-center text-sm text-green-600 dark:text-green-400 py-2">
                ✓ Currently selected
              </div>
            )}
          </div>
        )}

        {/* Not Configured Message */}
        {!provider.is_configured && (
          <div className="text-sm text-gray-600 dark:text-gray-400 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
            API key required to enable this provider
          </div>
        )}
      </div>
    </Card>
  );
};
