/**
 * AnalyticsExportPanel - Export analytics data in multiple formats
 */

import React from 'react';
import { Download, FileText, FileJson, Table } from 'lucide-react';
import { Card, Button, Alert } from '../common';

interface ExportOption {
  format: 'pdf' | 'csv' | 'json';
  label: string;
  description: string;
  icon: React.ReactNode;
}

interface AnalyticsExportPanelProps {
  projectId: string;
  projectName?: string;
  onExport?: (format: 'pdf' | 'csv' | 'json') => Promise<void>;
}

const exportOptions: ExportOption[] = [
  {
    format: 'pdf',
    label: 'PDF Report',
    description: 'Download a formatted PDF report with charts and insights',
    icon: <FileText className="h-5 w-5" />,
  },
  {
    format: 'csv',
    label: 'CSV Data',
    description: 'Download raw data in CSV format for spreadsheet analysis',
    icon: <Table className="h-5 w-5" />,
  },
  {
    format: 'json',
    label: 'JSON Export',
    description: 'Download complete analytics data as JSON for integration',
    icon: <FileJson className="h-5 w-5" />,
  },
];

export const AnalyticsExportPanel: React.FC<AnalyticsExportPanelProps> = ({
  projectId,
  projectName = 'Project',
  onExport,
}) => {
  const [selectedFormat, setSelectedFormat] = React.useState<'pdf' | 'csv' | 'json' | null>(null);
  const [isExporting, setIsExporting] = React.useState(false);
  const [exportSuccess, setExportSuccess] = React.useState(false);

  const handleExport = async (format: 'pdf' | 'csv' | 'json') => {
    setIsExporting(true);
    setSelectedFormat(format);
    try {
      if (onExport) {
        await onExport(format);
      } else {
        // Simulate export
        await new Promise((resolve) => setTimeout(resolve, 1000));

        // Generate mock data and trigger download
        const mockData = {
          projectId,
          projectName,
          exportDate: new Date().toISOString(),
          analytics: {
            maturity: 65,
            codeQuality: 70,
            testCoverage: 62,
            documentation: 72,
          },
        };

        if (format === 'json') {
          const json = JSON.stringify(mockData, null, 2);
          const blob = new Blob([json], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${projectName}_analytics_${new Date().toISOString().split('T')[0]}.json`;
          a.click();
        } else if (format === 'csv') {
          const csv = `Project,Maturity,CodeQuality,TestCoverage,Documentation\n${projectName},65,70,62,72`;
          const blob = new Blob([csv], { type: 'text/csv' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${projectName}_analytics_${new Date().toISOString().split('T')[0]}.csv`;
          a.click();
        }
      }

      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
      setSelectedFormat(null);
    }
  };

  return (
    <Card>
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Export Analytics
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Download your project analytics in your preferred format
          </p>
        </div>

        {exportSuccess && (
          <Alert type="success" title="Export Successful">
            Your analytics have been downloaded successfully.
          </Alert>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {exportOptions.map((option) => (
            <button
              key={option.format}
              onClick={() => handleExport(option.format)}
              disabled={isExporting}
              className="p-4 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-left"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="text-blue-600 dark:text-blue-400">
                    {option.icon}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {option.label}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {option.description}
                    </p>
                  </div>
                </div>
              </div>
              <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<Download className="h-4 w-4" />}
                  isLoading={isExporting && selectedFormat === option.format}
                  disabled={isExporting}
                  className="w-full justify-center"
                >
                  {isExporting && selectedFormat === option.format ? 'Exporting...' : 'Export'}
                </Button>
              </div>
            </button>
          ))}
        </div>

        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            <strong>Tip:</strong> Use PDF for sharing reports, CSV for detailed analysis in spreadsheets, and JSON for programmatic access to your data.
          </p>
        </div>
      </div>
    </Card>
  );
};
