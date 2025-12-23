/**
 * PageHeader Component - Page title, breadcrumbs, and actions
 */

import React from 'react';
import { ChevronRight } from 'lucide-react';

export interface Breadcrumb {
  label: string;
  href?: string;
  onClick?: () => void;
}

interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumbs?: Breadcrumb[];
  actions?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  breadcrumbs,
  actions,
  className = '',
}) => {
  return (
    <div className={`space-y-4 ${className}`}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          {breadcrumbs.map((breadcrumb, index) => (
            <React.Fragment key={index}>
              {index > 0 && <ChevronRight className="h-4 w-4" />}
              {breadcrumb.href ? (
                <a
                  href={breadcrumb.href}
                  className="hover:text-gray-900 dark:hover:text-gray-300 transition-colors"
                >
                  {breadcrumb.label}
                </a>
              ) : breadcrumb.onClick ? (
                <button
                  onClick={breadcrumb.onClick}
                  className="hover:text-gray-900 dark:hover:text-gray-300 transition-colors"
                >
                  {breadcrumb.label}
                </button>
              ) : (
                <span>{breadcrumb.label}</span>
              )}
            </React.Fragment>
          ))}
        </nav>
      )}

      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            {title}
          </h1>
          {description && (
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              {description}
            </p>
          )}
        </div>

        {actions && <div className="flex-shrink-0">{actions}</div>}
      </div>
    </div>
  );
};

PageHeader.displayName = 'PageHeader';
