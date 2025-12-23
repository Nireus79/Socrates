/**
 * API Key Manager - Manage API keys for LLM providers
 *
 * Features:
 * - Add/update API key
 * - Show/hide API key
 * - Remove API key
 */

import React from 'react';
import { Eye, EyeOff, Trash2, Save, Plus } from 'lucide-react';
import { useLLMStore } from '../../stores';
import { Button } from '../common';
import { Input } from '../common';
import { Card } from '../common';
import { Alert } from '../common';

interface APIKeyManagerProps {
  provider: string;
}

export const APIKeyManager: React.FC<APIKeyManagerProps> = ({ provider }) => {
  const { addAPIKey, removeAPIKey, isSaving, error } = useLLMStore();

  const [apiKey, setApiKey] = React.useState('');
  const [showKey, setShowKey] = React.useState(false);
  const [hasKey, setHasKey] = React.useState(false);
  const [isEditing, setIsEditing] = React.useState(false);
  const [validationError, setValidationError] = React.useState<string | null>(null);

  const handleAddKey = async () => {
    setValidationError(null);

    if (!apiKey.trim()) {
      setValidationError('API key is required');
      return;
    }

    if (apiKey.length < 10) {
      setValidationError('API key must be at least 10 characters');
      return;
    }

    try {
      await addAPIKey(provider, apiKey);
      setApiKey('');
      setIsEditing(false);
      setHasKey(true);
    } catch (err) {
      console.error('Failed to add API key:', err);
    }
  };

  const handleRemoveKey = async () => {
    if (
      window.confirm(
        `Are you sure you want to remove the API key for ${provider}? The provider will be disabled.`
      )
    ) {
      try {
        await removeAPIKey(provider);
        setApiKey('');
        setIsEditing(false);
        setHasKey(false);
      } catch (err) {
        console.error('Failed to remove API key:', err);
      }
    }
  };

  return (
    <Card className="bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 mt-3">
      <div className="space-y-3">
        {/* Error Alert */}
        {(validationError || error) && (
          <Alert type="error" closeable onClose={() => setValidationError(null)}>
            {validationError || error}
          </Alert>
        )}

        {/* Header */}
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900 dark:text-white flex items-center gap-2">
            API Key
          </h4>
          {hasKey && !isEditing && (
            <span className="text-xs text-green-600 dark:text-green-400">
              ✓ Added
            </span>
          )}
        </div>

        {/* Key Input */}
        {isEditing ? (
          <div className="space-y-2">
            <div className="relative">
              <Input
                type={showKey ? 'text' : 'password'}
                placeholder="Paste your API key here"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                disabled={isSaving}
                icon={
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    {showKey ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                }
              />
            </div>

            <div className="flex gap-2">
              <Button
                variant="primary"
                size="sm"
                fullWidth
                icon={<Save className="h-4 w-4" />}
                onClick={handleAddKey}
                disabled={isSaving}
                isLoading={isSaving}
              >
                Save Key
              </Button>
              <Button
                variant="secondary"
                size="sm"
                fullWidth
                onClick={() => {
                  setIsEditing(false);
                  setApiKey('');
                  setValidationError(null);
                }}
                disabled={isSaving}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex gap-2">
            {hasKey ? (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  fullWidth
                  onClick={() => setIsEditing(true)}
                >
                  Update Key
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<Trash2 className="h-4 w-4" />}
                  onClick={handleRemoveKey}
                  className="text-red-600 hover:text-red-700 dark:text-red-400"
                >
                  Remove
                </Button>
              </>
            ) : (
              <Button
                variant="secondary"
                size="sm"
                fullWidth
                icon={<Plus className="h-4 w-4" />}
                onClick={() => setIsEditing(true)}
              >
                Add API Key
              </Button>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};
