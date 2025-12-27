/**
 * ProjectAnalysisPage - Project analysis and validation
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { useProjectStore } from '../../stores';
import { useProjectAnalysisStore } from '../../stores/projectAnalysisStore';
import { MainLayout, PageHeader } from '../../components/layout';
import { Card, Alert, Tab } from '../../components/common';
import { AnalysisActionPanel, AnalysisResultsDisplay } from '../../components/analysis';

type TabType = 'validation' | 'testing' | 'review' | 'maturity' | 'structure' | 'report';

export const ProjectAnalysisPage: React.FC = () => {
  const { projectId } = useParams<{ projectId?: string }>();
  const { projects, getProject } = useProjectStore();
  const {
    selectedProjectId,
    isLoading,
    error,
    validationResult,
    testResult,
    reviewResult,
    maturityResult,
    structureResult,
    reportResult,
    activeAnalysis,
    setSelectedProject,
    validateCode,
    testCode,
    reviewCode,
    assessMaturity,
    analyzeStructure,
    fixCode,
    getReport,
    clearError,
  } = useProjectAnalysisStore();

  const [activeTab, setActiveTab] = React.useState<TabType>('validation');

  React.useEffect(() => {
    if (projectId) {
      setSelectedProject(projectId);
      getProject(projectId);
    }
  }, [projectId, setSelectedProject, getProject]);

  const handleAnalysisComplete = (tab: TabType) => {
    setActiveTab(tab);
    clearError();
  };

  return (
    <MainLayout>
      <PageHeader
        title="Project Analysis"
        description="Validate, test, review, and analyze your project code"
      />

      <div className="space-y-6">
        {!projectId && (
          <Card>
            <div className="p-6">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
                Select a Project
              </h3>
              {projects.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400">No projects available</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {projects.map((project) => (
                    <button
                      key={project.id}
                      onClick={() => setSelectedProject(project.id)}
                      className="p-4 text-left rounded border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 transition-colors"
                    >
                      <p className="font-medium text-gray-900 dark:text-white">{project.name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{project.id}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </Card>
        )}

        {error && (
          <Alert
            title="Error"
            description={error}
            variant="error"
            onClose={clearError}
          />
        )}

        <AnalysisActionPanel
          projectId={selectedProjectId || ''}
          isLoading={isLoading}
          onValidate={() => {
            if (selectedProjectId) {
              validateCode(selectedProjectId);
              handleAnalysisComplete('validation');
            }
          }}
          onTest={() => {
            if (selectedProjectId) {
              testCode(selectedProjectId);
              handleAnalysisComplete('testing');
            }
          }}
          onReview={() => {
            if (selectedProjectId) {
              reviewCode(selectedProjectId);
              handleAnalysisComplete('review');
            }
          }}
          onMaturity={() => {
            if (selectedProjectId) {
              assessMaturity(selectedProjectId);
              handleAnalysisComplete('maturity');
            }
          }}
          onStructure={() => {
            if (selectedProjectId) {
              analyzeStructure(selectedProjectId);
              handleAnalysisComplete('structure');
            }
          }}
          onFix={() => {
            if (selectedProjectId) {
              fixCode(selectedProjectId);
            }
          }}
          onReport={() => {
            if (selectedProjectId) {
              getReport(selectedProjectId);
              handleAnalysisComplete('report');
            }
          }}
        />

        {selectedProjectId && (
          <>
            <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
              <Tab
                label="Validation"
                active={activeTab === 'validation'}
                onClick={() => setActiveTab('validation')}
              />
              <Tab
                label="Testing"
                active={activeTab === 'testing'}
                onClick={() => setActiveTab('testing')}
              />
              <Tab
                label="Review"
                active={activeTab === 'review'}
                onClick={() => setActiveTab('review')}
              />
              <Tab
                label="Maturity"
                active={activeTab === 'maturity'}
                onClick={() => setActiveTab('maturity')}
              />
              <Tab
                label="Structure"
                active={activeTab === 'structure'}
                onClick={() => setActiveTab('structure')}
              />
              <Tab
                label="Report"
                active={activeTab === 'report'}
                onClick={() => setActiveTab('report')}
              />
            </div>

            <div>
              {activeTab === 'validation' && (
                <AnalysisResultsDisplay
                  title="Code Validation Results"
                  result={validationResult}
                  isLoading={isLoading && activeAnalysis === 'validation'}
                  error={error}
                />
              )}
              {activeTab === 'testing' && (
                <AnalysisResultsDisplay
                  title="Test Results"
                  result={testResult}
                  isLoading={isLoading && activeAnalysis === 'testing'}
                  error={error}
                />
              )}
              {activeTab === 'review' && (
                <AnalysisResultsDisplay
                  title="Code Review Results"
                  result={reviewResult}
                  isLoading={isLoading && activeAnalysis === 'review'}
                  error={error}
                />
              )}
              {activeTab === 'maturity' && (
                <AnalysisResultsDisplay
                  title="Maturity Assessment"
                  result={maturityResult}
                  isLoading={isLoading && activeAnalysis === 'maturity'}
                  error={error}
                />
              )}
              {activeTab === 'structure' && (
                <AnalysisResultsDisplay
                  title="Structure Analysis"
                  result={structureResult}
                  isLoading={isLoading && activeAnalysis === 'structure'}
                  error={error}
                />
              )}
              {activeTab === 'report' && (
                <AnalysisResultsDisplay
                  title="Analysis Report"
                  result={reportResult}
                  isLoading={isLoading && activeAnalysis === 'report'}
                  error={error}
                />
              )}
            </div>
          </>
        )}
      </div>
    </MainLayout>
  );
};
