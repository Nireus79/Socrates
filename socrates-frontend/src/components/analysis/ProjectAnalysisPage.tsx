/**
 * Project Analysis Page - Comprehensive project analysis interface
 *
 * Features:
 * - Code validation
 * - Test execution
 * - Code review
 * - Structure analysis
 * - Auto-fix with preview
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import {
  CheckCircle,
  AlertCircle,
  Zap,
  FileText,
  Loader,
  AlertTriangle,
  TrendingUp,
} from 'lucide-react';
import { useAnalysisStore } from '../../stores';
import { Button } from '../common';
import { Card } from '../common';
import { Alert } from '../common';
import { Badge } from '../common';
import { AnalysisActionPanel } from './AnalysisActionPanel';
import { AnalysisResultsDisplay } from './AnalysisResultsDisplay';

interface ProjectAnalysisPageProps {
  projectId?: string;
}

export const ProjectAnalysisPage: React.FC<ProjectAnalysisPageProps> = ({
  projectId: propProjectId,
}) => {
  const params = useParams<{ projectId: string }>();
  const projectId = propProjectId || params.projectId || '';
  const {
    validationResults,
    testResults,
    structureAnalysis,
    reviewFindings,
    analysisReport,
    isValidating,
    isTesting,
    isAnalyzing,
    isReviewing,
    error,
    validateCode,
    runTests,
    analyzeStructure,
    reviewCode,
    getAnalysisReport,
    clearResults,
    clearError,
  } = useAnalysisStore();

  const [selectedTab, setSelectedTab] = React.useState<
    'overview' | 'validation' | 'tests' | 'structure' | 'review'
  >('overview');

  const isLoading =
    isValidating || isTesting || isAnalyzing || isReviewing;

  const handleRunAllAnalysis = async () => {
    try {
      await Promise.all([
        validateCode(projectId),
        getAnalysisReport(projectId),
      ]);
    } catch (err) {
      console.error('Analysis failed:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Project Analysis
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Comprehensive code analysis and quality assessment
          </p>
        </div>
        <Button
          icon={<Zap className="h-5 w-5" />}
          onClick={handleRunAllAnalysis}
          disabled={isLoading}
          isLoading={isLoading}
        >
          Run Full Analysis
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert type="error" closeable onClose={clearError}>
          {error}
        </Alert>
      )}

      {/* Overview Cards */}
      {analysisReport && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Code Quality
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {analysisReport.code_quality.score}%
              </p>
              <Badge variant="secondary">
                Grade: {analysisReport.code_quality.grade}
              </Badge>
            </div>
          </Card>

          <Card>
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Issues Found
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {analysisReport.validation.issues}
              </p>
              <Badge variant="secondary">
                {analysisReport.validation.status}
              </Badge>
            </div>
          </Card>

          <Card>
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Test Coverage
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {analysisReport.tests.coverage}%
              </p>
              <Badge variant="secondary">{analysisReport.tests.status}</Badge>
            </div>
          </Card>

          <Card>
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Maintainability
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {analysisReport.structure.maintainability}
              </p>
              <Badge variant="secondary">
                <TrendingUp className="h-3 w-3 mr-1" />
                Index
              </Badge>
            </div>
          </Card>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
        {[
          { id: 'overview' as const, label: 'Overview' },
          { id: 'validation' as const, label: 'Validation' },
          { id: 'tests' as const, label: 'Tests' },
          { id: 'structure' as const, label: 'Structure' },
          { id: 'review' as const, label: 'Review' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id)}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              selectedTab === tab.id
                ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="space-y-4">
        {selectedTab === 'overview' && (
          <div className="space-y-4">
            <AnalysisActionPanel projectId={projectId} />
            {analysisReport && (
              <Card>
                <div className="space-y-4">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Recommendations
                  </h2>
                  {analysisReport.recommendations.length > 0 ? (
                    <ul className="space-y-2">
                      {analysisReport.recommendations.map((rec, idx) => (
                        <li
                          key={idx}
                          className="flex gap-3 text-sm text-gray-700 dark:text-gray-300"
                        >
                          <CheckCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-600 dark:text-gray-400">
                      No recommendations at this time
                    </p>
                  )}
                </div>
              </Card>
            )}
          </div>
        )}

        {selectedTab === 'validation' && (
          <AnalysisResultsDisplay
            title="Code Validation"
            icon={<AlertCircle className="h-5 w-5" />}
            isLoading={isValidating}
            onRefresh={() => validateCode(projectId)}
            results={validationResults}
            resultType="validation"
          />
        )}

        {selectedTab === 'tests' && (
          <AnalysisResultsDisplay
            title="Test Results"
            icon={<CheckCircle className="h-5 w-5" />}
            isLoading={isTesting}
            onRefresh={() => runTests(projectId)}
            results={testResults}
            resultType="tests"
          />
        )}

        {selectedTab === 'structure' && (
          <AnalysisResultsDisplay
            title="Structure Analysis"
            icon={<FileText className="h-5 w-5" />}
            isLoading={isAnalyzing}
            onRefresh={() => analyzeStructure(projectId)}
            results={structureAnalysis}
            resultType="structure"
          />
        )}

        {selectedTab === 'review' && (
          <AnalysisResultsDisplay
            title="Code Review"
            icon={<AlertTriangle className="h-5 w-5" />}
            isLoading={isReviewing}
            onRefresh={() => reviewCode(projectId)}
            results={reviewFindings}
            resultType="review"
          />
        )}
      </div>

      {/* Loading Overlay */}
      {isLoading && (
        <Card className="text-center py-12">
          <Loader className="h-8 w-8 text-blue-600 dark:text-blue-400 mx-auto mb-4 animate-spin" />
          <p className="text-gray-600 dark:text-gray-400">
            Running analysis...
          </p>
        </Card>
      )}
    </div>
  );
};
