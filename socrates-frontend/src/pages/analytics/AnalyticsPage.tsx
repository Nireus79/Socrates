/**
 * AnalyticsPage - Analytics dashboard with maturity and metrics
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { Download, TrendingUp, BarChart3, PieChart, ChevronDown } from 'lucide-react';
import { useProjectStore } from '../../stores';
import { apiClient } from '../../api/client';
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
    projects,
    currentProject,
    isLoading: projectLoading,
    loadProject,
  } = useProjectStore();

  // Local state for selected project and analytics data
  const [selectedProjectId, setSelectedProjectId] = React.useState<string>(projectId || '');
  const [analyticsData, setAnalyticsData] = React.useState<any>(null);
  const [maturityData, setMaturityData] = React.useState<any>(null);
  const [breakdownData, setBreakdownData] = React.useState<any>(null);
  const [statusData, setStatusData] = React.useState<any>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [isDropdownOpen, setIsDropdownOpen] = React.useState(false);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  const [activeTab, setActiveTab] = React.useState('summary');

  // Update selected project when URL projectId changes
  React.useEffect(() => {
    if (projectId) {
      setSelectedProjectId(projectId);
    }
  }, [projectId]);

  // Load analytics data when selected project changes
  React.useEffect(() => {
    if (!selectedProjectId) return;

    const loadAnalytics = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Fetch main analytics data
        const analytics = await apiClient.get(`/analytics/projects/${selectedProjectId}`) as any;
        setAnalyticsData(analytics?.data || analytics);

        // Fetch maturity data
        const maturity = await apiClient.get(`/projects/${selectedProjectId}/maturity`) as any;
        setMaturityData(maturity?.data || maturity);

        // Fetch breakdown data
        const breakdown = await apiClient.get(`/analytics/breakdown/${selectedProjectId}`) as any;
        setBreakdownData(breakdown?.data || breakdown);

        // Fetch status data
        const status = await apiClient.get(`/analytics/status/${selectedProjectId}`) as any;
        setStatusData(status?.data || status);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics');
        console.error('Analytics error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadAnalytics();
  }, [selectedProjectId]);

  // Handle clicking outside dropdown
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isDropdownOpen]);

  // Handle project selection from dropdown
  const handleProjectChange = (newProjectId: string) => {
    setSelectedProjectId(newProjectId);
    setIsDropdownOpen(false);
  };

  // Get the selected project object for display
  const selectedProject = projects.find(p => p.project_id === selectedProjectId) || currentProject;

  // Handle export analytics
  const handleExportAnalytics = async (format: 'csv' | 'pdf' = 'pdf') => {
    if (!selectedProjectId) return;
    try {
      // Step 1: Call export endpoint to generate the report
      const result = await apiClient.post(`/analytics/export`, {
        project_id: selectedProjectId,
        format
      }) as any;

      if (result?.filename) {
        // Step 2: Download the generated report file
        const downloadUrl = `/analytics/export/${result.filename}`;
        const response = await fetch(downloadUrl);

        if (!response.ok) {
          throw new Error(`Failed to download file: ${response.statusText}`);
        }

        // Step 3: Create blob and trigger download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = result.filename || `analytics-${selectedProjectId}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        console.log('Export successful:', result.filename);
      } else {
        throw new Error('No filename in export response');
      }
    } catch (err) {
      console.error('Export failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to export analytics');
    }
  };

  const tabs = [
    { label: 'Summary', value: 'summary' },
    { label: 'Breakdown', value: 'breakdown' },
    { label: 'Status', value: 'status' },
    { label: 'Details', value: 'details' },
  ];

  if (!selectedProjectId && projects.length === 0) {
    return (
      <MainLayout>
        <div className="space-y-4">
          <PageHeader
            title="📊 Analytics & Maturity"
            description="Real-time analytics and project progress tracking"
            breadcrumbs={[
              { label: 'Dashboard', onClick: () => window.location.href = '/dashboard' },
              { label: 'Analytics' },
            ]}
          />
          <Alert type="info" title="No Projects">
            You don't have any projects yet. Create a project first to view analytics.
          </Alert>
        </div>
      </MainLayout>
    );
  }

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <LoadingSpinner size="lg" />
        </div>
      </MainLayout>
    );
  }

  // Build stats from fetched analytics data
  const stats = analyticsData ? [
    {
      label: 'Total Questions',
      value: analyticsData.total_questions ?? 0,
      change: 0,
      period: 'this session',
    },
    {
      label: 'Maturity Score',
      value: `${(analyticsData.maturity_score ?? 0).toFixed(2)}%`,
      change: 0,
      period: 'overall',
    },
    {
      label: 'Completion %',
      value: `${(analyticsData.completion_percentage ?? 0).toFixed(1)}%`,
      change: 0,
      period: 'current phase',
    },
    {
      label: 'Avg Response Time',
      value: `${(analyticsData.average_response_time ?? 0).toFixed(2)}s`,
      change: 0,
      period: 'per question',
    },
  ] : [
    { label: 'Total Questions', value: 0, change: 0, period: 'this session' },
    { label: 'Maturity Score', value: '0.00', change: 0, period: 'overall' },
    { label: 'Completion %', value: '0.0%', change: 0, period: 'current phase' },
    { label: 'Avg Response Time', value: '0.00s', change: 0, period: 'per question' },
  ];

  // Build phase maturity data from fetched data
  const phaseMaturity = maturityData?.phase_maturity_scores ? Object.entries(maturityData.phase_maturity_scores).map(([phase, score]: [string, any], idx) => ({
    number: idx + 1,
    name: phase.charAt(0).toUpperCase() + phase.slice(1),
    maturity: score,
    isComplete: false,
  })) : [];

  // Get categories from maturity data
  const categories = maturityData?.categories ?? [];

  return (
    <MainLayout>
      <div className="space-y-8">
        {/* Error Alert */}
        {error && (
          <Alert type="error" title="Error">
            {error}
          </Alert>
        )}

        {/* Header with Project Selector */}
        <div className="space-y-4">
          <div className="flex justify-between items-start">
            <PageHeader
              title="📊 Analytics & Maturity"
              description="Real-time analytics and project progress tracking"
              breadcrumbs={[
                { label: 'Dashboard', onClick: () => window.location.href = '/dashboard' },
                { label: 'Analytics' },
              ]}
            />
            <Button
              onClick={() => handleExportAnalytics('pdf')}
              variant="outline"
              className="flex items-center gap-2"
            >
              <Download size={18} />
              Export Data (PDF)
            </Button>
          </div>

          {/* Project Selector Dropdown */}
          <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
            <div className="flex items-center gap-3">
              <label className="text-sm font-semibold text-gray-700">
                Select Project:
              </label>

              {/* Custom Styled Dropdown */}
              <div ref={dropdownRef} className="flex-1 relative">
                <button
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="w-full px-4 py-2 border border-indigo-300 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 bg-indigo-100 text-gray-900 text-left flex items-center justify-between hover:bg-indigo-200 transition-colors"
                >
                  <span>{selectedProject?.name || '-- Choose a Project --'}</span>
                  <ChevronDown
                    size={18}
                    className={`text-gray-600 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`}
                  />
                </button>

                {/* Dropdown Menu */}
                {isDropdownOpen && (
                  <div
                    className="absolute top-full left-0 right-0 mt-1 rounded-lg shadow-lg z-50"
                    style={{
                      backgroundColor: '#c7d2fe',
                      border: '2px solid #a5b4fc',
                    }}
                  >
                    <div className="py-1 max-h-64 overflow-y-auto">
                      <button
                        onClick={() => handleProjectChange('')}
                        className="w-full px-4 py-2 text-sm text-gray-900 text-left transition-colors"
                        style={{
                          backgroundColor: '#c7d2fe',
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#a5b4fc'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#c7d2fe'}
                      >
                        -- Choose a Project --
                      </button>
                      {projects.length > 0 ? (
                        projects.map((project) => (
                          <button
                            key={project.project_id}
                            onClick={() => handleProjectChange(project.project_id)}
                            className="w-full px-4 py-2 text-sm text-left transition-colors"
                            style={{
                              backgroundColor: selectedProjectId === project.project_id ? '#3b82f6' : '#c7d2fe',
                              color: selectedProjectId === project.project_id ? 'white' : '#111827',
                              fontWeight: selectedProjectId === project.project_id ? 'bold' : 'normal',
                            }}
                            onMouseEnter={(e) => {
                              if (selectedProjectId !== project.project_id) {
                                e.currentTarget.style.backgroundColor = '#a5b4fc';
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (selectedProjectId !== project.project_id) {
                                e.currentTarget.style.backgroundColor = '#c7d2fe';
                              }
                            }}
                          >
                            {project.name} {selectedProjectId === project.project_id ? '✓' : ''}
                          </button>
                        ))
                      ) : (
                        <div className="px-4 py-2 text-sm text-gray-700">No projects available</div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {selectedProject && (
                <div className="text-sm text-gray-600 whitespace-nowrap">
                  Phase: <span className="font-semibold capitalize">{selectedProject.phase || 'N/A'}</span>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Show message when no project selected */}
        {!selectedProjectId ? (
          <Alert type="info" title="Select a Project">
            Choose a project from the dropdown above to view its analytics and maturity data.
          </Alert>
        ) : (
          <>
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
          </>
        )}

        {/* Only show tabs content if a project is selected */}
        {selectedProjectId && (
          <>
        {/* Summary Tab - Overall Analytics */}
        {activeTab === 'summary' && (
          <div className="space-y-6">
            {analyticsData ? (
              <>
                <Card className="p-6">
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-600 mb-2">Phase Maturity Scores</h3>
                      {phaseMaturity.length > 0 ? (
                        <div className="space-y-3">
                          {phaseMaturity.map((phase: any) => (
                            <div key={phase.name}>
                              <div className="flex justify-between text-sm mb-1">
                                <span className="font-medium">{phase.name}</span>
                                <span className="text-gray-600">{(phase.maturity ?? 0).toFixed(2)}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-blue-600 h-2 rounded-full"
                                  style={{ width: `${Math.min((phase.maturity ?? 0) * 10, 100)}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No phase data available</p>
                      )}
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-gray-600 mb-2">Key Metrics</h3>
                      <dl className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Questions</dt>
                          <dd className="font-semibold">{analyticsData.total_questions ?? 0}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Completion</dt>
                          <dd className="font-semibold">{(analyticsData.completion_percentage ?? 0).toFixed(1)}%</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Avg Response</dt>
                          <dd className="font-semibold">{(analyticsData.average_response_time ?? 0).toFixed(2)}s</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Current Phase</dt>
                          <dd className="font-semibold capitalize">{currentProject?.phase || 'N/A'}</dd>
                        </div>
                      </dl>
                    </div>
                  </div>
                </Card>
              </>
            ) : (
              <Alert type="info" title="No Data Available">
                Start a chat session to generate analytics data for this project.
              </Alert>
            )}
          </div>
        )}

        {/* Breakdown Tab */}
        {activeTab === 'breakdown' && (
          <div className="space-y-6">
            {breakdownData ? (
              <Card className="p-6">
                <h3 className="font-semibold mb-4">Analytics Breakdown</h3>
                <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm max-h-96">
                  {JSON.stringify(breakdownData, null, 2)}
                </pre>
              </Card>
            ) : (
              <Alert type="info" title="No Breakdown Data">
                Breakdown data will appear after more interactions.
              </Alert>
            )}
          </div>
        )}

        {/* Status Tab */}
        {activeTab === 'status' && (
          <div className="space-y-6">
            {statusData ? (
              <Card className="p-6">
                <h3 className="font-semibold mb-4">Status Information</h3>
                <div className="space-y-4">
                  <div className="border-b pb-3">
                    <p className="text-sm font-medium text-gray-600">Project Status</p>
                    <p className="text-lg font-semibold mt-1">{statusData.status || 'Active'}</p>
                  </div>
                  {statusData.details && (
                    <div className="border-b pb-3">
                      <p className="text-sm font-medium text-gray-600">Details</p>
                      <p className="text-sm text-gray-700 mt-1">{statusData.details}</p>
                    </div>
                  )}
                </div>
              </Card>
            ) : (
              <Alert type="info" title="No Status Data">
                Status data will be updated as you progress through the project.
              </Alert>
            )}
          </div>
        )}

        {/* Details Tab - Raw Data */}
        {activeTab === 'details' && (
          <div className="space-y-6">
            {analyticsData ? (
              <Card className="p-6">
                <h3 className="font-semibold mb-4">Raw Analytics Data</h3>
                <pre className="bg-gray-100 p-4 rounded overflow-auto text-xs max-h-96">
                  {JSON.stringify({
                    analytics: analyticsData,
                    maturity: maturityData,
                    breakdown: breakdownData,
                  }, null, 2)}
                </pre>
              </Card>
            ) : (
              <Alert type="info" title="No Details Available">
                Detailed analytics will appear once data is collected.
              </Alert>
            )}
          </div>
        )}
          </>
        )}
      </div>

    </MainLayout>
  );
};
