/**
 * Detailed Maturity Analysis - Comprehensive maturity assessment display
 *
 * Shows:
 * - Phase status with progress bar
 * - Category breakdown (strong, adequate, weak, missing)
 * - Summary statistics
 * - Milestone progress (60%, 80%, 100%)
 * - Prioritized recommendations with action items
 */

import React from 'react';
import { AlertCircle, CheckCircle, TrendingUp, Zap } from 'lucide-react';
import { Card, Alert, Badge } from '../common';
import { MaturityResult, PhaseAnalysis } from '../../api/projectAnalysis';

interface DetailedMaturityAnalysisProps {
  result: MaturityResult | null;
  isLoading: boolean;
  error: string | null;
}

const getStatusColor = (percentage: number): string => {
  if (percentage >= 80) return 'from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20';
  if (percentage >= 60) return 'from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20';
  if (percentage >= 30) return 'from-yellow-50 to-amber-50 dark:from-yellow-900/20 dark:to-amber-900/20';
  return 'from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20';
};

const getStatusBadgeColor = (percentage: number): 'success' | 'warning' | 'error' | 'info' => {
  if (percentage >= 80) return 'success';
  if (percentage >= 60) return 'info';
  if (percentage >= 30) return 'warning';
  return 'error';
};

const getStatusText = (percentage: number): string => {
  if (percentage >= 80) return 'Strong';
  if (percentage >= 60) return 'Adequate';
  if (percentage >= 30) return 'Weak';
  return 'Missing';
};

const CategoryCard: React.FC<{
  name: string;
  currentScore: number;
  targetScore: number;
  percentage: number;
  specCount: number;
  confidence: number;
}> = ({ name, currentScore, targetScore, percentage, specCount, confidence }) => {
  const badgeColor = getStatusBadgeColor(percentage);

  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-gray-900 dark:text-white">{name}</h4>
        <Badge variant={badgeColor} size="sm">
          {percentage.toFixed(1)}%
        </Badge>
      </div>

      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${
            percentage >= 80
              ? 'bg-green-500'
              : percentage >= 60
                ? 'bg-blue-500'
                : percentage >= 30
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
          }`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>

      <div className="grid grid-cols-3 gap-3 text-xs">
        <div>
          <p className="text-gray-600 dark:text-gray-400">Score</p>
          <p className="font-semibold text-gray-900 dark:text-white">
            {currentScore.toFixed(1)} / {targetScore.toFixed(1)}
          </p>
        </div>
        <div>
          <p className="text-gray-600 dark:text-gray-400">Specs</p>
          <p className="font-semibold text-gray-900 dark:text-white">{specCount}</p>
        </div>
        <div>
          <p className="text-gray-600 dark:text-gray-400">Confidence</p>
          <p className="font-semibold text-gray-900 dark:text-white">{(confidence * 100).toFixed(0)}%</p>
        </div>
      </div>
    </div>
  );
};

const CategoriesBreakdown: React.FC<{ analysis: PhaseAnalysis }> = ({ analysis }) => {
  const { categories } = analysis;

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Category Breakdown</h3>

      <div className="space-y-8">
        {/* Strong Categories */}
        {categories.strong && categories.strong.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-green-700 dark:text-green-400 mb-4 flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Strong (80%+)
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-6">
              {categories.strong.map((cat) => (
                <CategoryCard
                  key={cat.name}
                  name={cat.name}
                  currentScore={cat.current_score}
                  targetScore={cat.target_score}
                  percentage={cat.percentage}
                  specCount={cat.spec_count}
                  confidence={cat.confidence}
                />
              ))}
            </div>
          </div>
        )}

        {/* Adequate Categories */}
        {categories.adequate && categories.adequate.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-blue-700 dark:text-blue-400 mb-4 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Adequate (30-80%)
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-6">
              {categories.adequate.map((cat) => (
                <CategoryCard
                  key={cat.name}
                  name={cat.name}
                  currentScore={cat.current_score}
                  targetScore={cat.target_score}
                  percentage={cat.percentage}
                  specCount={cat.spec_count}
                  confidence={cat.confidence}
                />
              ))}
            </div>
          </div>
        )}

        {/* Weak Categories */}
        {categories.weak && categories.weak.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-yellow-700 dark:text-yellow-400 mb-4 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Weak (0-30%)
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-6">
              {categories.weak.map((cat) => (
                <CategoryCard
                  key={cat.name}
                  name={cat.name}
                  currentScore={cat.current_score}
                  targetScore={cat.target_score}
                  percentage={cat.percentage}
                  specCount={cat.spec_count}
                  confidence={cat.confidence}
                />
              ))}
            </div>
          </div>
        )}

        {/* Missing Categories */}
        {categories.missing && categories.missing.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-red-700 dark:text-red-400 mb-4 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Missing (0%)
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-6">
              {categories.missing.map((cat) => (
                <CategoryCard
                  key={cat.name}
                  name={cat.name}
                  currentScore={cat.current_score}
                  targetScore={cat.target_score}
                  percentage={cat.percentage}
                  specCount={cat.spec_count}
                  confidence={cat.confidence}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

const StatisticsSection: React.FC<{ analysis: PhaseAnalysis }> = ({ analysis }) => {
  const { statistics } = analysis;

  const strong_count = statistics.strong_categories ?? 0;
  const adequate_count = statistics.adequate_count ?? 0;
  const weak_count = statistics.weak_count ?? 0;
  const missing_count = statistics.missing_count ?? 0;

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Summary Statistics</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Total Categories</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{statistics.total_categories}</p>
        </div>
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
          <p className="text-xs text-green-600 dark:text-green-400 mb-1">Completed</p>
          <p className="text-2xl font-bold text-green-700 dark:text-green-400">{statistics.completed_categories}</p>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
          <p className="text-xs text-blue-600 dark:text-blue-400 mb-1">Strong</p>
          <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">{strong_count}</p>
        </div>
        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
          <p className="text-xs text-purple-600 dark:text-purple-400 mb-1">Avg Confidence</p>
          <p className="text-2xl font-bold text-purple-700 dark:text-purple-400">
            {(statistics.average_category_confidence * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded p-3 text-center">
          <p className="text-xs text-yellow-600 dark:text-yellow-400">Adequate</p>
          <p className="text-lg font-bold text-yellow-700 dark:text-yellow-400">{adequate_count}</p>
        </div>
        <div className="bg-orange-50 dark:bg-orange-900/20 rounded p-3 text-center">
          <p className="text-xs text-orange-600 dark:text-orange-400">Weak</p>
          <p className="text-lg font-bold text-orange-700 dark:text-orange-400">{weak_count}</p>
        </div>
        <div className="bg-red-50 dark:bg-red-900/20 rounded p-3 text-center">
          <p className="text-xs text-red-600 dark:text-red-400">Missing</p>
          <p className="text-lg font-bold text-red-700 dark:text-red-400">{missing_count}</p>
        </div>
        <div className="bg-gray-50 dark:bg-gray-800 rounded p-3 text-center">
          <p className="text-xs text-gray-600 dark:text-gray-400">Points Earned</p>
          <p className="text-lg font-bold text-gray-900 dark:text-white">
            {statistics.total_points_earned.toFixed(1)} / {statistics.total_points_possible}
          </p>
        </div>
      </div>
    </Card>
  );
};

const MilestoneCard: React.FC<{
  targetPercentage: number;
  pointsNeeded: number;
  estimatedSpecs: number;
  estimatedSessions: number;
}> = ({ targetPercentage, pointsNeeded, estimatedSpecs, estimatedSessions }) => {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Reach {targetPercentage}%</h4>
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Points Needed</span>
          <span className="font-semibold text-gray-900 dark:text-white">{pointsNeeded.toFixed(1)}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Est. Specs</span>
          <span className="font-semibold text-gray-900 dark:text-white">{estimatedSpecs}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600 dark:text-gray-400">Est. Sessions</span>
          <span className="font-semibold text-gray-900 dark:text-white">{estimatedSessions}</span>
        </div>
      </div>
    </div>
  );
};

const MilestonesSection: React.FC<{ analysis: PhaseAnalysis }> = ({ analysis }) => {
  const { milestones } = analysis;

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Progress Milestones</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MilestoneCard
          targetPercentage={60}
          pointsNeeded={milestones.reach_60_percent.points_needed}
          estimatedSpecs={milestones.reach_60_percent.estimated_specs}
          estimatedSessions={milestones.reach_60_percent.estimated_sessions}
        />
        <MilestoneCard
          targetPercentage={80}
          pointsNeeded={milestones.reach_80_percent.points_needed}
          estimatedSpecs={milestones.reach_80_percent.estimated_specs}
          estimatedSessions={milestones.reach_80_percent.estimated_sessions}
        />
        <MilestoneCard
          targetPercentage={100}
          pointsNeeded={milestones.reach_100_percent.points_needed}
          estimatedSpecs={milestones.reach_100_percent.estimated_specs}
          estimatedSessions={milestones.reach_100_percent.estimated_sessions}
        />
      </div>
    </Card>
  );
};

const RecommendationItem: React.FC<{
  priority: string;
  title: string;
  description: string;
  focusAreas?: string[];
}> = ({ priority, title, description, focusAreas }) => {
  const getPriorityColor = (p: string) => {
    switch (p) {
      case 'critical':
        return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
      case 'high':
        return 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800';
      case 'info':
        return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
      case 'success':
        return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
      default:
        return 'bg-gray-50 dark:bg-gray-800';
    }
  };

  const getPriorityBadgeColor = (p: string): 'error' | 'warning' | 'info' | 'success' => {
    switch (p) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'info':
        return 'info';
      case 'success':
        return 'success';
      default:
        return 'info';
    }
  };

  return (
    <div className={`rounded-lg border p-4 space-y-3 ${getPriorityColor(priority)}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 dark:text-white text-sm">{title}</h4>
          <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">{description}</p>
        </div>
        <Badge variant={getPriorityBadgeColor(priority)} size="sm">
          {priority.charAt(0).toUpperCase() + priority.slice(1)}
        </Badge>
      </div>

      {focusAreas && focusAreas.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs font-semibold text-gray-700 dark:text-gray-400">Focus Areas:</p>
          <div className="flex flex-wrap gap-2">
            {focusAreas.map((area, idx) => (
              <Badge key={idx} variant="secondary" size="sm">
                {area}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const RecommendationsSection: React.FC<{ analysis: PhaseAnalysis }> = ({ analysis }) => {
  const { recommendations } = analysis;

  // Group recommendations by priority
  const critical = recommendations.filter((r) => r.priority === 'critical');
  const high = recommendations.filter((r) => r.priority === 'high');
  const info = recommendations.filter((r) => r.priority === 'info');
  const success = recommendations.filter((r) => r.priority === 'success');

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
        <Zap className="h-5 w-5" />
        Recommendations
      </h3>

      <div className="space-y-4">
        {critical.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-red-700 dark:text-red-400 mb-3">Critical Actions Required</h4>
            <div className="space-y-3">
              {critical.map((rec, idx) => (
                <RecommendationItem
                  key={idx}
                  priority={rec.priority}
                  title={rec.title ?? rec.category ?? 'Action'}
                  description={rec.description}
                  focusAreas={rec.action_items || (rec as any).focus_areas}
                />
              ))}
            </div>
          </div>
        )}

        {high.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-orange-700 dark:text-orange-400 mb-3">High Priority</h4>
            <div className="space-y-3">
              {high.map((rec, idx) => (
                <RecommendationItem
                  key={idx}
                  priority={rec.priority}
                  title={rec.title ?? rec.category ?? 'Action'}
                  description={rec.description}
                  focusAreas={rec.action_items || (rec as any).focus_areas}
                />
              ))}
            </div>
          </div>
        )}

        {info.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-blue-700 dark:text-blue-400 mb-3">Informational</h4>
            <div className="space-y-3">
              {info.map((rec, idx) => (
                <RecommendationItem
                  key={idx}
                  priority={rec.priority}
                  title={rec.title ?? rec.category ?? 'Action'}
                  description={rec.description}
                  focusAreas={rec.action_items || (rec as any).focus_areas}
                />
              ))}
            </div>
          </div>
        )}

        {success.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-green-700 dark:text-green-400 mb-3">Areas of Strength</h4>
            <div className="space-y-3">
              {success.map((rec, idx) => (
                <RecommendationItem
                  key={idx}
                  priority={rec.priority}
                  title={rec.title ?? rec.category ?? 'Success'}
                  description={rec.description}
                  focusAreas={rec.action_items || (rec as any).focus_areas}
                />
              ))}
            </div>
          </div>
        )}

        {recommendations.length === 0 && (
          <p className="text-gray-600 dark:text-gray-400 text-sm">No recommendations available</p>
        )}
      </div>
    </Card>
  );
};

export const DetailedMaturityAnalysis: React.FC<DetailedMaturityAnalysisProps> = ({
  result,
  isLoading,
  error,
}) => {
  if (isLoading) {
    return (
      <Card className="p-8 text-center">
        <div className="space-y-4">
          <div className="inline-block">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
          <p className="text-gray-600 dark:text-gray-400">Analyzing maturity...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert type="error" title="Error">
        {error}
      </Alert>
    );
  }

  if (!result || !result.data || !result.data.phases) {
    return (
      <Card className="p-8 text-center">
        <p className="text-gray-600 dark:text-gray-400">No maturity analysis data available</p>
      </Card>
    );
  }

  const data = result.data;
  const currentPhase = data.current_phase || Object.keys(data.phases)[0];
  const phaseAnalysis = data.phases[currentPhase];

  if (!phaseAnalysis) {
    return (
      <Card className="p-8 text-center">
        <p className="text-gray-600 dark:text-gray-400">No analysis data for current phase</p>
      </Card>
    );
  }

  const percentage = phaseAnalysis.overall_percentage;
  const bgGradient = getStatusColor(percentage);

  return (
    <div className="space-y-6">
      {/* Phase Overview */}
      <Card className={`p-8 bg-gradient-to-r ${bgGradient} border-2`}>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white capitalize">
                {currentPhase} Phase
              </h2>
              <p className="text-gray-700 dark:text-gray-300 mt-2">
                {getStatusText(percentage)} - {percentage.toFixed(1)}% Complete
              </p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold text-gray-900 dark:text-white">{percentage.toFixed(1)}%</div>
              <Badge
                variant={getStatusBadgeColor(percentage)}
                size="sm"
                className="mt-2"
              >
                {phaseAnalysis.ready_to_advance ? 'Ready to Advance' : 'Not Ready'}
              </Badge>
            </div>
          </div>

          {/* Overall Progress Bar */}
          <div className="w-full bg-gray-300 dark:bg-gray-600 rounded-full h-4 overflow-hidden">
            <div
              className={`h-4 rounded-full transition-all duration-300 ${
                percentage >= 80
                  ? 'bg-green-500'
                  : percentage >= 60
                    ? 'bg-blue-500'
                    : percentage >= 30
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
          </div>
        </div>
      </Card>

      {/* Categories Breakdown */}
      <CategoriesBreakdown analysis={phaseAnalysis} />

      {/* Statistics */}
      <StatisticsSection analysis={phaseAnalysis} />

      {/* Milestones */}
      <MilestonesSection analysis={phaseAnalysis} />

      {/* Recommendations */}
      <RecommendationsSection analysis={phaseAnalysis} />
    </div>
  );
};

export default DetailedMaturityAnalysis;
