/**
 * DocumentationPage - Socrates API Documentation
 */

import React from 'react';
import { ExternalLink } from 'lucide-react';
import { MainLayout, PageHeader } from '../../components/layout';
import { Card } from '../../components/common';

export const DocumentationPage: React.FC = () => {
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const docLinks = [
    {
      title: 'Swagger UI',
      description: 'Interactive API documentation with try-it-out functionality',
      url: `${apiBaseUrl}/docs`,
      icon: '📋',
    },
    {
      title: 'ReDoc',
      description: 'Beautiful, responsive API documentation',
      url: `${apiBaseUrl}/redoc`,
      icon: '📖',
    },
    {
      title: 'OpenAPI Specification',
      description: 'Raw OpenAPI/Swagger JSON specification',
      url: `${apiBaseUrl}/openapi.json`,
      icon: '⚙️',
    },
  ];

  const resources = [
    {
      title: 'Getting Started',
      description: 'Learn how to use Socrates and set up your first project',
      items: [
        'Create a new project',
        'Answer guided questions',
        'Track project maturity',
      ],
    },
    {
      title: 'Features',
      description: 'Explore the main features of Socrates',
      items: [
        'Socratic dialogue with AI',
        'Code generation',
        'Project analytics',
        'Knowledge base management',
      ],
    },
    {
      title: 'API Integration',
      description: 'Integrate Socrates API into your applications',
      items: [
        'Authentication',
        'Projects endpoint',
        'Analytics endpoint',
        'Chat endpoint',
      ],
    },
  ];

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header with back button */}
        <PageHeader
          title="Documentation"
          description="API documentation and guides for Socrates"
          breadcrumbs={[
            { label: 'Dashboard', onClick: () => window.location.href = '/dashboard' },
            { label: 'Documentation' },
          ]}
        />

        {/* API Documentation Links */}
        <Card>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            API Documentation
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Access our interactive API documentation:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {docLinks.map((link) => (
              <a
                key={link.title}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-lg transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <span className="text-3xl">{link.icon}</span>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {link.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {link.description}
                    </p>
                  </div>
                  <ExternalLink className="h-5 w-5 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors flex-shrink-0 ml-2" />
                </div>
              </a>
            ))}
          </div>
        </Card>

        {/* Resources */}
        <Card>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            Resources & Guides
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {resources.map((resource) => (
              <div key={resource.title} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {resource.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {resource.description}
                </p>
                <ul className="space-y-2">
                  {resource.items.map((item) => (
                    <li
                      key={item}
                      className="text-sm text-gray-700 dark:text-gray-300 flex items-center"
                    >
                      <span className="text-blue-600 dark:text-blue-400 mr-2">→</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Card>

        {/* Environment Info */}
        <Card>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Environment
          </h2>
          <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              <span className="font-semibold">API Base URL:</span>
            </p>
            <code className="text-sm bg-gray-100 dark:bg-gray-900 p-2 rounded text-gray-900 dark:text-gray-100 block break-all">
              {apiBaseUrl}
            </code>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">
              The API documentation links will open in a new tab. Make sure you have access to the API server.
            </p>
          </div>
        </Card>
      </div>
    </MainLayout>
  );
};

DocumentationPage.displayName = 'DocumentationPage';
