/**
 * DashboardPage - User dashboard with project overview and quick actions
 */

import React from 'react';
import { Plus, Play, TrendingUp, MessageSquare } from 'lucide-react';
import { useAuthStore } from '../../stores';
import { useProjectStore } from '../../stores';
import { projectsAPI } from '../../api';
import {
  MainLayout,
  PageHeader,
} from '../../components/layout';
import {
  Card,
  Button,
  Alert,
  Stat,
  Badge,
  EmptyState,
} from '../../components/common';
import { ProjectCard, CreateProjectModal } from '../../components/project';

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const { projects, isLoading, listProjects, createProject, getOrCreateOnboardingProject } = useProjectStore();
  const [showCreateModal, setShowCreateModal] = React.useState(false);
  const [isChatLoading, setIsChatLoading] = React.useState(false);
  const [stats, setStats] = React.useState({ questionsAnswered: 0, codeGenerated: 0 });
  const [statsLoading, setStatsLoading] = React.useState(false);

  React.useEffect(() => {
    listProjects();
    fetchStats();
  }, [listProjects]);

  const fetchStats = async () => {
    try {
      setStatsLoading(true);
      let totalQuestions = 0;
      let totalCode = 0;

      // Fetch stats for all projects
      for (const project of projects) {
        try {
          const projectStats = await projectsAPI.getProjectStats(project.project_id);
          totalQuestions += projectStats.questions_asked || 0;
          totalCode += projectStats.code_generated || 0;
        } catch (error) {
          // Continue if individual project fails
          console.error(`Failed to fetch stats for project ${project.project_id}:`, error);
        }
      }

      setStats({ questionsAnswered: totalQuestions, codeGenerated: totalCode });
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    } finally {
      setStatsLoading(false);
    }
  };

  const activeProjects = projects.filter((p) => !p.is_archived);
  const recentProjects = activeProjects.slice(0, 3);

  const handleCreateProject = async (formData: any) => {
    try {
      if (!user) {
        throw new Error('User not authenticated');
      }
      await createProject(formData.name, user.username, formData.description);
      setShowCreateModal(false);
    } catch (error) {
      console.error('Failed to create project:', error);
      throw error;
    }
  };

  const handleContinueProject = () => {
    if (recentProjects.length > 0) {
      window.location.href = `/projects/${recentProjects[0].project_id}`;
    }
  };

  const handleChatNow = async () => {
    try {
      setIsChatLoading(true);
      const projectId = await getOrCreateOnboardingProject();
      window.location.href = `/projects/${projectId}/chat`;
    } catch (error) {
      console.error('Failed to start chat:', error);
    } finally {
      setIsChatLoading(false);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-8">
        {/* Header */}
        <PageHeader
          title={`Welcome back, ${user?.username}!`}
          description="Here's your project overview and recent activity"
        />

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            {isLoading ? (
              <div className="h-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            ) : (
              <Stat
                label="Active Projects"
                value={activeProjects.length.toString()}
                icon={<TrendingUp className="h-6 w-6 text-blue-600 dark:text-blue-400" />}
              />
            )}
          </Card>
          <Card>
            {statsLoading ? (
              <div className="h-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            ) : (
              <Stat
                label="Questions Answered"
                value={stats.questionsAnswered.toString()}
                icon={<TrendingUp className="h-6 w-6 text-green-600 dark:text-green-400" />}
              />
            )}
          </Card>
          <Card>
            {statsLoading ? (
              <div className="h-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
            ) : (
              <Stat
                label="Code Generated"
                value={stats.codeGenerated.toString()}
                icon={<TrendingUp className="h-6 w-6 text-purple-600 dark:text-purple-400" />}
              />
            )}
          </Card>
          <Card>
            <div className="flex flex-col items-center justify-center text-center">
              <Badge variant="primary" size="md">
                {user?.subscription_tier || 'Free'}
              </Badge>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">Plan</p>
            </div>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <Button
              variant="primary"
              fullWidth
              icon={<Plus className="h-4 w-4" />}
              onClick={() => setShowCreateModal(true)}
            >
              Create Project
            </Button>
            <Button
              variant="secondary"
              fullWidth
              icon={<MessageSquare className="h-4 w-4" />}
              onClick={handleChatNow}
              isLoading={isChatLoading}
            >
              Chat Now
            </Button>
            <Button
              variant="secondary"
              fullWidth
              icon={<Play className="h-4 w-4" />}
              onClick={handleContinueProject}
              disabled={activeProjects.length === 0}
            >
              Continue Project
            </Button>
            <Button
              variant="outline"
              fullWidth
              onClick={() => window.location.href = '/analytics'}
            >
              View Analytics
            </Button>
          </div>
        </Card>

        {/* Subscription Info */}
        {user?.subscription_tier === 'free' && (
          <Alert type="info" title="Upgrade to Pro">
            <p className="mb-3">Get unlimited projects, advanced analytics, and team collaboration features.</p>
            <Button variant="primary" size="sm">
              Upgrade Now
            </Button>
          </Alert>
        )}

        {/* Recent Activity Section */}
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Activity
          </h2>
          <EmptyState
            icon={<TrendingUp className="h-12 w-12" />}
            title="No activity yet"
            description="Start by creating your first project to begin your Socratic learning journey."
          />
        </Card>

        {/* Projects Section */}
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Your Projects
            </h2>
            <Button
              variant="ghost"
              onClick={() => window.location.href = '/projects'}
            >
              View All
            </Button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-2"></div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Loading projects...</p>
              </div>
            </div>
          ) : recentProjects.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentProjects.map((project) => (
                <ProjectCard
                  key={project.project_id}
                  project={project}
                  maturity={0}
                  teamCount={1}
                  onOpen={(id) => window.location.href = `/projects/${id}`}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<Plus className="h-12 w-12" />}
              title="No projects yet"
              description="Create your first project to get started with the Socratic method."
              action={{
                label: 'Create First Project',
                onClick: () => setShowCreateModal(true),
              }}
            />
          )}
        </Card>

        {/* Create Project Modal */}
        <CreateProjectModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateProject}
          isLoading={isLoading}
        />
      </div>
    </MainLayout>
  );
};
