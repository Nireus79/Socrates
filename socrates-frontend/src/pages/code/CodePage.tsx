/**
 * CodePage - Code generation interface
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { useCodeGenerationStore, useSubscriptionStore } from '../../stores';
import { MainLayout, PageHeader } from '../../components/layout';
import {
  CodeGenerator,
  CodeOutput,
  CodeValidation,
} from '../../components/code';
import type {
  CodeGenerationConfig,
  ValidationIssue,
  CodeMetrics,
} from '../../components/code';
import { Card, Alert, Tab, LoadingSpinner } from '../../components/common';

export const CodePage: React.FC = () => {
  const { projectId } = useParams<{ projectId?: string }>();
  const { hasFeature } = useSubscriptionStore();
  const {
    generatedCode,
    validationResult,
    codeHistory,
    isLoading: isGenerating,
    error: codeError,
    currentLanguage,
    generateCode,
    validateCode,
    loadCodeHistory,
    clearError,
  } = useCodeGenerationStore();

  const [activeTab, setActiveTab] = React.useState('generator');
  const [isFullScreen, setIsFullScreen] = React.useState(false);

  // Check if code generation feature is available
  if (!hasFeature('code_generation')) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg p-8 max-w-md text-center">
            <h2 className="text-2xl font-bold mb-2">Premium Feature</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Code generation is available on Pro and Enterprise plans.
            </p>
            <button
              onClick={() => window.location.href = '/settings?tab=subscription'}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded"
            >
              Upgrade Now
            </button>
          </div>
        </div>
      </MainLayout>
    );
  }

  // Load code history
  React.useEffect(() => {
    if (projectId) {
      loadCodeHistory(projectId);
    }
  }, [projectId, loadCodeHistory]);

  const handleGenerate = async (config: CodeGenerationConfig) => {
    if (!projectId) {
      console.error('No project ID provided');
      return;
    }

    try {
      await generateCode(projectId, config.prompt, config.language as any);
      // Automatically validate the generated code
      if (generatedCode?.code) {
        await validateCode(projectId, generatedCode.code, config.language as any);
      }
      setActiveTab('output');
    } catch (error) {
      console.error('Failed to generate code:', error);
    }
  };

  const tabs = [
    { label: 'Generator', value: 'generator' },
    { label: 'Output', value: 'output' },
    { label: 'Validation', value: 'validation' },
    { label: 'History', value: 'history' },
  ];

  if (codeError) {
    return (
      <MainLayout>
        <Alert type="error" title="Code Generation Error">
          <p className="mb-3">{codeError}</p>
          <button
            onClick={() => clearError()}
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            Dismiss
          </button>
        </Alert>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <PageHeader
          title="Code Generation"
          description="Generate, validate, and manage code across multiple languages"
          breadcrumbs={[
            { label: 'Dashboard', onClick: () => window.location.href = '/dashboard' },
            { label: 'Code Generation' },
          ]}
        />

        {/* Tabs */}
        <Card>
          <Tab
            tabs={tabs}
            activeTab={activeTab}
            onChange={setActiveTab}
            variant="default"
          />
        </Card>

        {/* Generator Tab */}
        {activeTab === 'generator' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <CodeGenerator
                onGenerate={handleGenerate}
                isLoading={isGenerating}
                defaultLanguage={currentLanguage}
              />
            </div>

            {/* Recent Generations */}
            <div>
              <Card>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Recent Generations
                </h3>

                {isGenerating ? (
                  <div className="flex items-center justify-center py-8">
                    <LoadingSpinner size="sm" />
                  </div>
                ) : codeHistory.length === 0 ? (
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    No code generated yet. Create your first generation to get started.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {codeHistory.slice(0, 5).map((code) => (
                      <button
                        key={code.generation_id}
                        onClick={() => setActiveTab('output')}
                        className="w-full text-left p-3 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      >
                        <div className="flex justify-between items-start gap-2 mb-1">
                          <span className="text-sm font-medium text-gray-900 dark:text-white uppercase">
                            {code.language}
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {new Date(code.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                          {code.explanation?.substring(0, 50)}...
                        </p>
                      </button>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          </div>
        )}

        {/* Output Tab */}
        {activeTab === 'output' && generatedCode ? (
          <div className={isFullScreen ? '' : 'grid grid-cols-1 lg:grid-cols-3 gap-6'}>
            <div className={isFullScreen ? 'fixed inset-0 z-40' : 'lg:col-span-2'}>
              <CodeOutput
                code={generatedCode.code}
                language={generatedCode.language}
                onAccept={() => {
                  console.log('Code accepted');
                  setActiveTab('generator');
                }}
                onRegenerate={() => {
                  setActiveTab('generator');
                }}
                onCopy={() => {
                  navigator.clipboard.writeText(generatedCode.code);
                }}
                isFullScreen={isFullScreen}
                onToggleFullScreen={() => setIsFullScreen(!isFullScreen)}
              />
            </div>

            {!isFullScreen && (
              <div className="lg:col-span-1">
                <Card>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Code Info
                  </h3>
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="text-gray-600 dark:text-gray-400 mb-1">Language</p>
                      <p className="font-medium text-gray-900 dark:text-white uppercase">
                        {generatedCode.language}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600 dark:text-gray-400 mb-1">Generated</p>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {new Date(generatedCode.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600 dark:text-gray-400 mb-1">Explanation</p>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {generatedCode.explanation}
                      </p>
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </div>
        ) : activeTab === 'output' ? (
          <Card>
            <Alert type="info" title="No Code Generated">
              Generate some code first, then view and validate it here.
            </Alert>
          </Card>
        ) : null}

        {/* Validation Tab */}
        {activeTab === 'validation' && validationResult ? (
          <CodeValidation
            issues={[
              ...validationResult.errors.map(e => ({ message: e, severity: 'error' as const })),
              ...validationResult.warnings.map(w => ({ message: w, severity: 'warning' as const }))
            ] as unknown as ValidationIssue[]}
            metrics={{ complexityScore: validationResult.complexity_score, readabilityScore: validationResult.readability_score } as unknown as CodeMetrics}
            isLoading={isGenerating}
          />
        ) : activeTab === 'validation' ? (
          <Card>
            <Alert type="info" title="No Code to Validate">
              Generate code first to see validation results.
            </Alert>
          </Card>
        ) : null}

        {/* History Tab */}
        {activeTab === 'history' && (
          <Card>
            {codeHistory.length === 0 ? (
              <Alert type="info" title="No History">
                Your code generation history will appear here.
              </Alert>
            ) : (
              <div className="space-y-3">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Generated Code History ({codeHistory.length})
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700">
                        <th className="text-left py-3 px-4 font-medium text-gray-700 dark:text-gray-300">
                          Language
                        </th>
                        <th className="text-left py-3 px-4 font-medium text-gray-700 dark:text-gray-300">
                          Specification
                        </th>
                        <th className="text-left py-3 px-4 font-medium text-gray-700 dark:text-gray-300">
                          Generated
                        </th>
                        <th className="text-center py-3 px-4 font-medium text-gray-700 dark:text-gray-300">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {codeHistory.map((code) => (
                        <tr
                          key={code.generation_id}
                          className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                        >
                          <td className="py-3 px-4">
                            <span className="font-medium uppercase text-gray-900 dark:text-white">
                              {code.language}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                            {code.explanation?.substring(0, 40)}...
                          </td>
                          <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                            {new Date(code.created_at).toLocaleString()}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <button
                              onClick={() => setActiveTab('output')}
                              className="text-blue-600 dark:text-blue-400 hover:underline"
                            >
                              View
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </Card>
        )}
      </div>
    </MainLayout>
  );
};
