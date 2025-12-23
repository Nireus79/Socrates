/**
 * TrendsChart - Historical trends visualization for project maturity and progress
 */

import React from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, Button, Select } from '../common';
import { Download, TrendingUp } from 'lucide-react';

interface TrendData {
  date: string;
  maturity: number;
  codeQuality: number;
  testCoverage: number;
  documentation: number;
}

interface TrendsChartProps {
  projectId: string;
  data?: TrendData[];
  isLoading?: boolean;
}

export const TrendsChart: React.FC<TrendsChartProps> = ({
  projectId,
  data = [
    { date: 'Jan 1', maturity: 10, codeQuality: 15, testCoverage: 5, documentation: 20 },
    { date: 'Jan 8', maturity: 18, codeQuality: 22, testCoverage: 12, documentation: 28 },
    { date: 'Jan 15', maturity: 25, codeQuality: 30, testCoverage: 18, documentation: 35 },
    { date: 'Jan 22', maturity: 32, codeQuality: 38, testCoverage: 28, documentation: 42 },
    { date: 'Jan 29', maturity: 42, codeQuality: 48, testCoverage: 38, documentation: 50 },
    { date: 'Feb 5', maturity: 52, codeQuality: 58, testCoverage: 48, documentation: 60 },
    { date: 'Feb 12', maturity: 65, codeQuality: 70, testCoverage: 62, documentation: 72 },
  ],
  isLoading = false,
}) => {
  const [chartType, setChartType] = React.useState<'line' | 'bar'>('line');
  const [timePeriod, setTimePeriod] = React.useState('30d');

  if (isLoading) {
    return (
      <Card>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading trends...</p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Project Trends
            </h3>
          </div>

          <div className="flex gap-2">
            <Select
              options={[
                { value: '7d', label: 'Last 7 days' },
                { value: '30d', label: 'Last 30 days' },
                { value: '90d', label: 'Last 90 days' },
                { value: '1y', label: 'Last year' },
              ]}
              value={timePeriod}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setTimePeriod(e.target.value)}
            />

            <Button
              variant={chartType === 'line' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setChartType('line')}
            >
              Line
            </Button>
            <Button
              variant={chartType === 'bar' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setChartType('bar')}
            >
              Bar
            </Button>
          </div>
        </div>

        {/* Chart */}
        <div className="w-full h-96">
          <ResponsiveContainer width="100%" height="100%">
            {chartType === 'line' ? (
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="date" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="maturity"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6' }}
                  name="Maturity"
                />
                <Line
                  type="monotone"
                  dataKey="codeQuality"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ fill: '#10b981' }}
                  name="Code Quality"
                />
                <Line
                  type="monotone"
                  dataKey="testCoverage"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={{ fill: '#f59e0b' }}
                  name="Test Coverage"
                />
                <Line
                  type="monotone"
                  dataKey="documentation"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  dot={{ fill: '#8b5cf6' }}
                  name="Documentation"
                />
              </LineChart>
            ) : (
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="date" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff',
                  }}
                />
                <Legend />
                <Bar dataKey="maturity" fill="#3b82f6" name="Maturity" />
                <Bar dataKey="codeQuality" fill="#10b981" name="Code Quality" />
                <Bar dataKey="testCoverage" fill="#f59e0b" name="Test Coverage" />
                <Bar dataKey="documentation" fill="#8b5cf6" name="Documentation" />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <p className="text-xs text-blue-600 dark:text-blue-400 font-medium">Maturity Change</p>
            <p className="text-2xl font-bold text-blue-900 dark:text-blue-100 mt-1">+55%</p>
          </div>
          <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
            <p className="text-xs text-green-600 dark:text-green-400 font-medium">Code Quality</p>
            <p className="text-2xl font-bold text-green-900 dark:text-green-100 mt-1">+55%</p>
          </div>
          <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
            <p className="text-xs text-amber-600 dark:text-amber-400 font-medium">Test Coverage</p>
            <p className="text-2xl font-bold text-amber-900 dark:text-amber-100 mt-1">+57%</p>
          </div>
          <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
            <p className="text-xs text-purple-600 dark:text-purple-400 font-medium">Documentation</p>
            <p className="text-2xl font-bold text-purple-900 dark:text-purple-100 mt-1">+52%</p>
          </div>
        </div>
      </div>
    </Card>
  );
};
