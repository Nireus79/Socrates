/**
 * Skeleton Component - Loading placeholder with shimmer animation
 *
 * Features:
 * - Multiple skeleton variants for different content types
 * - Shimmer animation for visual feedback
 * - Customizable dimensions
 * - Dark mode support
 */

import React from 'react';

interface SkeletonProps {
  type?: 'text' | 'avatar' | 'card' | 'line' | 'circle';
  count?: number;
  width?: string | number;
  height?: string | number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  type = 'text',
  count = 1,
  width = '100%',
  height = '16px',
}) => {
  const baseClass = 'bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 animate-pulse rounded';

  const getStyle = (): React.CSSProperties => {
    const w = typeof width === 'number' ? `${width}px` : width;
    const h = typeof height === 'number' ? `${height}px` : height;

    switch (type) {
      case 'avatar':
        return { width: '40px', height: '40px', borderRadius: '50%' };
      case 'circle':
        return { width: '24px', height: '24px', borderRadius: '50%' };
      case 'card':
        return { width: '100%', height: '200px' };
      case 'line':
        return { width: w, height: h };
      case 'text':
      default:
        return { width: w, height: h };
    }
  };

  const style = getStyle();

  if (type === 'card') {
    return (
      <div className={`${baseClass} p-4 space-y-4`}>
        <div className={baseClass} style={{ height: '20px' }} />
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div
              key={`skeleton-line-${i}`}
              className={baseClass}
              style={{ height: '12px', width: i === 3 ? '80%' : '100%' }}
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={`skeleton-${type}-${i}`} className={baseClass} style={style} />
      ))}
    </div>
  );
};

Skeleton.displayName = 'Skeleton';

// Specialized skeleton variants
export const SkeletonText: React.FC<{ lines?: number }> = ({ lines = 1 }) => (
  <div className="space-y-2">
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton key={i} type="text" height={i === lines - 1 ? '14px' : '16px'} width={i === lines - 1 ? '60%' : '100%'} />
    ))}
  </div>
);

SkeletonText.displayName = 'SkeletonText';

export const SkeletonCard: React.FC<{ lines?: number }> = ({ lines = 3 }) => (
  <div className="bg-white dark:bg-gray-800 rounded-lg p-4 space-y-4">
    <div className="flex gap-4">
      <Skeleton type="circle" width="48" height="48" />
      <div className="flex-1 space-y-2">
        <Skeleton type="text" height="16px" width="60%" />
        <Skeleton type="text" height="14px" width="40%" />
      </div>
    </div>
    {Array.from({ length: lines - 1 }).map((_, i) => (
      <Skeleton key={i} type="text" height="16px" />
    ))}
  </div>
);

SkeletonCard.displayName = 'SkeletonCard';

export const SkeletonList: React.FC<{ count?: number; height?: string | number }> = ({ count = 3, height = '60px' }) => (
  <div className="space-y-3">
    {Array.from({ length: count }).map((_, i) => (
      <Skeleton key={i} type="card" height={height} />
    ))}
  </div>
);

SkeletonList.displayName = 'SkeletonList';

export const SkeletonTableRow: React.FC<{ columns?: number }> = ({ columns = 4 }) => (
  <div className="flex gap-4 p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
    {Array.from({ length: columns }).map((_, i) => (
      <Skeleton key={i} type="text" width={`${100 / columns}%`} height="20px" />
    ))}
  </div>
);

SkeletonTableRow.displayName = 'SkeletonTableRow';
