/**
 * AnalyticsPage - Analytics dashboard with maturity and metrics
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { Download, TrendingUp } from 'lucide-react';
import { useProjectStore, useAnalyticsStore } from '../../stores';
import { MainLayout, PageHeader } from '../../components/layout';
import {
  MaturityOverview,
  AnalyticsStats,
  CategoryBreakdown,
  TrendsChart,
} from '../../components/analytics';
import { Card, Tab, Alert, LoadingSpinner, Button } from '../../components/common';

export const AnalyticsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId?: string }>();
  const {
    currentProject,
    projectStats,
    projectMaturity,
    isLoading,
    fetchStats,
    fetchMaturity,
  } = useProjectStore();

  const {
    summary,
    trends,
    recommendations,
    isLoadingTrends,
    isLoadingRecommendations,
    isExporting,
    error,
    getTrends,
    getRecommendations,
    exportAnalytics,
    clearError,
  } = useAnalyticsStore();

  const [activeTab, setActiveTab] = React.useState('summary');

  // Map phase name to phase number
  const phaseNumber = {
    'discovery': 1,
    'analysis': 2,
    'design': 3,
    'implementation': 4,
    'testing': 5,
    'deployment': 6,
  }[currentProject?.phase || 'discovery'] || 1;

  // Load analytics data
  React.useEffect(() => {
    if (projectId) {
      fetchStats(projectId);
      fetchMaturity(projectId);
      getTrends(projectId);
      getRecommendations(projectId);
    }
  }, [projectId, fetchStats, fetchMaturity, getTrends, getRecommendations]);

  // Clear errors when user navigates
  React.useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);

  // Handle export analytics
  const handleExportAnalytics = async (format: 'csv' | 'json' | 'pdf' = 'json') => {
    if (!projectId) return;
    try {
      const result = await exportAnalytics(projectId, format);
      if (result) {
        // Create a blob and download
        const blob = new Blob([result.data], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = result.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const tabs = [
    { label: 'Summary', value: 'summary' },
    { label: 'Categories', value: 'categories' },
    { label: 'Recommendations', value: 'recommendations' },
    { label: 'Trends', value: 'trends' },
  ];

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <LoadingSpinner size="lg" />
        </div>
      </MainLayout>
    );
  }

  // Build stats from API data or use defaults
  const stats = [
    {
      label: 'Total Questions',
      value: projectStats?.total_questions ?? 0,
      change: projectStats?.questions_change ?? 0,
      period: 'vs last session',
    },
    {
      label: 'Avg Confidence',
      value: `${projectStats?.average_confidence ?? 0}%`,
      change: projectStats?.confidence_change ?? 0,
      period: 'vs last session',
    },
    {
      label: 'Code Generated',
      value: projectStats?.code_generations ?? 0,
      change: projectStats?.code_generation_change ?? 0,
      period: 'vs last session',
    },
    {
      label: 'Velocity',
      value: `${projectStats?.velocity ?? 0} pts/hr`,
      change: projectStats?.velocity_change ?? 0,
      period: 'vs last session',
    },
  ];

  const phaseMaturity = [
    {
      number: 1,
      name: 'Discovery',
      maturity: projectMaturity?.phase_1_maturity ?? 0,
      isComplete: currentProject?.phase !== 'discovery',
    },
    {
      number: 2,
      name: 'Analysis',
      maturity: projectMaturity?.phase_2_maturity ?? 0,
      isComplete: !['discovery', 'analysis'].includes(currentProject?.phase || ''),
    },
    {
      number: 3,
      name: 'Design',
      maturity: projectMaturity?.phase_3_maturity ?? 0,
      isComplete: !['discovery', 'analysis', 'design'].includes(currentProject?.phase || ''),
    },
    {
      number: 4,
      name: 'Implementation',
      maturity: projectMaturity?.phase_4_maturity ?? 0,
      isComplete: false,
    },
  ];

  const categories = projectMaturity?.categories ?? [];

  return (
    <MainLayout>
      <div className="space-y-8">
        {/* Error Alert */}
        {error && (
          <Alert type="error" title="Error">
            {error}
          </Alert>
        )}

        {/* Header */}
        <div className="flex justify-between items-start">
          <PageHeader
            title="Analytics & Maturity"
            description="Track your project's progress across phases and categories"
            breadcrumbs={[
              { label: 'Dashboard', onClick: () => window.location.href = '/dashboard' },
              { label: 'Analytics' },
            ]}
          />
          <Button
            onClick={() => handleExportAnalytics('json')}
            disabled={isExporting}
            variant="outline"
            className="flex items-center gap-2"
          >
            <Download size={18} />
            {isExporting ? 'Exporting...' : 'Export'}
          </Button>
        </div>

        {/* Stats Grid */}
        <AnalyticsStats stats={stats} />

        {/* Tabs */}
        <Card>
          <Tab
            tabs={tabs}
            activeTab={activeTab}
            onChange={setActiveTab}
            variant="default"
          />
        </Card>

        {/* Summary Tab */}
        {activeTab === 'summary' && (
          <div className="space-y-6">
            <MaturityOverview
              overallMaturity={projectMaturity?.overall_score ?? 0}
              phases={phaseMaturity}
              strongestCategory={projectMaturity?.strongest_category ?? 'N/A'}
              weakestCategory={projectMaturity?.weakest_category ?? 'N/A'}
              readyToAdvance={projectMaturity?.ready_to_advance ?? false}
            />
          </div>
        )}

        {/* Categories Tab */}
        {activeTab === 'categories' && (
          <div className="space-y-6">
            {categories.length > 0 ? (
              <CategoryBreakdown phase={phaseNumber} categories={categories} />
            ) : (
              <Alert type="info" title="No Category Data">
                Complete more dialogue to generate maturity insights across categories.
              </Alert>
            )}
          </div>
        )}

        {/* Recommendations Tab */}
        {activeTab === 'recommendations' && (
          <div className="space-y-4">
            {isLoadingRecommendations ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="lg" />
              </div>
            ) : recommendations?.recommendations && recommendations.recommendations.length > 0 ? (
              recommendations.recommendations.map((rec: any, index: number) => {
                const priority = rec.priority || 'info';
                const priorityColor =
                  priority === 'high'
                    ? { bg: 'bg-red-100 dark:bg-red-900', text: 'text-red-700 dark:text-red-200', dot: 'bg-red-500' }
                    : priority === 'medium'
                    ? { bg: 'bg-yellow-100 dark:bg-yellow-900', text: 'text-yellow-700 dark:text-yellow-200', dot: 'bg-yellow-500' }
                    : { bg: 'bg-blue-100 dark:bg-blue-900', text: 'text-blue-700 dark:text-blue-200', dot: 'bg-blue-500' };

                return (
                  <Card key={`rec-${index}-${rec.title}`}>
                    <div className="flex gap-4">
                      <div className="flex-shrink-0 mt-1">
                        <div className={`w-3 h-3 rounded-full ${priorityColor.dot}`} />
                      </div>

                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {rec.title}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {rec.description}
                        </p>
                      </div>

                      <div className="flex-shrink-0">
                        <span
                          className={`text-xs font-medium uppercase px-2 py-1 rounded ${priorityColor.bg} ${priorityColor.text}`}
                        >
                          {priority}
                        </span>
                      </div>
                    </div>
                  </Card>
                );
              })
            ) : (
              <Alert type="info" title="No Recommendations Yet">
                Continue your dialogue to generate personalized recommendations for improvement.
              </Alert>
            )}
          </div>
        )}

        {/* Trends Tab */}
        {activeTab === 'trends' && (
          <>
            {isLoadingTrends ? (
              <div className="flex justify-center py-12">
                <LoadingSpinner size="lg" />
              </div>
            ) : trends?.trends && trends.trends.length > 0 ? (
              <TrendsChart
                projectId={projectId || ''}
                isLoading={isLoadingTrends}
              />
            ) : (
              <Alert type="info" title="No Trends Data">
                Not enough data to display trends. Continue your work on the project to generate trend analysis.
              </Alert>
            )}
          </>
        )}
      </div>
    </MainLayout>
  );
};
