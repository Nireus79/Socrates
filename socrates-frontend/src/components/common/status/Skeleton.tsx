/**
 * Skeleton Component - Loading placeholder
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
  const baseClass = 'bg-gray-200 dark:bg-gray-700 animate-pulse rounded';

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
              key={i}
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
        <div key={i} className={baseClass} style={style} />
      ))}
    </div>
  );
};

Skeleton.displayName = 'Skeleton';
