/**
 * LLM Usage Chart - Display usage statistics and costs
 *
 * Shows:
 * - Total requests and tokens
 * - Usage by provider
 * - Estimated costs
 */

import React from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import type { UsageStats } from '../../api/llm';
import { Card } from '../common';
import { Badge } from '../common';

interface LLMUsageChartProps {
  stats: UsageStats;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

export const LLMUsageChart: React.FC<LLMUsageChartProps> = ({ stats }) => {
  // Prepare data for provider pie chart
  const providerData = Object.entries(stats.by_provider).map(([name, data]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: data.requests,
  }));

  // Prepare summary cards data
  const summaryCards = [
    {
      label: 'Total Requests',
      value: stats.total_requests.toLocaleString(),
      color: 'blue',
    },
    {
      label: 'Total Tokens',
      value: `${(stats.total_tokens.input + stats.total_tokens.output).toLocaleString()}`,
      color: 'green',
    },
    {
      label: 'Input Tokens',
      value: stats.total_tokens.input.toLocaleString(),
      color: 'indigo',
    },
    {
      label: 'Output Tokens',
      value: stats.total_tokens.output.toLocaleString(),
      color: 'purple',
    },
  ];

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryCards.map((card) => (
          <Card key={card.label}>
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {card.label}
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {card.value}
              </p>
            </div>
          </Card>
        ))}
      </div>

      {/* Cost Summary */}
      <Card>
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Cost Summary
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                Estimated Cost
              </p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">
                ${stats.cost_summary.estimated.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                Period
              </p>
              <Badge variant="secondary">
                {stats.cost_summary.period}
              </Badge>
            </div>
          </div>
        </div>
      </Card>

      {/* Usage by Provider */}
      {providerData.length > 0 && (
        <Card>
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Usage by Provider
            </h3>

            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={providerData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {providerData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>

            {/* Provider Details */}
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(stats.by_provider).map(([provider, data]) => (
                <Card key={provider} className="bg-gray-50 dark:bg-gray-800">
                  <div className="space-y-2">
                    <h4 className="font-semibold text-gray-900 dark:text-white capitalize">
                      {provider}
                    </h4>
                    <div className="text-sm space-y-1 text-gray-600 dark:text-gray-400">
                      <p>Requests: <span className="font-medium">{data.requests}</span></p>
                      <p>Tokens: <span className="font-medium">{data.tokens.toLocaleString()}</span></p>
                      <p>Cost: <span className="font-medium">${data.cost.toFixed(2)}</span></p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Info Box */}
      <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <div className="text-sm text-blue-800 dark:text-blue-200">
          <p className="font-medium mb-2">Usage Statistics</p>
          <p>
            These statistics are updated in real-time as you use different LLM providers
            for code generation and other features. Costs are estimated based on current
            provider pricing.
          </p>
        </div>
      </Card>
    </div>
  );
};
