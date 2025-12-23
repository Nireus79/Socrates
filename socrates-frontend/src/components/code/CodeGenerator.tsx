/**
 * CodeGenerator Component - Form to configure code generation
 */

import React from 'react';
import { Zap, Copy } from 'lucide-react';
import {
  Card,
  Select,
  TextArea,
  FormField,
  FormActions,
  Checkbox,
  Button,
} from '../common';

interface CodeGeneratorProps {
  onGenerate: (config: CodeGenerationConfig) => Promise<void>;
  isLoading?: boolean;
  defaultLanguage?: string;
}

export interface CodeGenerationConfig {
  language: string;
  prompt: string;
  includeComments: boolean;
  includeTests: boolean;
  includeErrorHandling: boolean;
  includeDocumentation: boolean;
}

const languages = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'java', label: 'Java' },
  { value: 'cpp', label: 'C++' },
  { value: 'csharp', label: 'C#' },
  { value: 'go', label: 'Go' },
  { value: 'rust', label: 'Rust' },
  { value: 'php', label: 'PHP' },
];

export const CodeGenerator: React.FC<CodeGeneratorProps> = ({
  onGenerate,
  isLoading = false,
  defaultLanguage = 'python',
}) => {
  const [config, setConfig] = React.useState<CodeGenerationConfig>({
    language: defaultLanguage,
    prompt: '',
    includeComments: true,
    includeTests: false,
    includeErrorHandling: true,
    includeDocumentation: true,
  });

  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const handleValidate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!config.prompt.trim()) {
      newErrors.prompt = 'Please describe what you want to generate';
    }
    if (config.prompt.trim().length < 10) {
      newErrors.prompt = 'Description should be at least 10 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (handleValidate()) {
      try {
        await onGenerate(config);
      } catch (error) {
        console.error('Code generation failed:', error);
      }
    }
  };

  const insertTemplate = (template: string) => {
    setConfig((prev) => ({
      ...prev,
      prompt: prev.prompt + (prev.prompt ? '\n\n' : '') + template,
    }));
  };

  return (
    <div className="space-y-4">
      {/* Language Selection */}
      <Card>
        <FormField label="Programming Language" required>
          <Select
            options={languages}
            value={config.language}
            onChange={(e) => setConfig((prev) => ({ ...prev, language: e.target.value }))}
            disabled={isLoading}
          />
        </FormField>
      </Card>

      {/* Code Specification */}
      <Card>
        <FormField
          label="Code Specification"
          required
          error={errors.prompt}
          help="Describe what code you want to generate"
        >
          <TextArea
            placeholder="E.g., 'Create a function that validates email addresses using regex, handles edge cases, and includes error handling'"
            value={config.prompt}
            onChange={(e) => {
              setConfig((prev) => ({ ...prev, prompt: e.target.value }));
              if (errors.prompt) {
                setErrors((prev) => {
                  const newErrors = { ...prev };
                  delete newErrors.prompt;
                  return newErrors;
                });
              }
            }}
            rows={5}
            disabled={isLoading}
          />
        </FormField>

        {/* Quick Templates */}
        <div className="mt-3 space-y-2">
          <p className="text-xs font-medium text-gray-600 dark:text-gray-400">
            Quick Templates:
          </p>
          <div className="flex gap-2 flex-wrap">
            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                insertTemplate(
                  'Create a REST API endpoint with proper HTTP methods, validation, and error handling'
                )
              }
              disabled={isLoading}
            >
              + API
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                insertTemplate(
                  'Implement a data structure/class with getter/setter methods and validation'
                )
              }
              disabled={isLoading}
            >
              + Class
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                insertTemplate(
                  'Write unit tests covering happy path and edge cases'
                )
              }
              disabled={isLoading}
            >
              + Tests
            </Button>
          </div>
        </div>
      </Card>

      {/* Options */}
      <Card>
        <div className="space-y-3">
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            Code Options
          </p>

          <Checkbox
            label="Include Comments"
            checked={config.includeComments}
            onChange={(e) =>
              setConfig((prev) => ({ ...prev, includeComments: e.target.checked }))
            }
            disabled={isLoading}
          />

          <Checkbox
            label="Include Error Handling"
            checked={config.includeErrorHandling}
            onChange={(e) =>
              setConfig((prev) => ({ ...prev, includeErrorHandling: e.target.checked }))
            }
            disabled={isLoading}
          />

          <Checkbox
            label="Include Documentation"
            checked={config.includeDocumentation}
            onChange={(e) =>
              setConfig((prev) => ({ ...prev, includeDocumentation: e.target.checked }))
            }
            disabled={isLoading}
          />

          <Checkbox
            label="Generate Unit Tests"
            checked={config.includeTests}
            onChange={(e) =>
              setConfig((prev) => ({ ...prev, includeTests: e.target.checked }))
            }
            disabled={isLoading}
          />
        </div>
      </Card>

      {/* Generate Button */}
      <Card>
        <Button
          variant="primary"
          fullWidth
          icon={<Zap className="h-4 w-4" />}
          onClick={handleSubmit}
          isLoading={isLoading}
          disabled={isLoading}
        >
          {isLoading ? 'Generating Code...' : 'Generate Code'}
        </Button>
      </Card>
    </div>
  );
};

CodeGenerator.displayName = 'CodeGenerator';
