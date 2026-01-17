/**
 * Analysis & Testing Control Panel
 *
 * Allows users to:
 * - Run code validation (syntax, dependencies)
 * - Execute tests (pytest, jest, mocha)
 * - Analyze code structure and quality
 * - Auto-fix issues
 * - Assess code maturity
 * - View analysis results and recommendations
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useProjectStore } from '../../stores/projectStore';
import { MainLayout, PageHeader } from '../../components/layout';
import { Card, Alert } from '../../components/common';
import { AnalysisActionPanel } from '../../components/analysis/AnalysisActionPanel';
import { AnalysisResultsDisplay } from '../../components/analysis/AnalysisResultsDisplay';
import { analysisAPI } from '../../api/analysis';

interface AnalysisResults {
  validation: any | null;
  tests: any | null;
  structure: any | null;
  review: any | null;
  maturity: any | null;
  fix: any | null;
  report: any | null;
}

interface LoadingState {
  validation: boolean;
  tests: boolean;
  structure: boolean;
  review: boolean;
  maturity: boolean;
  fix: boolean;
  report: boolean;
}

interface ErrorState {
  validation: string | null;
  tests: string | null;
  structure: string | null;
  review: string | null;
  maturity: string | null;
  fix: string | null;
  report: string | null;
}

export const AnalysisPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { currentProject, projects, getProject, listProjects } = useProjectStore();
  const [selectedProjectId, setSelectedProjectId] = useState<string>(projectId || '');

  // Analysis results state
  const [results, setResults] = useState<AnalysisResults>({
    validation: null,
    tests: null,
    structure: null,
    review: null,
    maturity: null,
    fix: null,
    report: null,
  });

  // Loading state for each action
  const [loading, setLoading] = useState<LoadingState>({
    validation: false,
    tests: false,
    structure: false,
    review: false,
    maturity: false,
    fix: false,
    report: false,
  });

  // Error state for each action
  const [errors, setErrors] = useState<ErrorState>({
    validation: null,
    tests: null,
    structure: null,
    review: null,
    maturity: null,
    fix: null,
    report: null,
  });

  // Track which result is currently displayed
  const [activeResult, setActiveResult] = useState<keyof AnalysisResults | null>(null);

  useEffect(() => {
    listProjects();
  }, [listProjects]);

  useEffect(() => {
    if (selectedProjectId) {
      getProject(selectedProjectId);
    }
  }, [selectedProjectId, getProject]);

  // Update selected project when URL param changes
  useEffect(() => {
    if (projectId && !selectedProjectId) {
      setSelectedProjectId(projectId);
    }
  }, [projectId, selectedProjectId]);

  const effectiveProjectId = selectedProjectId || projectId;
  const isLoading = Object.values(loading).some((l) => l);

  // Handler: Validate Code
  const handleValidate = async () => {
    if (!effectiveProjectId) return;

    setLoading((prev) => ({ ...prev, validation: true }));
    setErrors((prev) => ({ ...prev, validation: null }));
    setActiveResult('validation');

    try {
      const result = await analysisAPI.validateCode(effectiveProjectId);
      setResults((prev) => ({ ...prev, validation: result }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to validate code';
      setErrors((prev) => ({ ...prev, validation: errorMessage }));
    } finally {
      setLoading((prev) => ({ ...prev, validation: false }));
    }
  };

  // Handler: Run Tests
  const handleTest = async () => {
    if (!effectiveProjectId) return;

    setLoading((prev) => ({ ...prev, tests: true }));
    setErrors((prev) => ({ ...prev, tests: null }));
    setActiveResult('tests');

    try {
      const result = await analysisAPI.runTests(effectiveProjectId);
      setResults((prev) => ({ ...prev, tests: result }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to run tests';
      setErrors((prev) => ({ ...prev, tests: errorMessage }));
    } finally {
      setLoading((prev) => ({ ...prev, tests: false }));
    }
  };

  // Handler: Code Review
  const handleReview = async () => {
    if (!effectiveProjectId) return;

    setLoading((prev) => ({ ...prev, review: true }));
    setErrors((prev) => ({ ...prev, review: null }));
    setActiveResult('review');

    try {
      const result = await analysisAPI.reviewCode(effectiveProjectId);
      setResults((prev) => ({ ...prev, review: result }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to review code';
      setErrors((prev) => ({ ...prev, review: errorMessage }));
    } finally {
      setLoading((prev) => ({ ...prev, review: false }));
    }
  };

  // Handler: Assess Maturity
  const handleMaturity = async () => {
    if (!effectiveProjectId) return;

    setLoading((prev) => ({ ...prev, maturity: true }));
    setErrors((prev) => ({ ...prev, maturity: null }));
    setActiveResult('maturity');

    try {
      const result = await analysisAPI.assessMaturity(effectiveProjectId);
      setResults((prev) => ({ ...prev, maturity: result }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to assess maturity';
      setErrors((prev) => ({ ...prev, maturity: errorMessage }));
    } finally {
      setLoading((prev) => ({ ...prev, maturity: false }));
    }
  };

  // Handler: Analyze Structure
  const handleStructure = async () => {
    if (!effectiveProjectId) return;

    setLoading((prev) => ({ ...prev, structure: true }));
    setErrors((prev) => ({ ...prev, structure: null }));
    setActiveResult('structure');

    try {
      const result = await analysisAPI.analyzeStructure(effectiveProjectId);
      setResults((prev) => ({ ...prev, structure: result }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to analyze structure';
      setErrors((prev) => ({ ...prev, structure: errorMessage }));
    } finally {
      setLoading((prev) => ({ ...prev, structure: false }));
    }
  };

  // Handler: Fix Issues
  const handleFix = async () => {
    if (!effectiveProjectId) return;

    setLoading((prev) => ({ ...prev, fix: true }));
    setErrors((prev) => ({ ...prev, fix: null }));
    setActiveResult('fix');

    try {
      const result = await analysisAPI.autoFixIssues(effectiveProjectId);
      setResults((prev) => ({ ...prev, fix: result }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fix issues';
      setErrors((prev) => ({ ...prev, fix: errorMessage }));
    } finally {
      setLoading((prev) => ({ ...prev, fix: false }));
    }
  };

  // Handler: Generate Report
  const handleReport = async () => {
    if (!effectiveProjectId) return;

    setLoading((prev) => ({ ...prev, report: true }));
    setErrors((prev) => ({ ...prev, report: null }));
    setActiveResult('report');

    try {
      const result = await analysisAPI.getAnalysisReport(effectiveProjectId);
      setResults((prev) => ({ ...prev, report: result }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate report';
      setErrors((prev) => ({ ...prev, report: errorMessage }));
    } finally {
      setLoading((prev) => ({ ...prev, report: false }));
    }
  };

  return (
    <MainLayout>
      {/* Project Selector */}
      {projects.length > 0 && (
        <div className="max-w-6xl mx-auto px-4 py-4">
          <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 dark:from-blue-900 dark:to-indigo-900 dark:border-blue-800">
            <div className="flex items-center gap-3">
              <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 whitespace-nowrap">
                Select Project:
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="">-- Choose a Project --</option>
                {projects.map((project) => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
          </Card>
        </div>
      )}

      {/* Page Header */}
      <PageHeader
        title="Code Analysis & Testing"
        description="Validate, analyze, test, and improve your project code"
      />

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* No Project Selected */}
        {!effectiveProjectId && (
          <Alert type="info" title="No Project Selected">
            Please select a project from the dropdown above to begin analysis.
          </Alert>
        )}

        {effectiveProjectId && (
          <>
            {/* Action Panel */}
            <AnalysisActionPanel
              projectId={effectiveProjectId}
              isLoading={isLoading}
              onValidate={handleValidate}
              onTest={handleTest}
              onReview={handleReview}
              onMaturity={handleMaturity}
              onStructure={handleStructure}
              onFix={handleFix}
              onReport={handleReport}
            />

            {/* Results Section */}
            <div className="space-y-6">
              {/* Code Validation Results */}
              {activeResult === 'validation' && (
                <AnalysisResultsDisplay
                  title="Code Validation"
                  result={results.validation}
                  isLoading={loading.validation}
                  error={errors.validation || undefined}
                />
              )}

              {/* Test Results */}
              {activeResult === 'tests' && (
                <AnalysisResultsDisplay
                  title="Test Results"
                  result={results.tests}
                  isLoading={loading.tests}
                  error={errors.tests || undefined}
                />
              )}

              {/* Structure Analysis Results */}
              {activeResult === 'structure' && (
                <AnalysisResultsDisplay
                  title="Structure Analysis"
                  result={results.structure}
                  isLoading={loading.structure}
                  error={errors.structure || undefined}
                />
              )}

              {/* Code Review Results */}
              {activeResult === 'review' && (
                <AnalysisResultsDisplay
                  title="Code Review"
                  result={results.review}
                  isLoading={loading.review}
                  error={errors.review || undefined}
                />
              )}

              {/* Maturity Assessment Results */}
              {activeResult === 'maturity' && (
                <AnalysisResultsDisplay
                  title="Maturity Assessment"
                  result={results.maturity}
                  isLoading={loading.maturity}
                  error={errors.maturity || undefined}
                />
              )}

              {/* Auto-Fix Results */}
              {activeResult === 'fix' && (
                <AnalysisResultsDisplay
                  title="Issue Fixes"
                  result={results.fix}
                  isLoading={loading.fix}
                  error={errors.fix || undefined}
                />
              )}

              {/* Analysis Report Results */}
              {activeResult === 'report' && (
                <AnalysisResultsDisplay
                  title="Analysis Report"
                  result={results.report}
                  isLoading={loading.report}
                  error={errors.report || undefined}
                />
              )}

              {/* No Results Yet */}
              {!activeResult && (
                <Card className="p-8 text-center bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                  <p className="text-gray-600 dark:text-gray-400">
                    Click an action button above to start analyzing your project.
                  </p>
                </Card>
              )}
            </div>
          </>
        )}
      </div>
    </MainLayout>
  );
};

export default AnalysisPage;
